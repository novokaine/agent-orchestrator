// Switch to admin database for authentication
db = db.getSiblingDB('admin');

// Create root user if not exists
db.createUser({
  user: "agent_admin",
  pwd: "ChangeMe123StrongPassword",
  roles: [
    { role: "root", db: "admin" }
  ]
});

// Switch to agent_factory database
db = db.getSiblingDB('agent_factory');

// Create collections
db.createCollection('projects');
db.createCollection('architecture_schemas');
db.createCollection('agent_logs');
db.createCollection('generated_code');

// Create indexes
db.projects.createIndex({ "createdAt": -1 });
db.projects.createIndex({ "status": 1 });
db.architecture_schemas.createIndex({ "projectId": 1 });
db.architecture_schemas.createIndex({ "version": -1 });
db.agent_logs.createIndex({ "projectId": 1, "timestamp": -1 });

print("MongoDB initialization complete");