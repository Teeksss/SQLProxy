/**
 * Advanced SQL Editor Component
 * 
 * Enhanced SQL editor with syntax highlighting, autocompletion, and formatting
 * 
 * Last updated: 2025-05-21 06:58:56
 * Updated by: Teeksss
 */

import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Button, IconButton, Tooltip, Paper, CircularProgress } from '@mui/material';
import FormatIndentIncreaseIcon from '@mui/icons-material/FormatIndentIncrease';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SaveIcon from '@mui/icons-material/Save';
import HistoryIcon from '@mui/icons-material/History';
import UndoIcon from '@mui/icons-material/Undo';
import RedoIcon from '@mui/icons-material/Redo';
import { toast } from 'react-toastify';
import { useMutation } from 'react-query';

// Monaco Editor
import * as monaco from 'monaco-editor';
import Editor, { Monaco, OnMount } from '@monaco-editor/react';

// SQL Formatter
import { format } from 'sql-formatter';

// Services
import { queryApi } from '../../services/queryService';
import { serverApi } from '../../services/serverService';

// Define the properties for the AdvancedSQLEditor component
interface AdvancedSQLEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute?: (sql: string) => void;
  onSave?: (sql: string) => void;
  height?: string | number;
  readOnly?: boolean;
  serverId?: string;
  suggestions?: { label: string; detail?: string; insertText: string }[];
  showToolbar?: boolean;
  isExecuting?: boolean;
  className?: string;
}

