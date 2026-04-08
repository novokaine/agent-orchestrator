import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Set
from datetime import datetime
from bson import ObjectId

from agents.orchestrator import AgentOrchestrator
from models.schema import ProjectCreate, ArchitectureSchema
from database.mongo import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent Factory", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)
        logger.info(f"WebSocket connected for project {project_id}")
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if len(self.active_connections[project_id]) == 0:
                del self.active_connections[project_id]
    
    async def send_message(self, project_id: str, message: dict):
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()
orchestrator = AgentOrchestrator()

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    await db.connect()
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await db.disconnect()
    logger.info("Application shutdown complete")

@app.get("/")
async def root():
    return {"message": "AI Agent Factory API", "status": "running"}

@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    """Create a new project with requirements"""
    project_id = await db.create_project(project.dict())
    
    # Start agent orchestration in background
    asyncio.create_task(orchestrator.process_project(project_id, project.requirements))
    
    return {"project_id": project_id, "status": "processing"}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.get("/api/projects/{project_id}/schema")
async def get_schema(project_id: str):
    """Get current architecture schema"""
    schema = await db.get_schema(project_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema

@app.post("/api/projects/{project_id}/schema")
async def update_schema(project_id: str, schema: ArchitectureSchema):
    """Update architecture schema (user approval)"""
    await db.update_schema(project_id, schema.dict())
    
    # Notify orchestrator that schema is approved
    await orchestrator.approve_schema(project_id, schema.dict())
    
    return {"status": "approved", "project_id": project_id}

@app.post("/api/projects/{project_id}/approve")
async def approve_schema(project_id: str, schema: dict):
    """Approve schema and start building"""
    await db.update_project(project_id, {
        "schema_approved": True,
        "approved_schema": schema,
        "status": "building"
    })
    
    await orchestrator.approve_schema(project_id, schema)
    
    return {"status": "building", "project_id": project_id}

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, project_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "approve_schema":
                await orchestrator.approve_schema(project_id, message.get("schema"))
            elif message.get("type") == "edit_schema":
                await db.update_schema(project_id, message.get("schema"))
                await manager.send_message(project_id, {
                    "type": "schema_updated",
                    "data": message.get("schema")
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
        logger.info(f"WebSocket disconnected for project {project_id}")

# Custom JSON encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)