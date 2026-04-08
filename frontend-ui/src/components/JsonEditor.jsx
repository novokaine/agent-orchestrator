import React, { useState, useEffect } from 'react';

const JsonEditor = ({ value, onChange, readOnly = false }) => {
  const [jsonString, setJsonString] = useState('');
  const [error, setError] = useState(null);
  
  useEffect(() => {
    setJsonString(JSON.stringify(value, null, 2));
  }, [value]);
  
  const handleChange = (e) => {
    const newValue = e.target.value;
    setJsonString(newValue);
    
    try {
      const parsed = JSON.parse(newValue);
      setError(null);
      onChange(parsed);
    } catch (err) {
      setError(err.message);
    }
  };
  
  return (
    <div className="json-editor">
      {error && <div className="json-error">{error}</div>}
      <textarea
        value={jsonString}
        onChange={handleChange}
        readOnly={readOnly}
        className="json-textarea"
        spellCheck={false}
        style={{
          width: '100%',
          height: '500px',
          fontFamily: 'monospace',
          fontSize: '12px',
          background: '#1e1e1e',
          color: '#d4d4d4',
          border: error ? '1px solid #f92672' : '1px solid #3c3c3c',
          padding: '10px',
          borderRadius: '4px'
        }}
      />
    </div>
  );
};

export default JsonEditor;