import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

// This component assumes you're using a CDN for CodeMirror
// In a real project, you might want to use a CodeMirror React wrapper

const CodeEditor = ({
  value,
  onChange,
  language = 'sql',
  placeholder = '',
  height = '200px',
  readOnly = false
}) => {
  const editorRef = useRef(null);
  const cmInstanceRef = useRef(null);
  
  useEffect(() => {
    // Check if CodeMirror is available globally
    if (!window.CodeMirror) {
      console.error('CodeMirror is not available. Make sure it is loaded via CDN or NPM package.');
      return;
    }
    
    // Initialize CodeMirror
    if (editorRef.current && !cmInstanceRef.current) {
      cmInstanceRef.current = window.CodeMirror.fromTextArea(editorRef.current, {
        mode: language === 'sql' ? 'text/x-sql' : language,
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        autofocus: false,
        matchBrackets: true,
        autoCloseBrackets: true,
        readOnly: readOnly,
        placeholder: placeholder,
        extraKeys: {
          'Ctrl-Space': 'autocomplete',
          'Tab': function(cm) {
            const spaces = Array(cm.getOption('indentUnit') + 1).join(' ');
            cm.replaceSelection(spaces);
          }
        }
      });
      
      // Set height
      cmInstanceRef.current.setSize(null, height);
      
      // Add change handler
      cmInstanceRef.current.on('change', (instance) => {
        if (onChange) {
          onChange(instance.getValue());
        }
      });
    }
    
    // Update editor value when prop changes
    if (cmInstanceRef.current && value !== cmInstanceRef.current.getValue()) {
      cmInstanceRef.current.setValue(value || '');
    }
    
    // Cleanup when component unmounts
    return () => {
      if (cmInstanceRef.current) {
        cmInstanceRef.current.toTextArea();
        cmInstanceRef.current = null;
      }
    };
  }, [language, placeholder, readOnly, height]);
  
  // Update value when prop changes
  useEffect(() => {
    if (cmInstanceRef.current && value !== cmInstanceRef.current.getValue()) {
      cmInstanceRef.current.setValue(value || '');
    }
  }, [value]);
  
  return (
    <div className="border rounded-md overflow-hidden">
      <textarea
        ref={editorRef}
        defaultValue={value}
        placeholder={placeholder}
        style={{ display: 'none' }}
      />
    </div>
  );
};

CodeEditor.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func,
  language: PropTypes.string,
  placeholder: PropTypes.string,
  height: PropTypes.string,
  readOnly: PropTypes.bool
};

export default CodeEditor;