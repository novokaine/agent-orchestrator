from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class ProjectCreate(BaseModel):
    requirements: str
    user_id: Optional[str] = "default"

class ArchitectureSchema(BaseModel):
    database: Dict[str, Any]
    api_endpoints: List[Dict[str, Any]]
    frontend: Dict[str, Any]
    backend: Dict[str, Any]
    mermaid: Optional[str] = ""