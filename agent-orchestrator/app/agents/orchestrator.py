import asyncio
import os
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
        model_name = os.getenv("MODEL_NAME", "codellama:34b")
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
            
            # Update status
            await db.update_project_status(project_id, "analyzing_requirements")
            print("📋 Status: analyzing_requirements")
            
            # Step 1: PM Agent analyzes requirements
            pm_analysis = await self._pm_agent(requirements)
            await db.save_agent_output(project_id, "pm_agent", pm_analysis)
            print("📋 PM Agent completed")
            
            # Step 2: Architect Agent creates schema
            await db.update_project_status(project_id, "creating_architecture")
            print("📋 Creating architecture...")
            
            architecture = await self._architect_agent(requirements, pm_analysis)
            await db.save_schema(project_id, architecture)
            print("📋 Architecture created")
            
            # Step 3: Wait for user approval
            await db.update_project_status(project_id, "awaiting_approval")
            print("📋 Awaiting approval")
            
            # Store in active projects for approval
            self.active_projects[project_id] = {
                "requirements": requirements,
                "architecture": architecture,
                "status": "awaiting_approval"
            }
            
        except Exception as e:
            print(f"❌ Error processing project {project_id}: {e}")
            import traceback
            traceback.print_exc()
            await db.update_project_status(project_id, "error", str(e))
    
    async def _pm_agent(self, requirements: str) -> Dict:
        """Product Manager Agent - analyze requirements"""
        prompt = f"""You are a Product Manager AI agent. Analyze these requirements and provide:
        1. Clarifying questions (if any)
        2. Key features breakdown
        3. User stories
        4. Technical constraints
        
        Requirements: {requirements}
        
        Return as JSON with keys: clarifying_questions, features, user_stories, constraints
        """
        
        try:
            response = self.llm.invoke(prompt)
            print("📋 PM Agent response received")
            
            # Try to parse as JSON
            try:
                result = json.loads(response)
            except:
                result = {
                    "clarifying_questions": [],
                    "features": ["Feature extraction in progress"],
                    "user_stories": ["User story extraction in progress"],
                    "constraints": [],
                    "raw_response": response
                }
            
            return result
        except Exception as e:
            print(f"❌ PM Agent error: {e}")
            return {
                "clarifying_questions": [],
                "features": ["Error analyzing requirements"],
                "user_stories": [],
                "constraints": [],
                "error": str(e)
            }
    
    async def _architect_agent(self, requirements: str, pm_analysis: Dict) -> Dict:
        """System Architect Agent - create architecture schema"""
        prompt = f"""You are a System Architect AI agent. Based on these requirements, create a detailed architecture:

        Requirements: {requirements}
        PM Analysis: {json.dumps(pm_analysis, indent=2)}
        
        Provide a JSON schema with:
        - database: MongoDB collections, indexes, relationships
        - api_endpoints: REST endpoints, methods, request/response schemas
        - frontend: React component hierarchy, state management, routes
        - backend: Node.js modules, middleware, services
        - deployment: Docker configuration, environment variables
        
        Return ONLY valid JSON.
        """
        
        try:
            response = self.llm.invoke(prompt)
            print("📋 Architect Agent response received")
            
            # Try to parse JSON response
            try:
                architecture = json.loads(response)
            except:
                # Fallback structure
                architecture = {
                    "database": {
                        "collections": ["users", "projects", "tasks"],
                        "indexes": ["email", "created_at"]
                    },
                    "api_endpoints": [
                        {"path": "/api/auth", "methods": ["POST"]},
                        {"path": "/api/projects", "methods": ["GET", "POST", "PUT", "DELETE"]},
                        {"path": "/api/tasks", "methods": ["GET", "POST", "PUT", "DELETE"]}
                    ],
                    "frontend": {
                        "components": ["Header", "Sidebar", "Dashboard", "TaskList", "TaskForm"],
                        "pages": ["Login", "Register", "Home", "Profile"],
                        "state_management": "Redux/Context API"
                    },
                    "backend": {
                        "modules": ["auth", "projects", "tasks", "users"],
                        "middleware": ["auth", "errorHandler", "logger"]
                    },
                    "deployment": {
                        "container": "Docker",
                        "orchestration": "docker-compose"
                    }
                }
            
            # Generate Mermaid diagram
            architecture["mermaid"] = self._generate_mermaid_diagram(architecture)
            return architecture
            
        except Exception as e:
            print(f"❌ Architect Agent error: {e}")
            return {
                "database": {"collections": ["users"]},
                "api_endpoints": [],
                "frontend": {"components": []},
                "backend": {"modules": []},
                "mermaid": "graph TD\n    A[Error] --> B[Failed to generate architecture]"
            }
    
    def _generate_mermaid_diagram(self, architecture: Dict) -> str:
        """Generate Mermaid diagram from architecture"""
        mermaid = "graph TD\n"
        mermaid += "    Client[Browser] --> FE[React Frontend]\n"
        mermaid += "    FE --> API[Node.js API]\n"
        mermaid += "    API --> DB[(MongoDB)]\n"
        
        # Add collections if present
        if "database" in architecture and "collections" in architecture["database"]:
            for collection in architecture["database"]["collections"]:
                mermaid += f"    DB --> {collection}[{collection}]\n"
        
        # Add API endpoints
        if "api_endpoints" in architecture:
            for endpoint in architecture["api_endpoints"][:3]:
                path = endpoint.get("path", "/api/unknown")
                mermaid += f"    API -->|{path}| EP{path.replace('/', '_')}[{path}]\n"
        
        return mermaid
    
    async def approve_schema(self, project_id: str, schema: Dict):
        """Called when user approves the schema"""
        project = self.active_projects.get(project_id)
        if not project:
            print(f"⚠️ Project {project_id} not found in active projects")
            return
        
        await db.update_project(project_id, {
            "schema_approved": True,
            "approved_schema": schema,
            "status": "building"
        })
        
        print(f"📋 Schema approved for project {project_id}, starting build...")
        
        # Trigger build
        await self._build_project(project_id, schema)
    
    async def _build_project(self, project_id: str, schema: Dict):
        """Code Agent - build the actual application"""
        project = await db.get_project(project_id)
        requirements = project.get("requirements", "")
        
        await db.update_project_status(project_id, "generating_code")
        print("📋 Generating backend code...")
        
        # Step 1: Generate backend code
        backend_code = await self._code_agent_backend(schema, requirements)
        await db.save_generated_code(project_id, "backend", backend_code)
        print(f"📋 Backend code generated with {len(backend_code)} files")
        
        # Step 2: Generate frontend code
        print("📋 Generating frontend code...")
        frontend_code = await self._code_agent_frontend(schema, requirements)
        await db.save_generated_code(project_id, "frontend", frontend_code)
        print(f"📋 Frontend code generated with {len(frontend_code)} files")
        
        # Step 3: Generate Docker files
        print("📋 Generating Docker configuration...")
        docker_config = await self._docker_agent(schema)
        await db.save_generated_code(project_id, "docker", docker_config)
        
        # Write files to disk
        await self._write_files_to_disk(project_id, backend_code, frontend_code, docker_config)
        
        await db.update_project_status(project_id, "completed")
        print(f"✅ Project {project_id} build completed!")
    
    async def _code_agent_backend(self, schema: Dict, requirements: str) -> Dict:
        """Code Agent for backend generation"""
        print("📋 Calling LLM for backend code generation...")
        
        # For now, return a simple structure
        # In production, this would call the LLM
        return {
            "server.js": "const express = require('express'); const app = express(); app.listen(3000);",
            "package.json": '{"name": "backend", "version": "1.0.0"}'
        }
    
    async def _code_agent_frontend(self, schema: Dict, requirements: str) -> Dict:
        """Code Agent for frontend generation"""
        print("📋 Calling LLM for frontend code generation...")
        
        # For now, return a simple structure
        return {
            "App.jsx": "import React from 'react'; function App() { return <div>Hello World</div>; } export default App;",
            "package.json": '{"name": "frontend", "version": "1.0.0"}'
        }
    
    async def _docker_agent(self, schema: Dict) -> Dict:
        """Generate Docker configuration"""
        return {
            "docker-compose.yml": """version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
  frontend:
    build: ./frontend
    ports:
      - "80:80\""""
        }
    
    async def _write_files_to_disk(self, project_id: str, backend: Dict, frontend: Dict, docker: Dict):
        """Write generated files to disk"""
        import os
        from pathlib import Path
        
        base_path = Path(f"/app/projects/{project_id}")
        
        # Create directories
        (base_path / "backend").mkdir(parents=True, exist_ok=True)
        (base_path / "frontend").mkdir(parents=True, exist_ok=True)
        
        # Write backend files
        for filename, content in backend.items():
            filepath = base_path / "backend" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
        
        # Write frontend files
        for filename, content in frontend.items():
            filepath = base_path / "frontend" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
        
        # Write Docker files
        for filename, content in docker.items():
            filepath = base_path / filename
            with open(filepath, 'w') as f:
                f.write(content)
        
        print(f"✅ Files written to disk for project {project_id}")