#!/bin/bash
set -e

echo "Waiting for MongoDB..."
until python -c "import pymongo; pymongo.MongoClient('mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASS}@mongodb:27017').admin.command('ismaster')" 2>/dev/null; do
    sleep 2
done
echo "MongoDB is ready"

echo "Waiting for Ollama..."
until curl -s http://ollama:11434/api/tags > /dev/null; do
    sleep 2
done
echo "Ollama is ready"

# Check if model exists, if not pull it (this takes time)
if ! curl -s http://ollama:11434/api/tags | grep -q "${MODEL_NAME}"; then
    echo "Pulling model ${MODEL_NAME} (this may take 10-30 minutes)..."
    ollama pull ${MODEL_NAME}
    echo "Model pulled successfully"
fi

echo "Starting agent orchestrator..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload