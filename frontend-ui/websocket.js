// const { io } = require('socket.io-client');
import io from 'socket.io-client'

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect(projectId) {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';
    
    this.socket = io(wsUrl, {
      path: '/socket.io/',
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.joinProject(projectId);
    });

    this.socket.on('agent:update', (data) => {
      this.notifyListeners('agent:update', data);
    });

    this.socket.on('agent:log', (data) => {
      this.notifyListeners('agent:log', data);
    });

    this.socket.on('schema:approved', (data) => {
      this.notifyListeners('schema:approved', data);
    });

    this.socket.on('project:joined', (data) => {
      console.log('Project joined:', data);
      this.notifyListeners('project:joined', data);
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });
  }

  joinProject(projectId) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('project:join', projectId);
    }
  }

  approveSchema(projectId, schema) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('schema:approve', { projectId, approvedSchema: schema });
    }
  }

  editSchema(projectId, changes) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('schema:edit', { projectId, schemaChanges: changes });
    }
  }

  requestStatus(projectId) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('project:status', projectId);
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  notifyListeners(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected() {
    return this.socket && this.socket.connected;
  }
}

export default new WebSocketService();