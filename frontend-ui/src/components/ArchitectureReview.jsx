import React, { useState } from 'react';
import ReactJson from '@microlink/react-json-view';
import Mermaid from './Mermaid';

const ArchitectureReview = ({ schema, onApprove, onEdit }) => {
  const [editedSchema, setEditedSchema] = useState(schema);
  
  const handleEdit = (edit) => {
    setEditedSchema(edit.updated_src);
    if (onEdit) onEdit(edit.updated_src);
  };
  
  const handleApprove = () => {
    if (onApprove) onApprove(editedSchema);
  };
  
  return (
    <div style={{ display: 'flex', gap: '20px', padding: '20px', height: '100vh' }}>
      {/* Left panel - Diagram */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ 
          background: '#1e1e1e', 
          borderRadius: '8px', 
          padding: '20px',
          border: '1px solid #3c3c3c'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#fff' }}>System Architecture</h3>
          <Mermaid chart={editedSchema.mermaid || schema.mermaid} />
        </div>
        
        <div style={{ 
          background: '#1e1e1e', 
          borderRadius: '8px', 
          padding: '20px',
          border: '1px solid #3c3c3c'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#fff' }}>API Endpoints</h3>
          <pre style={{ color: '#d4d4d4', fontSize: '12px', margin: 0 }}>
            {JSON.stringify(editedSchema.api_endpoints, null, 2)}
          </pre>
        </div>
      </div>
      
      {/* Right panel - JSON Editor */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ 
          background: '#1e1e1e', 
          borderRadius: '8px', 
          padding: '20px',
          border: '1px solid #3c3c3c',
          flex: 1,
          overflow: 'auto'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#fff' }}>Schema Editor</h3>
          <ReactJson
            src={editedSchema}
            onEdit={handleEdit}
            onAdd={handleEdit}
            onDelete={handleEdit}
            theme="monokai"
            iconStyle="square"
            indentWidth={2}
            collapseStringsAfterLength={50}
            displayDataTypes={false}
            enableClipboard={true}
            style={{ background: '#1e1e1e' }}
          />
        </div>
        
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button
            onClick={handleApprove}
            style={{
              background: '#4caf50',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            ✅ Approve & Build
          </button>
        </div>
      </div>
    </div>
  );
};

export default ArchitectureReview;