// The AdvancedSQLEditor component
const AdvancedSQLEditor: React.FC<AdvancedSQLEditorProps> = ({
  value,
  onChange,
  onExecute,
  onSave,
  height = '300px',
  readOnly = false,
  serverId,
  suggestions = [],
  showToolbar = true,
  isExecuting = false,
  className
}) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAutocompleteFetching, setIsAutocompleteFetching] = useState<boolean>(false);
  const [dbObjects, setDbObjects] = useState<any[]>([]);

  // Mutation for fetching server schema (tables, columns) for autocompletion
  const fetchSchemaMutation = useMutation(
    (serverId: string) => serverApi.getServerSchema(serverId),
    {
      onSuccess: (data) => {
        if (data) {
          setDbObjects(data);
          registerAutocompletion(data);
        }
        setIsAutocompleteFetching(false);
      },
      onError: (error) => {
        console.error('Error fetching schema:', error);
        setIsAutocompleteFetching(false);
      }
    }
  );

  // Initialize editor
  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Configure SQL language
    configureSqlLanguage(monaco);

    // Add custom commands
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
      formatSql();
    });

    // Register autocompletion
    if (serverId && !isAutocompleteFetching) {
      setIsAutocompleteFetching(true);
      fetchSchemaMutation.mutate(serverId);
    } else if (suggestions.length > 0) {
      registerCustomSuggestions(suggestions);
    }
  };

  // Configure SQL language features
  const configureSqlLanguage = (monaco: Monaco) => {
    // Define SQL token provider for enhanced syntax highlighting
    monaco.languages.setMonarchTokensProvider('sql', {
      defaultToken: '',
      tokenPostfix: '.sql',
      ignoreCase: true,

      brackets: [
        { open: '[', close: ']', token: 'delimiter.square' },
        { open: '(', close: ')', token: 'delimiter.parenthesis' }
      ],

      keywords: [
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
        'TABLE', 'VIEW', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'INDEX', 'CONSTRAINT',
        'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'UNIQUE', 'CHECK', 'DEFAULT',
        'NULL', 'NOT', 'AND', 'OR', 'IN', 'LIKE', 'BETWEEN', 'EXISTS', 'INNER', 'OUTER',
        'LEFT', 'RIGHT', 'JOIN', 'FULL', 'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC',
        'WITH', 'UNION', 'ALL', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AS', 'ON',
        'IS', 'INTO', 'VALUES', 'SET', 'TOP', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'
      ],

      operators: [
        '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
        '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^', '%'
      ],

      // Define token rules
      tokenizer: {
        root: [
          { include: '@comments' },
          { include: '@whitespace' },
          { include: '@numbers' },
          { include: '@strings' },
          { include: '@complexIdentifiers' },
          { include: '@scopes' },
          [/[;,.]/, 'delimiter'],
          [/[()]/, '@brackets'],
          [/[\[\]]/, '@brackets'],
          [/@[a-zA-Z_]\w*/, 'tag'],
          [
            /[a-zA-Z_]\w*/,
            {
              cases: {
                '@keywords': 'keyword',
                '@default': 'identifier'
              }
            }
          ],
          [
            /[<>=!%&+\-*/|~^]/,
            {
              cases: {
                '@operators': 'operator',
                '@default': ''
              }
            }
          ]
        ],

        whitespace: [
          [/\s+/, 'white']
        ],

        comments: [
          [/--+.*/, 'comment'],
          [/\/\*/, { token: 'comment.quote', next: '@comment' }]
        ],

        comment: [
          [/[^*/]+/, 'comment'],
          [/\*\//, { token: 'comment.quote', next: '@pop' }],
          [/./, 'comment']
        ],

        numbers: [
          [/0[xX][0-9a-fA-F]*/, 'number'],
          [/[$][+-]*\d*(\.\d*)?/, 'number'],
          [/((\d+(\.\d*)?)|(\.\d+))([eE][\-+]?\d+)?/, 'number']
        ],

        strings: [
          [/'/, { token: 'string', next: '@string' }],
          [/"/, { token: 'string.double', next: '@stringDouble' }]
        ],

        string: [
          [/[^']+/, 'string'],
          [/''/, 'string'],
          [/'/, { token: 'string', next: '@pop' }]
        ],

        stringDouble: [
          [/[^"]+/, 'string.double'],
          [/""/, 'string.double'],
          [/"/, { token: 'string.double', next: '@pop' }]
        ],

        complexIdentifiers: [
          [/\[/, { token: 'identifier.quote', next: '@bracketedIdentifier' }],
          [/"/, { token: 'identifier.quote', next: '@quotedIdentifier' }]
        ],

        bracketedIdentifier: [
          [/[^\]]+/, 'identifier'],
          [/]]/, 'identifier'],
          [/]/, { token: 'identifier.quote', next: '@pop' }]
        ],

        quotedIdentifier: [
          [/[^"]+/, 'identifier'],
          [/""/, 'identifier'],
          [/"/, { token: 'identifier.quote', next: '@pop' }]
        ],

        scopes: []
      }
    });
  };

  // Register autocompletion for database objects
  const registerAutocompletion = (dbSchema: any) => {
    if (!monacoRef.current) return;

    // Extract tables and columns
    const tables = dbSchema.tables || [];
    const allSuggestions: any[] = [];

    // Add table suggestions
    tables.forEach((table: any) => {
      allSuggestions.push({
        label: table.name,
        kind: monacoRef.current!.languages.CompletionItemKind.Class,
        detail: table.schema ? `${table.schema}.${table.name}` : table.name,
        insertText: table.schema ? `${table.schema}.${table.name}` : table.name,
        documentation: `Table with ${table.columns?.length || 0} columns`
      });

      // Add column suggestions for each table
      if (table.columns && table.columns.length > 0) {
        table.columns.forEach((column: any) => {
          allSuggestions.push({
            label: column.name,
            kind: monacoRef.current!.languages.CompletionItemKind.Field,
            detail: `${column.name} (${column.data_type})`,
            insertText: column.name,
            documentation: `Column of ${table.name}. Type: ${column.data_type}`
          });

          // Add table.column suggestions
          allSuggestions.push({
            label: `${table.name}.${column.name}`,
            kind: monacoRef.current!.languages.CompletionItemKind.Field,
            detail: `${table.name}.${column.name} (${column.data_type})`,
            insertText: `${table.name}.${column.name}`,
            documentation: `Column of ${table.name}. Type: ${column.data_type}`
          });
        });
      }
    });

    // Register SQL completion provider
    monacoRef.current.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };

        return {
          suggestions: allSuggestions.map(suggestion => ({
            ...suggestion,
            range
          }))
        };
      }
    });
  };

  // Register custom suggestions
  const registerCustomSuggestions = (customSuggestions: any[]) => {
    if (!monacoRef.current) return;

    monacoRef.current.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };

        return {
          suggestions: customSuggestions.map(suggestion => ({
            label: suggestion.label,
            kind: monacoRef.current!.languages.CompletionItemKind.Function,
            detail: suggestion.detail || suggestion.label,
            insertText: suggestion.insertText,
            range
          }))
        };
      }
    });
  };

  // Format SQL query
  const formatSql = () => {
    if (!editorRef.current) return;

    try {
      const currentValue = editorRef.current.getValue();
      const formattedValue = format(currentValue, {
        language: 'sql',
        indent: '  ', // Two spaces
        uppercase: true, // Uppercase keywords
        linesBetweenQueries: 2
      });
      
      // Add to history
      addToHistory(currentValue);
      
      // Set formatted value
      editorRef.current.setValue(formattedValue);
      onChange(formattedValue);
      
      toast.success('SQL formatted successfully');
    } catch (error) {
      console.error('Error formatting SQL:', error);
      toast.error('Error formatting SQL');
    }
  };

  // Add to history
  const addToHistory = (sql: string) => {
    // Don't add if same as last entry
    if (history.length > 0 && history[history.length - 1] === sql) {
      return;
    }
    
    const newHistory = [...history, sql];
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  // Handle copy to clipboard
  const handleCopy = () => {
    if (!editorRef.current) return;
    
    const currentValue = editorRef.current.getValue();
    navigator.clipboard.writeText(currentValue);
    toast.success('Copied to clipboard');
  };

  // Handle save
  const handleSave = () => {
    if (!editorRef.current || !onSave) return;
    
    const currentValue = editorRef.current.getValue();
    onSave(currentValue);
  };

  // Handle execute
  const handleExecute = () => {
    if (!editorRef.current || !onExecute) return;
    
    const currentValue = editorRef.current.getValue();
    onExecute(currentValue);
  };

  // Handle undo
  const handleUndo = () => {
    if (!editorRef.current) return;
    editorRef.current.trigger('', 'undo', null);
  };

  // Handle redo
  const handleRedo = () => {
    if (!editorRef.current) return;
    editorRef.current.trigger('', 'redo', null);
  };

  // Update editor options when readOnly changes
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({ readOnly });
    }
  }, [readOnly]);

  // Fetch schema for autocompletion when serverId changes
  useEffect(() => {
    if (serverId && monacoRef.current && !isAutocompleteFetching) {
      setIsAutocompleteFetching(true);
      fetchSchemaMutation.mutate(serverId);
    }
  }, [serverId]);

  return (
    <Box className={className} sx={{ width: '100%', height: '100%' }}>
      {showToolbar && (
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          mb: 1,
          backgroundColor: (theme) => theme.palette.background.paper,
          borderRadius: 1,
          border: (theme) => `1px solid ${theme.palette.divider}`
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title="Format SQL (Ctrl+F)">
              <IconButton size="small" onClick={formatSql} disabled={readOnly}>
                <FormatIndentIncreaseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Copy to Clipboard">
              <IconButton size="small" onClick={handleCopy}>
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Undo (Ctrl+Z)">
              <IconButton size="small" onClick={handleUndo} disabled={readOnly}>
                <UndoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Redo (Ctrl+Y)">
              <IconButton size="small" onClick={handleRedo} disabled={readOnly}>
                <RedoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            {onSave && (
              <Tooltip title="Save (Ctrl+S)">
                <IconButton size="small" onClick={handleSave} disabled={readOnly}>
                  <SaveIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
          
          <Box>
            {onExecute && (
              <Button
                variant="contained"
                color="primary"
                size="small"
                onClick={handleExecute}
                disabled={isExecuting || readOnly}
                startIcon={isExecuting ? <CircularProgress size={16} /> : undefined}
              >
                {isExecuting ? 'Executing...' : 'Execute'}
              </Button>
            )}
          </Box>
        </Box>
      )}
      
      <Box sx={{ 
        height: typeof height === 'number' ? `${height}px` : height,
        border: (theme) => `1px solid ${theme.palette.divider}`,
        borderRadius: 1,
        overflow: 'hidden'
      }}>
        <Editor
          height="100%"
          defaultLanguage="sql"
          defaultValue={value}
          value={value}
          onChange={(value) => onChange(value || '')}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 14,
            tabSize: 2,
            readOnly,
            wordWrap: 'on',
            renderLineHighlight: 'all',
            colorDecorators: true,
            formatOnPaste: true,
            automaticLayout: true,
            folding: true,
            lineNumbersMinChars: 3,
            scrollbar: {
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10
            }
          }}
        />
      </Box>
      
      {isAutocompleteFetching && (
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
          <CircularProgress size={16} sx={{ mr: 1 }} />
          <Typography variant="caption" color="text.secondary">
            Loading schema for autocompletion...
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default AdvancedSQLEditor;

// Son güncelleme: 2025-05-21 06:58:56
// Güncelleyen: Teeksss