import React, { useState, useEffect } from 'react';
import websocketService from '../websocket';

function App() {
  const [projectId, setProjectId] = useState(null);
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState('Initializing...');

  useEffect(() => {
    createProject();
  }, []);

  const createProject = async () => {
    try {
      setStatus('Creating project...');
      const response = await fetch('http://localhost:8000/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirements: "Build a task management app with user authentication"
        })
      });
      const data = await response.json();
      setProjectId(data.project_id);
      
      // Connect WebSocket
      websocketService.connect(data.project_id);
      
      // Listen for updates
      websocketService.on('agent:update', (update) => {
        console.log('Agent update:', update);
        setStatus(`Agent: ${update.type || 'working'}...`);
      });
      
      websocketService.on('project:joined', () => {
        setConnected(true);
        setStatus('Connected, waiting for agent analysis...');
      });
      
      setConnected(true);
    } catch (error) {
      
      console.error('Error creating project:', error);
      setStatus('Error: ' + error.message);
    }
  };

  return (
    <div style={{ padding: '20px', color: '#fff', background: '#0a0a0a', minHeight: '100vh' }}>
      <h1>🤖 AI Agent Factory</h1>
      <div style={{ marginTop: '20px' }}>
        <div>📡 Status: {connected ? '✅ Connected' : '⏳ Connecting...'}</div>
        <div>🆔 Project ID: {projectId || 'Creating...'}</div>
        <div>⚙️ Current: {status}</div>
      </div>
    </div>
  );
}

export default App;