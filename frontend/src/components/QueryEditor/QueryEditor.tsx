/**
 * SQL Query Editor Component
 * 
 * Advanced SQL editor with syntax highlighting, auto-completion,
 * and query execution capabilities.
 * 
 * Last updated: 2025-05-20 12:33:36
 * Updated by: Teeksss
 */

import React, { useState, useRef, useEffect } from 'react';
import { Box, Button, IconButton, Tooltip, Typography, Paper, CircularProgress, Menu, MenuItem } from '@mui/material';
import { Editor, Monaco } from '@monaco-editor/react';
import { editor as monacoEditor } from 'monaco-editor';
import { useMutation } from 'react-query';
import { toast } from 'react-toastify';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SaveIcon from '@mui/icons-material/Save';
import HistoryIcon from '@mui/icons-material/History';
import FormatColorTextIcon from '@mui/icons-material/FormatColorText';
import CleaningServicesIcon from '@mui/icons-material/CleaningServices';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SettingsIcon from '@mui/icons-material/Settings';

import { queryApi } from '../../services/queryService';
import ParameterDialog from './ParameterDialog';
import ServerSelector from './ServerSelector';
import ConnectionStatus from './ConnectionStatus';
import QueryHistory from './QueryHistory';
import SaveQueryDialog from './SaveQueryDialog';
import { formatSql } from '../../utils/sqlFormatter';
import { parseParameters } from '../../utils/queryUtils';
import { useTheme } from '../../contexts/ThemeContext';
import { QueryResult } from '../../types/api';
import QuerySettingsDialog from './QuerySettingsDialog';

export interface QuerySettings {
  maxRows: number;
  timeout: number;
  includeMetadata: boolean;
  streamResults: boolean;
  allowWriteOperations: boolean;
}

interface QueryEditorProps {
  initialQuery?: string;
  initialServerId?: string;
  savedQueryId?: string;
  onResultsChange?: (results: QueryResult | null) => void;
  onQueryChange?: (query: string) => void;
  onServerChange?: (serverId: string) => void;
  onSave?: (queryId: string) => void;
  height?: string | number;
  readOnly?: boolean;
}

