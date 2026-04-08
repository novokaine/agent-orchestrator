#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting AI Agent Factory on Dell T630${NC}"

# Check for NVIDIA GPUs
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}NVIDIA GPU detected - enabling GPU acceleration${NC}"
    export COMPOSE_GPU=true
else
    echo -e "${YELLOW}No NVIDIA GPU detected - using CPU (will be slower)${NC}"
fi

# Create required directories
mkdir -p projects mongodb/init ollama/models nginx/ssl

# Set permissions
chmod 755 projects

# Copy MongoDB init script
cat > mongodb/init.js << 'EOF'
// Initialize MongoDB collections and indexes
db = db.getSiblingDB('agent_factory');

// Projects collection
db.createCollection('projects');
db.projects.createIndex({ "createdAt": -1 });
db.projects.createIndex({ "status": 1 });
db.projects.createIndex({ "userId": 1 });

// Agent sessions
db.createCollection('agent_sessions');
db.agent_sessions.createIndex({ "projectId": 1 }, { unique: true });
db.agent_sessions.createIndex({ "updatedAt": 1 }, { expireAfterSeconds: 86400 });

// Architecture schemas
db.createCollection('architecture_schemas');
db.architecture_schemas.createIndex({ "projectId": 1 });
db.architecture_schemas.createIndex({ "version": -1 });

// Code generation logs
db.createCollection('code_generation_logs');
db.code_generation_logs.createIndex({ "projectId": 1 });
db.code_generation_logs.createIndex({ "timestamp": -1 });

print("MongoDB initialization complete");
EOF

# Pull images and build
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose build

# Start services
echo -e "${GREEN}Starting services...${NC}"
docker-compose up -d

# Wait for Ollama to be ready
echo -e "${YELLOW}Waiting for Ollama to start (this may take a minute)...${NC}"
until curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 2
done

echo -e "${GREEN}All services started!${NC}"
echo -e "Access the UI at: ${GREEN}http://localhost:3000${NC}"
echo -e "API docs at: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "MongoDB at: ${GREEN}localhost:27017${NC}"

# Show logs
docker-compose logs -f