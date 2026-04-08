# Project structure:
agent-factory/
├── docker-compose.yml
├── .env
├── mongodb/
│   └── init.js
├── agent-orchestrator/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── entrypoint.sh
│   └── app/
│       ├── main.py
│       ├── agents/
│       │   └── orchestrator.py
│       ├── database/
│       │   └── mongo.py
│       └── models/
│           └── schema.py
├── frontend-ui/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf
│   ├── entrypoint.sh
│   ├── websocket-server.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components/
│       │   ├── ArchitectureReview.jsx
│       │   └── Mermaid.jsx
│       └── services/
│           └── websocket.js
├── projects/               (generated code will appear here)
└── start.sh               (optional launcher script)

# Start production setup
docker-compose up -d

# Start development with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev up -d

# View logs
docker-compose logs -f agent-orchestrator

# Scale agents for parallel processing
docker-compose up -d --scale agent-orchestrator=3

# Stop all services
docker-compose down

# Stop and remove volumes (reset everything)
docker-compose down -v

# Execute commands inside container
docker exec -it agent-orchestrator bash

# Pull different LLM model
docker exec -it agent-ollama ollama pull codellama:34b



AI Agent Factory - Docker & Ollama Commands Reference
Initial Setup Commands
1. Start All Containers
bash

docker-compose up -d

2. Check Container Status
bash

docker-compose ps

Expected output:
text

NAME                 STATUS
agent-ollama         Up
agent-mongodb        Up (healthy)
agent-redis          Up (healthy)
agent-orchestrator   Up
agent-ui             Up
agent-sandbox        Up

3. View All Logs
bash

docker-compose logs -f

Ollama Commands
Pull a Model (First Time)
bash

# Pull CodeLlama 34B (19GB - ~20-30 min)
docker exec agent-ollama ollama pull codellama:34b

# Pull smaller model for testing (4.7GB - ~5-10 min)
docker exec agent-ollama ollama pull llama3.1:8b

# Pull CodeLlama 7B (3.8GB - ~5 min)
docker exec agent-ollama ollama pull codellama:7b

List Downloaded Models
bash

docker exec agent-ollama ollama list

Check Model Download Progress
bash

docker-compose logs -f ollama

Test Model Directly
bash

docker exec agent-ollama ollama run codellama:34b "Say hello"

Delete a Model (free up space)
bash

docker exec agent-ollama ollama rm codellama:34b

Check Ollama Version
bash

docker exec agent-ollama ollama --version

Container Management Commands
Start Specific Services
bash

# Start everything
docker-compose up -d

# Start only backend and database
docker-compose up -d mongodb redis agent-orchestrator

# Start only frontend
docker-compose up -d frontend-ui

Stop Services
bash

# Stop everything
docker-compose down

# Stop specific service
docker-compose stop agent-orchestrator

Restart Services
bash

# Restart all
docker-compose restart

# Restart specific service
docker-compose restart agent-orchestrator

Rebuild After Code Changes
bash

# Rebuild specific service
docker-compose build --no-cache agent-orchestrator

# Rebuild and start
docker-compose up -d --build agent-orchestrator

Remove Everything (Fresh Start)
bash

# Stop and remove containers, networks, volumes
docker-compose down -v

# Also prune unused Docker resources
docker system prune -a

Log Monitoring Commands
View All Logs
bash

docker-compose logs -f

View Specific Service Logs
bash

# Backend logs
docker-compose logs -f agent-orchestrator

# Ollama logs (watch model download)
docker-compose logs -f ollama

# Frontend logs
docker-compose logs -f frontend-ui

# MongoDB logs
docker-compose logs -f mongodb

# Redis logs
docker-compose logs -f redis

View Last N Lines
bash

docker-compose logs --tail=50 agent-orchestrator

Debugging Commands
Execute Commands Inside Containers
bash

# Enter backend container shell
docker exec -it agent-orchestrator bash

# Enter MongoDB shell (with auth)
docker exec -it agent-mongodb mongosh -u admin -p admin123

# Enter Redis CLI (with password)
docker exec -it agent-redis redis-cli -a RedisSecurePass456!

# Test backend connectivity from frontend container
docker exec agent-ui wget -q -O- http://agent-orchestrator:8000/

Check Container Resource Usage
bash

# See all containers stats
docker stats

# Specific container
docker stats agent-orchestrator

Inspect Container Details
bash

# See environment variables
docker exec agent-orchestrator printenv

# See container IP and network details
docker inspect agent-orchestrator | grep IPAddress

Volume Management
List Volumes
bash

docker volume ls | grep agent

Remove Specific Volume
bash

docker volume rm agent-factory_ollama_data
docker volume rm agent-factory_mongodb_data

Backup Volume Data
bash

docker run --rm -v agent-factory_ollama_data:/source -v %cd%:/backup alpine cp -r /source /backup/ollama_backup

Testing API Endpoints
Test Backend Health
bash

curl http://localhost:8000/

Create a Project
bash

curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d "{\"requirements\": \"Build a todo app\"}"

Get Project Status
bash

curl http://localhost:8000/api/projects/YOUR_PROJECT_ID

Get Project Schema
bash

curl http://localhost:8000/api/projects/YOUR_PROJECT_ID/schema

View API Documentation

Open browser: http://localhost:8000/docs
Database Commands
MongoDB
bash

# Enter MongoDB shell
docker exec -it agent-mongodb mongosh -u admin -p admin123

# Inside MongoDB shell:
show dbs
use agent_factory
show collections
db.projects.find().pretty()
db.architecture_schemas.find().pretty()

Redis
bash

# Enter Redis CLI
docker exec -it agent-redis redis-cli -a RedisSecurePass456!

# Inside Redis:
KEYS *
GET "project:xxx"
MONITOR

Ollama Model Management Flow
bash

# 1. Pull the model (first time only)
docker exec agent-ollama ollama pull codellama:34b

# 2. Verify it's downloaded
docker exec agent-ollama ollama list

# 3. Test it works
docker exec agent-ollama ollama run codellama:34b "Hello"

# 4. Update .env file with model name
# LLM_MODEL=codellama:34b

# 5. Restart backend to use new model
docker-compose restart agent-orchestrator

# 6. Watch it load into memory
docker-compose logs -f agent-orchestrator

Quick Troubleshooting Flow
bash

# 1. Check all containers are running
docker-compose ps

# 2. If container is missing, start it
docker-compose up -d missing_container_name

# 3. Check logs for errors
docker-compose logs --tail=30 agent-orchestrator

# 4. If model not found, check Ollama
docker exec agent-ollama ollama list
docker exec agent-ollama ollama pull your_model_name

# 5. If MongoDB auth fails, reset volumes
docker-compose down -v
docker-compose up -d

# 6. Full reset (nuclear option)
docker-compose down -v
docker system prune -a
docker-compose up -d
docker exec agent-ollama ollama pull codellama:34b

Performance Monitoring
bash

# Check GPU usage (if NVIDIA)
docker exec agent-ollama nvidia-smi

# Check memory usage
docker stats --no-stream

# Check disk space
docker system df