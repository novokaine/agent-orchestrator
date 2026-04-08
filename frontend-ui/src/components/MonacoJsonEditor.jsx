import React from 'react';
import Editor from '@monaco-editor/react';

const MonacoJsonEditor = ({ value, onChange, readOnly = false }) => {
  const handleEditorChange = (value) => {
    if (onChange && value) {
      try {
        const parsed = JSON.parse(value);
        onChange(parsed);
      } catch (err) {
        // Invalid JSON - don't update parent
        console.warn('Invalid JSON:', err.message);
      }
    }
  };
  
  return (
    <Editor
      height="600px"
      defaultLanguage="json"
      defaultValue={JSON.stringify(value, null, 2)}
      onChange={handleEditorChange}
      options={{
        readOnly: readOnly,
        minimap: { enabled: false },
        fontSize: 12,
        formatOnPaste: true,
        formatOnType: true,
        automaticLayout: true,
        theme: 'vs-dark'
      }}
    />
  );
};

export default MonacoJsonEditor;