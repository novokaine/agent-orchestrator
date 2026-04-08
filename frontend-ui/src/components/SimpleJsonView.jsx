import React, { useState } from 'react';

const SimpleJsonView = ({ data, name = 'root', depth = 0 }) => {
  const [collapsed, setCollapsed] = useState(depth > 2);
  
  if (data === null) return <span className="json-null">null</span>;
  if (typeof data === 'string') return <span className="json-string">"{data}"</span>;
  if (typeof data === 'number') return <span className="json-number">{data}</span>;
  if (typeof data === 'boolean') return <span className="json-boolean">{data.toString()}</span>;
  
  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="json-array">[]</span>;
    
    return (
      <div className="json-array">
        <span className="json-toggle" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? '▶' : '▼'} {name}: [{data.length}]
        </span>
        {!collapsed && (
          <div className="json-children">
            {data.map((item, i) => (
              <div key={i} className="json-item">
                <SimpleJsonView data={item} name={i.toString()} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
  
  if (typeof data === 'object') {
    const keys = Object.keys(data);
    if (keys.length === 0) return <span className="json-object">{'{}'}</span>;
    
    return (
      <div className="json-object">
        <span className="json-toggle" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? '▶' : '▼'} {name}: {'{'}
        </span>
        {!collapsed && (
          <div className="json-children">
            {keys.map(key => (
              <div key={key} className="json-item">
                <span className="json-key">{key}</span>: 
                <SimpleJsonView data={data[key]} name={key} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
        {!collapsed && <span>{'}'}</span>}
      </div>
    );
  }
  
  return <span>{String(data)}</span>;
};

export default SimpleJsonView;