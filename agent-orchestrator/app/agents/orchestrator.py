import os
import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
from langchain_community.llms import Ollama
import sys
sys.path.append('/app')
from database.mongo import db

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        model_name = os.getenv("MODEL_NAME", "codellama:7b")
        self.llm = Ollama(
            base_url="http://ollama:11434",
            model=model_name,
            temperature=0.7
        )
        self.active_projects: Dict[str, Dict] = {}
        
    async def process_project(self, project_id: str, requirements: str):
        """Main orchestration flow for a project"""
        try:
            print(f"📋 Processing project {project_id}")
            print(f"📋 Requirements: {requirements[:200]}...")
            
            await db.update_project_status(project_id, "analyzing_requirements")
            
            # Step 1: PM Agent
            print("📋 PM Agent: Analyzing...")
            pm_analysis = await self._pm_agent(requirements)
            await db.save_agent_output(project_id, "pm_agent", pm_analysis)
            
            # Step 2: Architect Agent
            await db.update_project_status(project_id, "creating_architecture")
            print("📋 Architect Agent: Creating schema...")
            architecture = await self._architect_agent(requirements, pm_analysis)
            await db.save_schema(project_id, architecture)
            
            # Step 3: Wait for approval
            await db.update_project_status(project_id, "awaiting_approval")
            self.active_projects[project_id] = {
                "requirements": requirements,
                "architecture": architecture,
                "pm_analysis": pm_analysis,
                "status": "awaiting_approval"
            }
            print("📋 Waiting for user approval...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.update_project_status(project_id, "error", str(e))
    
    async def _pm_agent(self, requirements: str) -> Dict:
        """Product Manager Agent - analyze requirements"""
        prompt = f"""Analyze these requirements and return a JSON object.

Requirements: {requirements}

Return JSON with these keys:
- "project_name": string
- "features": list of strings
- "entities": list of strings (data entities like User, Product, etc.)
- "has_auth": boolean
- "api_endpoints": list of strings
- "pages": list of strings (frontend pages needed)

Return ONLY valid JSON. No other text.
"""
        response = self.llm.invoke(prompt)
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            response = response[start:end]
        return json.loads(response)
    
    async def _architect_agent(self, requirements: str, pm_analysis: Dict) -> Dict:
        """System Architect Agent - create architecture schema"""
        prompt = f"""Based on these requirements and analysis, create a technical architecture.

Requirements: {requirements}
Analysis: {json.dumps(pm_analysis, indent=2)}

Return JSON with these keys:
- "database": {{"collections": list of strings}}
- "api_endpoints": list of {{"path": string, "method": string, "description": string}}
- "frontend": {{"pages": list of strings, "components": list of strings}}
- "backend": {{"models": list of strings, "routes": list of strings}}

Return ONLY valid JSON. No other text.
"""
        response = self.llm.invoke(prompt)
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            response = response[start:end]
        architecture = json.loads(response)
        architecture["mermaid"] = self._generate_mermaid_diagram(architecture)
        return architecture
    
    def _generate_mermaid_diagram(self, architecture: Dict) -> str:
        """Generate Mermaid diagram from architecture"""
        mermaid = "graph TD\n"
        mermaid += "    Client[Browser] --> FE[React Frontend]\n"
        mermaid += "    FE --> API[Node.js API]\n"
        mermaid += "    API --> DB[(MongoDB)]\n"
        
        if "database" in architecture and "collections" in architecture.get("database", {}):
            for collection in architecture["database"].get("collections", [])[:3]:
                mermaid += f"    DB --> {collection}[{collection}]\n"
        
        if "api_endpoints" in architecture:
            for endpoint in architecture["api_endpoints"][:3]:
                path = endpoint.get("path", "/api")
                mermaid += f"    API -->|{path}| EP{path.replace('/', '_')}[{path}]\n"
        
        return mermaid
    
    async def approve_schema(self, project_id: str, schema: Dict):
        """User approved the schema - generate code"""
        project = self.active_projects.get(project_id)
        if not project:
            db_project = await db.get_project(project_id)
            if db_project:
                project = {
                    "requirements": db_project.get("requirements", ""),
                    "architecture": schema,
                    "pm_analysis": {}
                }
        
        if not project:
            print(f"❌ Project {project_id} not found")
            return
        
        await db.update_project(project_id, {
            "schema_approved": True,
            "approved_schema": schema,
            "status": "building"
        })
        
        await self._build_project(project_id, schema, project.get("requirements", ""))
    
    async def _build_project(self, project_id: str, schema: Dict, requirements: str):
        """Generate the actual code"""
        try:
            await db.update_project_status(project_id, "generating_code")
            
            print("📋 Generating backend code...")
            backend_code = await self._code_agent_backend(requirements, schema)
            await db.save_generated_code(project_id, "backend", backend_code)
            
            print("📋 Generating frontend code...")
            frontend_code = await self._code_agent_frontend(requirements, schema)
            await db.save_generated_code(project_id, "frontend", frontend_code)
            
            print("📋 Generating Docker files...")
            docker_config = await self._docker_agent()
            await db.save_generated_code(project_id, "docker", docker_config)
            
            await self._write_files_to_disk(project_id, backend_code, frontend_code, docker_config)
            
            await db.update_project_status(project_id, "completed")
            print(f"✅ Project {project_id} completed!")
            
        except Exception as e:
            print(f"❌ Build error: {e}")
            import traceback
            traceback.print_exc()
            await db.update_project_status(project_id, "error", str(e))
    
    async def _code_agent_backend(self, requirements: str, schema: Dict) -> Dict:
        """Code Agent for backend generation"""
        print("📋 LLM: Generating backend code...")
        
        prompt = f"""Generate a complete Node.js backend based on these requirements:

{requirements}

Return ONLY valid JSON with filenames as keys and file contents as values.
Include: package.json, server.js, models/, routes/, middleware/, .env.example
"""
        response = self.llm.invoke(prompt)
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            response = response[start:end]
        return json.loads(response)
    
    async def _code_agent_frontend(self, requirements: str, schema: Dict) -> Dict:
        """Code Agent for frontend generation"""
        print("📋 LLM: Generating frontend code...")
        
        prompt = f"""Generate a complete React frontend based on these requirements:

{requirements}

Return ONLY valid JSON with filenames as keys and file contents as values.
Include: package.json, index.html, src/main.jsx, src/App.jsx, src/components/, src/pages/, src/context/, src/services/
"""
        response = self.llm.invoke(prompt)
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            response = response[start:end]
        return json.loads(response)
    
    async def _docker_agent(self) -> Dict:
        """Generate Docker configuration"""
        return {
            "docker-compose.yml": """version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/app
    depends_on:
      - mongodb

  frontend:
    build: ./frontend
    ports:
      - "80:80"

  mongodb:
    image: mongo:7.0
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:""",
            "backend/Dockerfile": """FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]""",
            "frontend/Dockerfile": """FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]"""
        }
    
    async def _write_files_to_disk(self, project_id: str, backend: Dict, frontend: Dict, docker: Dict):
        """Write generated files to disk"""
        from pathlib import Path
        
        base_path = Path(f"/app/projects/{project_id}")
        (base_path / "backend").mkdir(parents=True, exist_ok=True)
        (base_path / "frontend").mkdir(parents=True, exist_ok=True)
        
        for filename, content in backend.items():
            filepath = base_path / "backend" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"  ✅ backend/{filename}")
        
        for filename, content in frontend.items():
            filepath = base_path / "frontend" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"  ✅ frontend/{filename}")
        
        for filename, content in docker.items():
            filepath = base_path / filename
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"  ✅ {filename}")
        
        print(f"✅ All files written to {base_path}")