const QueryEditor: React.FC<QueryEditorProps> = ({
  initialQuery = '',
  initialServerId,
  savedQueryId,
  onResultsChange,
  onQueryChange,
  onServerChange,
  onSave,
  height = '300px',
  readOnly = false
}) => {
  const [query, setQuery] = useState<string>(initialQuery);
  const [selectedServerId, setSelectedServerId] = useState<string>(initialServerId || '');
  const [showParameterDialog, setShowParameterDialog] = useState<boolean>(false);
  const [showSaveDialog, setShowSaveDialog] = useState<boolean>(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState<boolean>(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState<boolean>(false);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [editorInstance, setEditorInstance] = useState<monacoEditor.IStandaloneCodeEditor | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [querySettings, setQuerySettings] = useState<QuerySettings>({
    maxRows: 1000,
    timeout: 30,
    includeMetadata: true,
    streamResults: false,
    allowWriteOperations: false
  });
  
  const { isDarkMode } = useTheme();
  const editorRef = useRef<monacoEditor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);

  // Execute query mutation
  const executeQueryMutation = useMutation(
    () => queryApi.executeQuery(
      query, 
      parameters, 
      selectedServerId, 
      undefined, 
      {
        maxRows: querySettings.maxRows,
        timeoutSeconds: querySettings.timeout,
        includeMetadata: querySettings.includeMetadata,
        streamResults: querySettings.streamResults
      }
    ),
    {
      onSuccess: (data) => {
        toast.success('Query executed successfully');
        if (onResultsChange) {
          onResultsChange(data);
        }
      },
      onError: (error: any) => {
        console.error('Query execution error:', error);
        toast.error(error.response?.data?.detail || 'Failed to execute query');
        if (onResultsChange) {
          onResultsChange(null);
        }
      }
    }
  );

  // Format query mutation
  const formatQueryMutation = useMutation(
    (queryToFormat: string) => Promise.resolve(formatSql(queryToFormat)),
    {
      onSuccess: (formattedQuery) => {
        setQuery(formattedQuery);
        if (editorRef.current) {
          editorRef.current.setValue(formattedQuery);
        }
        toast.success('Query formatted');
        if (onQueryChange) {
          onQueryChange(formattedQuery);
        }
      },
      onError: (error) => {
        console.error('Query formatting error:', error);
        toast.error('Failed to format query');
      }
    }
  );

  // Handle editor mount
  const handleEditorDidMount = (editor: monacoEditor.IStandaloneCodeEditor, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    setEditorInstance(editor);
    
    // Setup SQL language features
    setupSqlLanguage(monaco);
    
    // Focus editor
    editor.focus();
  };

  // Setup SQL language features
  const setupSqlLanguage = (monaco: Monaco) => {
    // Register SQL language if not already registered
    if (!monaco.languages.getLanguages().some(lang => lang.id === 'sql')) {
      monaco.languages.register({ id: 'sql' });
    }
    
    // SQL keywords for autocompletion
    const sqlKeywords = [
      'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
      'TABLE', 'INDEX', 'VIEW', 'FUNCTION', 'PROCEDURE', 'TRIGGER', 'DATABASE', 'SCHEMA',
      'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'FULL', 'ON', 'GROUP BY', 'ORDER BY',
      'HAVING', 'LIMIT', 'OFFSET', 'AS', 'UNION', 'ALL', 'DISTINCT', 'AND', 'OR', 'NOT',
      'IN', 'BETWEEN', 'LIKE', 'IS NULL', 'IS NOT NULL', 'ASC', 'DESC', 'COUNT', 'SUM',
      'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'WITH', 'VALUES'
    ];
    
    // Register provider for SQL completions
    monaco.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };
        
        const suggestions = sqlKeywords.map(keyword => ({
          label: keyword,
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: keyword,
          range
        }));
        
        return { suggestions };
      }
    });
    
    // Register SQL syntax highlighting
    monaco.editor.defineTheme('sqlTheme', {
      base: isDarkMode ? 'vs-dark' : 'vs',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: isDarkMode ? '569cd6' : '0000FF', fontStyle: 'bold' },
        { token: 'operator', foreground: '000000' },
        { token: 'string', foreground: 'ce9178' },
        { token: 'number', foreground: '098658' },
        { token: 'comment', foreground: '008000', fontStyle: 'italic' }
      ],
      colors: {}
    });
    
    monaco.editor.setTheme('sqlTheme');
  };

  // Update theme when dark mode changes
  useEffect(() => {
    if (monacoRef.current) {
      setupSqlLanguage(monacoRef.current);
    }
  }, [isDarkMode]);

  // Initialize query from props
  useEffect(() => {
    setQuery(initialQuery);
    if (editorRef.current && initialQuery !== editorRef.current.getValue()) {
      editorRef.current.setValue(initialQuery);
    }
  }, [initialQuery]);

  // Update selected server from props
  useEffect(() => {
    if (initialServerId) {
      setSelectedServerId(initialServerId);
    }
  }, [initialServerId]);

  // Handle query execution
  const handleExecuteQuery = () => {
    // Parse parameters from query
    const extractedParams = parseParameters(query);
    
    if (extractedParams.length > 0) {
      // If parameters exist and don't match current parameters, show dialog
      const missingParams = extractedParams.filter(param => !parameters[param]);
      if (missingParams.length > 0) {
        setShowParameterDialog(true);
        return;
      }
    }
    
    // Execute query directly if no parameters needed
    executeQueryMutation.mutate();
  };

  // Handle parameter submission
  const handleParameterSubmit = (paramValues: Record<string, any>) => {
    setParameters(paramValues);
    setShowParameterDialog(false);
    executeQueryMutation.mutate();
  };

  // Handle format query
  const handleFormatQuery = () => {
    formatQueryMutation.mutate(query);
  };

  // Handle clear query
  const handleClearQuery = () => {
    setQuery('');
    if (editorRef.current) {
      editorRef.current.setValue('');
    }
    if (onQueryChange) {
      onQueryChange('');
    }
  };

  // Handle copy query
  const handleCopyQuery = () => {
    navigator.clipboard.writeText(query).then(
      () => {
        toast.success('Query copied to clipboard');
      },
      () => {
        toast.error('Failed to copy query');
      }
    );
    handleMenuClose();
  };

  // Handle download query
  const handleDownloadQuery = () => {
    const element = document.createElement('a');
    const file = new Blob([query], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `query_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.sql`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    handleMenuClose();
  };

  // Handle server change
  const handleServerChange = (serverId: string) => {
    setSelectedServerId(serverId);
    if (onServerChange) {
      onServerChange(serverId);
    }
  };

  // Handle query change
  const handleQueryChange = (value: string | undefined) => {
    const newValue = value || '';
    setQuery(newValue);
    if (onQueryChange) {
      onQueryChange(newValue);
    }
  };

  // Handle menu open
  const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  // Handle menu close
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Handle save query
  const handleSaveQuery = () => {
    setShowSaveDialog(true);
    handleMenuClose();
  };

  // Handle history open
  const handleHistoryOpen = () => {
    setShowHistoryDialog(true);
    handleMenuClose();
  };

  // Handle settings open
  const handleSettingsOpen = () => {
    setShowSettingsDialog(true);
    handleMenuClose();
  };

  // Handle query selection from history
  const handleSelectFromHistory = (historicalQuery: string) => {
    setQuery(historicalQuery);
    if (editorRef.current) {
      editorRef.current.setValue(historicalQuery);
    }
    if (onQueryChange) {
      onQueryChange(historicalQuery);
    }
    setShowHistoryDialog(false);
  };

  // Handle save query submission
  const handleSaveQuerySubmit = (name: string, description: string, isPublic: boolean, tags: string[]) => {
    queryApi.saveQuery(name, query, selectedServerId, description, isPublic, tags)
      .then((savedQuery) => {
        toast.success('Query saved successfully');
        if (onSave) {
          onSave(savedQuery.id);
        }
        setShowSaveDialog(false);
      })
      .catch((error) => {
        console.error('Save query error:', error);
        toast.error('Failed to save query');
      });
  };

  // Handle query settings update
  const handleSettingsUpdate = (newSettings: QuerySettings) => {
    setQuerySettings(newSettings);
    setShowSettingsDialog(false);
    toast.success('Query settings updated');
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Paper elevation={1} sx={{ p: 1, mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <ServerSelector
            selectedServerId={selectedServerId}
            onChange={handleServerChange}
            sx={{ mr: 2, minWidth: 200 }}
            disabled={readOnly}
          />
          <ConnectionStatus serverId={selectedServerId} />
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title="Query Settings">
            <IconButton
              onClick={handleSettingsOpen}
              disabled={readOnly}
              size="small"
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Show Query History">
            <IconButton
              onClick={handleHistoryOpen}
              size="small"
              sx={{ mr: 1 }}
            >
              <HistoryIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="More Options">
            <IconButton
              onClick={handleMenuOpen}
              size="small"
              aria-controls="query-menu"
              aria-haspopup="true"
            >
              <MoreVertIcon />
            </IconButton>
          </Tooltip>
          <Menu
            id="query-menu"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={handleCopyQuery} disabled={!query}>
              <ContentCopyIcon fontSize="small" sx={{ mr: 1 }} />
              Copy Query
            </MenuItem>
            <MenuItem onClick={handleDownloadQuery} disabled={!query}>
              <FileDownloadIcon fontSize="small" sx={{ mr: 1 }} />
              Download SQL
            </MenuItem>
            <MenuItem onClick={handleSaveQuery} disabled={!query || readOnly}>
              <SaveIcon fontSize="small" sx={{ mr: 1 }} />
              Save Query
            </MenuItem>
            <MenuItem onClick={handleHistoryOpen}>
              <HistoryIcon fontSize="small" sx={{ mr: 1 }} />
              Query History
            </MenuItem>
            <MenuItem onClick={handleSettingsOpen} disabled={readOnly}>
              <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
              Query Settings
            </MenuItem>
          </Menu>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={executeQueryMutation.isLoading ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
            onClick={handleExecuteQuery}
            disabled={!query || !selectedServerId || executeQueryMutation.isLoading || readOnly}
            sx={{ mr: 1 }}
          >
            Execute
          </Button>
          <Tooltip title="Format SQL">
            <IconButton
              onClick={handleFormatQuery}
              disabled={!query || formatQueryMutation.isLoading || readOnly}
              color="primary"
              size="small"
            >
              <FormatColorTextIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear Editor">
            <IconButton
              onClick={handleClearQuery}
              disabled={!query || readOnly}
              color="primary"
              size="small"
            >
              <CleaningServicesIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Save Query">
            <IconButton
              onClick={handleSaveQuery}
              disabled={!query || readOnly}
              color="primary"
              size="small"
            >
              <SaveIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>
      
      <Box sx={{ flexGrow: 1, minHeight: 0 }}>
        <Editor
          height={height}
          language="sql"
          value={query}
          onChange={handleQueryChange}
          onMount={handleEditorDidMount}
          options={{
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            wrappingIndent: 'indent',
            lineNumbers: 'on',
            glyphMargin: false,
            folding: true,
            lineDecorationsWidth: 10,
            readOnly
          }}
        />
      </Box>
      
      {/* Parameter Dialog */}
      {showParameterDialog && (
        <ParameterDialog
          open={showParameterDialog}
          parameters={parseParameters(query)}
          initialValues={parameters}
          onClose={() => setShowParameterDialog(false)}
          onSubmit={handleParameterSubmit}
        />
      )}
      
      {/* Save Query Dialog */}
      {showSaveDialog && (
        <SaveQueryDialog
          open={showSaveDialog}
          initialName=""
          initialDescription=""
          onClose={() => setShowSaveDialog(false)}
          onSubmit={handleSaveQuerySubmit}
          queryPreview={query}
        />
      )}
      
      {/* Query History Dialog */}
      {showHistoryDialog && (
        <QueryHistory
          open={showHistoryDialog}
          onClose={() => setShowHistoryDialog(false)}
          onSelect={handleSelectFromHistory}
        />
      )}
      
      {/* Query Settings Dialog */}
      {showSettingsDialog && (
        <QuerySettingsDialog
          open={showSettingsDialog}
          settings={querySettings}
          onClose={() => setShowSettingsDialog(false)}
          onSubmit={handleSettingsUpdate}
        />
      )}
    </Box>
  );
};

export default QueryEditor;

// Son güncelleme: 2025-05-20 12:33:36
// Güncelleyen: Teeksss