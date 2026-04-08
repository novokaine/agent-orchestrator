import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  themeVariables: {
    'background': '#1e1e1e',
    'primaryColor': '#4a9eff',
    'primaryBorderColor': '#4a9eff',
    'primaryTextColor': '#ffffff',
    'lineColor': '#4a9eff',
    'secondaryColor': '#0066cc',
    'tertiaryColor': '#2d2d2d',
    'fontSize': '14px',
    'fontFamily': 'monospace'
  },
  flowchart: {
    useMaxWidth: true,
    htmlLabels: true,
    curve: 'basis',
  },
  securityLevel: 'loose',
});

const Mermaid = ({ chart, onRendered }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (chart && containerRef.current) {
      // Clear previous content
      containerRef.current.innerHTML = '';
      
      // Generate unique ID for this chart
      const chartId = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
      
      try {
        // Render the chart
        mermaid.render(chartId, chart).then((result) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = result.svg;
            
            // Optional: Add zoom/pan controls
            const svg = containerRef.current.querySelector('svg');
            if (svg) {
              svg.style.maxWidth = '100%';
              svg.style.height = 'auto';
              svg.style.background = '#1e1e1e';
              svg.style.borderRadius = '8px';
              svg.style.padding = '20px';
            }
            
            if (onRendered) onRendered();
          }
        }).catch((error) => {
          console.error('Mermaid rendering error:', error);
          if (containerRef.current) {
            containerRef.current.innerHTML = `
              <div style="color: #f92672; padding: 20px; text-align: center;">
                <strong>Error rendering diagram:</strong><br/>
                ${error.message}
              </div>
            `;
          }
        });
      } catch (error) {
        console.error('Mermaid error:', error);
        if (containerRef.current) {
          containerRef.current.innerHTML = `
            <div style="color: #f92672; padding: 20px; text-align: center;">
              <strong>Invalid diagram syntax:</strong><br/>
              Please check the architecture schema
            </div>
          `;
        }
      }
    }
  }, [chart, onRendered]);

  if (!chart) {
    return (
      <div style={{ 
        padding: '20px', 
        textAlign: 'center', 
        color: '#888',
        background: '#1e1e1e',
        borderRadius: '8px'
      }}>
        No diagram available
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="mermaid-container"
      style={{
        background: '#1e1e1e',
        borderRadius: '8px',
        overflow: 'auto',
        minHeight: '400px',
      }}
    />
  );
};

export default Mermaid;