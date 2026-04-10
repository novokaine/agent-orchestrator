import React, { useState, useEffect } from 'react';

function App() {
  const [projectId, setProjectId] = useState(null);
  const [status, setStatus] = useState('Initializing...');
  const [schema, setSchema] = useState(null);
  const [isPolling, setIsPolling] = useState(false);

  // Create a new project
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
      const newProjectId = data.project_id;
      setProjectId(newProjectId);
      setStatus('Project created! Fetching schema...');
      
      // Start fetching the schema
      fetchSchema(newProjectId);
      
    } catch (error) {
      console.error('Error:', error);
      setStatus('Error: ' + error.message);
    }
  };

  // Fetch the schema for a project
  const fetchSchema = async (id) => {
    setIsPolling(true);
    let attempts = 0;
    const maxAttempts = 60; // 60 attempts * 3 seconds = 180 seconds max
    
    const pollInterval = setInterval(async () => {
      attempts++;
      setStatus(`Checking for schema... (attempt ${attempts}/${maxAttempts})`);
      
      try {
        const response = await fetch(`http://localhost:8000/api/projects/${id}/schema`);
        
        if (response.ok) {
          const schemaData = await response.json();
          
          // Check if schema has meaningful data
          if (schemaData && Object.keys(schemaData).length > 0 && schemaData.database) {
            setSchema(schemaData);
            setStatus('✅ Schema ready! Review below.');
            setIsPolling(false);
            clearInterval(pollInterval);
          }
        }
        
        if (attempts >= maxAttempts) {
          setStatus('⏰ Timeout waiting for schema. Check backend logs.');
          setIsPolling(false);
          clearInterval(pollInterval);
        }
        
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000); // Check every 3 seconds
  };

  // Approve schema and start building
  const approveSchema = async () => {
    try {
      setStatus('🚀 Approving schema and starting build...');
      const response = await fetch(`http://localhost:8000/api/projects/${projectId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schema)
      });
      
      if (response.ok) {
        setStatus('✅ Build started! Check backend logs for progress.');
      } else {
        setStatus('❌ Error approving schema');
      }
    } catch (error) {
      console.error('Approval error:', error);
      setStatus('Error: ' + error.message);
    }
  };

  // useEffect(() => {
  //   createProject();
  // }, []);

  // Display schema if available
  if (schema) {
    return (
      <div style={{ padding: '20px', color: '#fff', background: '#0a0a0a', minHeight: '100vh' }}>
        <h1>🤖 AI Agent Factory</h1>
        
        <div style={{ marginTop: '20px', background: '#1e1e1e', padding: '20px', borderRadius: '8px' }}>
          <h2>📐 Architecture Schema</h2>
          
          <div style={{ marginTop: '10px' }}>
            <strong>Database Collections:</strong>
            <pre style={{ color: '#4ec9b0', overflow: 'auto' }}>
              {JSON.stringify(schema.database, null, 2)}
            </pre>
          </div>
          
          <div style={{ marginTop: '10px' }}>
            <strong>API Endpoints:</strong>
            <pre style={{ color: '#ce9178', overflow: 'auto' }}>
              {JSON.stringify(schema.api_endpoints, null, 2)}
            </pre>
          </div>
          
          <div style={{ marginTop: '10px' }}>
            <strong>Frontend Components:</strong>
            <pre style={{ color: '#9cdcfe', overflow: 'auto' }}>
              {JSON.stringify(schema.frontend, null, 2)}
            </pre>
          </div>
          
          <div style={{ marginTop: '10px' }}>
            <strong>Backend Modules:</strong>
            <pre style={{ color: '#d7ba7d', overflow: 'auto' }}>
              {JSON.stringify(schema.backend, null, 2)}
            </pre>
          </div>
          
          {schema.mermaid && (
            <div style={{ marginTop: '10px' }}>
              <strong>Mermaid Diagram:</strong>
              <pre style={{ color: '#9cdcfe', background: '#2d2d2d', padding: '10px', borderRadius: '4px', overflow: 'auto' }}>
                {schema.mermaid}
              </pre>
            </div>
          )}
        </div>
        
        <button 
          onClick={approveSchema}
          style={{
            marginTop: '20px',
            padding: '12px 24px',
            background: '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          ✅ Approve & Build
        </button>
      </div>
    );
  }

  // Loading state
  return (
    <div style={{ padding: '20px', color: '#fff', background: '#0a0a0a', minHeight: '100vh' }}>
      <h1>🤖 AI Agent Factory</h1>
      <div style={{ marginTop: '20px' }}>
        <div>🆔 Project ID: {projectId || 'Creating...'}</div>
        <div>⚙️ Status: {status}</div>
        <button type='button' onClick={() => createProject()}>Create project</button>
        {isPolling && (
          <div style={{ marginTop: '20px' }}>
            <div>⏳ Agents are analyzing your requirements...</div>
            <div style={{ fontSize: '12px', color: '#888', marginTop: '10px' }}>
              This takes 30-60 seconds on CPU. The schema will appear here when ready.
            </div>
            <div style={{ fontSize: '12px', color: '#888', marginTop: '5px' }}>
              You can also check progress at: http://localhost:8000/docs
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;