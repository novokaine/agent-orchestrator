const { Server } = require('socket.io');
const http = require('http');
const { createClient } = require('redis');

// Configuration
const PORT = process.env.WS_PORT || 3001;
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379';
const REDIS_PASSWORD = process.env.REDIS_PASSWORD || 'RedisSecurePass456!';

// Create HTTP server
const server = http.createServer();
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  },
  path: '/socket.io/'
});

// Redis client with password
const redisClient = createClient({ 
  url: REDIS_URL,
  password: REDIS_PASSWORD
});
const redisSubscriber = createClient({ 
  url: REDIS_URL,
  password: REDIS_PASSWORD
});

// Store active connections
const activeConnections = new Map();
const socketToProject = new Map();

async function initializeRedis() {
  try {
    await redisClient.connect();
    await redisSubscriber.connect();
    
    console.log('✅ Redis connected successfully');
    
    // Subscribe to agent updates
    await redisSubscriber.subscribe('agent:updates', (message) => {
      const data = JSON.parse(message);
      const { projectId, update } = data;
      
      if (activeConnections.has(projectId)) {
        activeConnections.get(projectId).forEach(socketId => {
          io.to(socketId).emit('agent:update', update);
        });
      }
    });
    
    await redisSubscriber.subscribe('agent:log', (message) => {
      const data = JSON.parse(message);
      const { projectId, logEntry } = data;
      
      if (activeConnections.has(projectId)) {
        activeConnections.get(projectId).forEach(socketId => {
          io.to(socketId).emit('agent:log', logEntry);
        });
      }
    });
    
    console.log('Redis pub/sub initialized');
  } catch (err) {
    console.error('Failed to initialize Redis:', err.message);
    console.log('Continuing without Redis - WebSocket will work but only on single instance');
  }
}

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);
  
  // Join project room
  socket.on('project:join', (projectId) => {
    socket.join(`project:${projectId}`);
    
    if (!activeConnections.has(projectId)) {
      activeConnections.set(projectId, new Set());
    }
    activeConnections.get(projectId).add(socket.id);
    socketToProject.set(socket.id, projectId);
    
    console.log(`Socket ${socket.id} joined project ${projectId}`);
    socket.emit('project:joined', { projectId, success: true });
  });
  
  // Leave project room
  socket.on('project:leave', (projectId) => {
    socket.leave(`project:${projectId}`);
    
    if (activeConnections.has(projectId)) {
      activeConnections.get(projectId).delete(socket.id);
      if (activeConnections.get(projectId).size === 0) {
        activeConnections.delete(projectId);
      }
    }
    socketToProject.delete(socket.id);
    console.log(`Socket ${socket.id} left project ${projectId}`);
  });
  
  // User approval signal
  socket.on('schema:approve', async (data) => {
    const { projectId, approvedSchema } = data;
    console.log(`Schema approved for project ${projectId}`);
    
    try {
      await redisClient.publish('user:action', JSON.stringify({
        type: 'schema_approved',
        projectId,
        data: approvedSchema,
        timestamp: new Date().toISOString()
      }));
    } catch (err) {
      console.log('Redis publish failed (non-critical):', err.message);
    }
    
    io.to(`project:${projectId}`).emit('schema:approved', {
      projectId,
      status: 'building'
    });
  });
  
  // User schema edit
  socket.on('schema:edit', async (data) => {
    const { projectId, schemaChanges } = data;
    console.log(`Schema edit for project ${projectId}`);
    
    try {
      await redisClient.publish('user:action', JSON.stringify({
        type: 'schema_edited',
        projectId,
        data: schemaChanges,
        timestamp: new Date().toISOString()
      }));
    } catch (err) {
      console.log('Redis publish failed (non-critical):', err.message);
    }
    
    socket.emit('schema:edit-confirmed', {
      projectId,
      changesApplied: true
    });
  });
  
  // Request current status
  socket.on('project:status', async (projectId) => {
    try {
      await redisClient.publish('user:action', JSON.stringify({
        type: 'status_request',
        projectId,
        socketId: socket.id
      }));
    } catch (err) {
      console.log('Redis publish failed (non-critical):', err.message);
    }
  });
  
  // Disconnect
  socket.on('disconnect', () => {
    const projectId = socketToProject.get(socket.id);
    if (projectId && activeConnections.has(projectId)) {
      activeConnections.get(projectId).delete(socket.id);
      if (activeConnections.get(projectId).size === 0) {
        activeConnections.delete(projectId);
      }
    }
    socketToProject.delete(socket.id);
    console.log(`Client disconnected: ${socket.id}`);
  });
});

// Health check endpoint
server.on('request', (req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('OK');
  }
});

// Start server
initializeRedis().then(() => {
  server.listen(PORT, () => {
    console.log(`WebSocket server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
  });
}).catch(() => {
  // Still start the server without Redis
  server.listen(PORT, () => {
    console.log(`WebSocket server running on port ${PORT} (without Redis)`);
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing server...');
  io.close(() => {
    redisClient.quit().catch(() => {});
    redisSubscriber.quit().catch(() => {});
    process.exit(0);
  });
});