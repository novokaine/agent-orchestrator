from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class ProjectCreate(BaseModel):
    requirements: str
    user_id: Optional[str] = "default"

class ProjectResponse(BaseModel):
    id: str
    requirements: str
    status: str
    created_at: datetime
    schema_approved: bool = False

class ArchitectureSchema(BaseModel):
    database: Dict[str, Any]
    api_endpoints: List[Dict[str, Any]]
    frontend: Dict[str, Any]
    backend: Dict[str, Any]
    mermaid: Optional[str] = ""