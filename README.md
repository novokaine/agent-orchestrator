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