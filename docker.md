# Rebuild both backend and frontend
docker-compose build --no-cache agent-orchestrator
docker-compose build --no-cache frontend-ui

# Start everything
docker-compose up -d

# Watch logs
docker-compose logs -f agent-orchestrator