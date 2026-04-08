#!/bin/sh
set -e

echo "Starting WebSocket server on port 3001..."
node /app/websocket-server.js &

echo "Starting nginx on port 80..."
nginx -g "daemon off;"