import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

class MongoDB:
    client = None
    db = None
    
    async def connect(self):
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:admin123@mongodb:27017/agent_factory?authSource=admin")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client.agent_factory
        print("✅ Connected to MongoDB")
    
    async def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    async def create_project(self, project_data: dict) -> str:
        project_data["created_at"] = datetime.utcnow()
        project_data["status"] = "created"
        project_data["schema_approved"] = False
        project_data["requirements"] = project_data.get("requirements", "")
        
        result = await self.db.projects.insert_one(project_data)
        return str(result.inserted_id)
    
    async def get_project(self, project_id: str) -> dict:
        try:
            project = await self.db.projects.find_one({"_id": ObjectId(project_id)})
            if project:
                project["id"] = str(project["_id"])
                del project["_id"]
            return project
        except Exception as e:
            print(f"Error getting project: {e}")
            return None
    
    async def update_project(self, project_id: str, update_data: dict):
        update_data["updated_at"] = datetime.utcnow()
        await self.db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": update_data}
        )
    
    async def update_project_status(self, project_id: str, status: str, error: str = None):
        update = {"status": status}
        if error:
            update["error"] = error
        await self.update_project(project_id, update)
    
    async def save_schema(self, project_id: str, schema: dict):
        schema["project_id"] = ObjectId(project_id)
        schema["created_at"] = datetime.utcnow()
        schema["version"] = 1
        
        result = await self.db.architecture_schemas.insert_one(schema)
        print(f"✅ Schema saved with id: {result.inserted_id}")
        return result.inserted_id
    
    async def get_schema(self, project_id: str) -> dict:
        try:
            print(f"🔍 Searching for schema with project_id: {project_id}")
            
            # Convert project_id to ObjectId
            try:
                obj_id = ObjectId(project_id)
            except:
                print(f"❌ Invalid ObjectId: {project_id}")
                return None
            
            # Search by project_id field (not _id)
            schema = await self.db.architecture_schemas.find_one(
                {"project_id": obj_id},
                sort=[("version", -1)]
            )
            
            if schema:
                print(f"✅ Found schema with version: {schema.get('version', 'unknown')}")
                schema["id"] = str(schema["_id"])
                del schema["_id"]
                if isinstance(schema.get("project_id"), ObjectId):
                    schema["project_id"] = str(schema["project_id"])
                return schema
            else:
                print(f"❌ No schema found for project_id: {project_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting schema: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def update_schema(self, project_id: str, schema: dict):
        schema["project_id"] = ObjectId(project_id)
        schema["updated_at"] = datetime.utcnow()
        
        # Get current version
        current = await self.get_schema(project_id)
        version = (current.get("version", 0) + 1) if current else 1
        schema["version"] = version
        
        await self.db.architecture_schemas.insert_one(schema)
    
    async def save_agent_output(self, project_id: str, agent_name: str, output: dict):
        await self.db.agent_logs.insert_one({
            "project_id": ObjectId(project_id),
            "agent": agent_name,
            "output": output,
            "timestamp": datetime.utcnow()
        })
    
    async def save_generated_code(self, project_id: str, code_type: str, code: dict):
        await self.db.generated_code.insert_one({
            "project_id": ObjectId(project_id),
            "type": code_type,
            "code": code,
            "timestamp": datetime.utcnow()
        })

db = MongoDB()