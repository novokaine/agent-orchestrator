import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama
import sys
sys.path.append('/app')
from database.mongo import db

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.llm = Ollama(
            base_url="http://ollama:11434",
            model="llama3.1:70b-instruct-q4_K_M",
            temperature=0.7
        )
        self.active_projects: Dict[str, Dict] = {}
        
    async def process_project(self, project_id: str, requirements: str):
        """Main orchestration flow for a project"""
        try:
            # Update status
            await db.update_project_status(project_id, "analyzing_requirements")
            await self._send_update(project_id, "analyzing", "PM Agent analyzing requirements...")
            
            # Step 1: PM Agent analyzes requirements
            pm_analysis = await self._pm_agent(requirements)
            await db.save_agent_output(project_id, "pm_agent", pm_analysis)
            await self._send_update(project_id, "pm_complete", pm_analysis)
            
            # Step 2: Architect Agent creates schema
            await db.update_project_status(project_id, "creating_architecture")
            await self._send_update(project_id, "architecting", "Creating system architecture...")
            
            architecture = await self._architect_agent(requirements, pm_analysis)
            await db.save_schema(project_id, architecture)
            await self._send_update(project_id, "schema_ready", architecture)
            
            # Step 3: Wait for user approval
            await db.update_project_status(project_id, "awaiting_approval")
            await self._send_update(project_id, "awaiting_approval", {
                "message": "Schema ready for approval",
                "schema": architecture
            })
            
            # Store in active projects for approval
            self.active_projects[project_id] = {
                "requirements": requirements,
                "architecture": architecture,
                "status": "awaiting_approval"
            }
            
        except Exception as e:
            logger.error(f"Error processing project {project_id}: {e}")
            await db.update_project_status(project_id, "error", str(e))
            await self._send_update(project_id, "error", {"error": str(e)})
    
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
        
        response = self.llm.invoke(prompt)
        
        # Try to parse as JSON, fallback to structured dict
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
        
        response = self.llm.invoke(prompt)
        
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
                    {"path": "/api/projects", "methods": ["GET", "POST"]}
                ],
                "frontend": {
                    "components": ["Header", "Sidebar", "Dashboard"],
                    "pages": ["Login", "Home", "Profile"]
                },
                "backend": {
                    "modules": ["auth", "projects", "users"]
                }
            }
        
        # Generate Mermaid diagram
        architecture["mermaid"] = self._generate_mermaid_diagram(architecture)
        return architecture
    
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
            for endpoint in architecture["api_endpoints"][:3]:  # Limit to 3 for readability
                path = endpoint.get("path", "/api/unknown")
                mermaid += f"    API -->|{path}| EP{path.replace('/', '_')}[{path}]\n"
        
        return mermaid
    
    async def _send_update(self, project_id: str, event_type: str, data: Any):
        """Send update via WebSocket"""
        from ..main import manager
        await manager.send_message(project_id, {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def approve_schema(self, project_id: str, schema: Dict):
        """Called when user approves the schema"""
        project = self.active_projects.get(project_id)
        if not project:
            logger.warning(f"Project {project_id} not found in active projects")
            return
        
        await db.update_project(project_id, {
            "schema_approved": True,
            "approved_schema": schema,
            "status": "building"
        })
        
        await self._send_update(project_id, "build_started", {
            "message": "Schema approved, starting code generation..."
        })
        
        # Trigger build
        await self._build_project(project_id, schema)
    
    async def _build_project(self, project_id: str, schema: Dict):
        """Code Agent - build the actual application"""
        project = await db.get_project(project_id)
        requirements = project.get("requirements", "")
        
        await db.update_project_status(project_id, "generating_code")
        await self._send_update(project_id, "generating", "Generating backend code...")
        
        # Step 1: Generate backend code
        backend_code = await self._code_agent_backend(schema, requirements)
        await db.save_generated_code(project_id, "backend", backend_code)
        await self._send_update(project_id, "backend_generated", {"files": list(backend_code.keys())})
        
        # Step 2: Generate frontend code
        await self._send_update(project_id, "generating", "Generating frontend code...")
        frontend_code = await self._code_agent_frontend(schema, requirements)
        await db.save_generated_code(project_id, "frontend", frontend_code)
        await self._send_update(project_id, "frontend_generated", {"files": list(frontend_code.keys())})
        
        # Step 3: Generate Docker files
        await self._send_update(project_id, "generating", "Generating Docker configuration...")
        docker_config = await self._docker_agent(schema)
        await db.save_generated_code(project_id, "docker", docker_config)
        
        # Write files to disk
        await self._write_files_to_disk(project_id, backend_code, frontend_code, docker_config)
        
        await db.update_project_status(project_id, "completed")
        await self._send_update(project_id, "completed", {
            "message": "Project build completed!",
            "project_path": f"/app/projects/{project_id}"
        })
    
    async def _code_agent_backend(self, schema: Dict, requirements: str) -> Dict:
        """Code Agent for backend generation"""
        prompt = f"""Generate complete Node.js/Express backend code based on this schema:
        
        Schema: {json.dumps(schema, indent=2)}
        Requirements: {requirements}
        
        Generate files as JSON with filenames as keys and code as values.
        Include:
        - package.json
        - server.js
        - models/*.js (Mongoose models)
        - routes/*.js (API routes)
        - middleware/auth.js
        - config/database.js
        
        Return ONLY valid JSON.
        """
        
        response = self.llm.invoke(prompt)
        
        try:
            code_files = json.loads(response)
        except:
            # Fallback template
            code_files = {
                "package.json": '{"name": "backend", "version": "1.0.0", "dependencies": {"express": "^4.18.2", "mongoose": "^7.0.0"}}',
                "server.js": "const express = require('express'); const app = express(); app.listen(3000);",
                "README.md": "# Backend generated by AI Agent Factory"
            }
        
        return code_files
    
    async def _code_agent_frontend(self, schema: Dict, requirements: str) -> Dict:
        """Code Agent for frontend generation"""
        prompt = f"""Generate complete React frontend code based on this schema:
        
        Schema: {json.dumps(schema, indent=2)}
        Requirements: {requirements}
        
        Generate files as JSON with filenames as keys and code as values.
        Include:
        - package.json
        - src/App.jsx
        - src/main.jsx
        - src/components/*.jsx
        - src/services/api.js
        
        Return ONLY valid JSON.
        """
        
        response = self.llm.invoke(prompt)
        
        try:
            code_files = json.loads(response)
        except:
            code_files = {
                "package.json": '{"name": "frontend", "version": "1.0.0"}',
                "src/App.jsx": "import React from 'react'; function App() { return <div>Hello World</div>; } export default App;",
                "README.md": "# Frontend generated by AI Agent Factory"
            }
        
        return code_files
    
    async def _docker_agent(self, schema: Dict) -> Dict:
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
            "Dockerfile": "FROM node:18\nWORKDIR /app\nCOPY . .\nRUN npm install\nCMD npm start"
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
        
        logger.info(f"Files written to disk for project {project_id}")