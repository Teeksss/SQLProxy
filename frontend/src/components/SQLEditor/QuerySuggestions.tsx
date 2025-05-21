/**
 * Query Suggestions Component
 * 
 * Component for displaying ML-based query suggestions in the SQL editor
 * 
 * Last updated: 2025-05-21 07:25:48
 * Updated by: Teeksss
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Tooltip,
  Collapse,
  Divider,
  CircularProgress,
  Alert,
  Popper,
  Fade,
  ListItemIcon
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';
import HistoryIcon from '@mui/icons-material/History';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import FunctionsIcon from '@mui/icons-material/Functions';
import StorageIcon from '@mui/icons-material/Storage';
import CodeIcon from '@mui/icons-material/Code';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useMutation } from 'react-query';
import { toast } from 'react-toastify';

import { queryApi } from '../../services/queryService';
import useDebounce from '../../hooks/useDebounce';

interface QuerySuggestionsProps {
  sql: string;
  serverId?: string;
  onRunSuggestion?: (sql: string) => void;
  onInsertSuggestion?: (sql: string) => void;
  editorRef?: any;
  position?: 'sidebar' | 'tooltip';
  cursorPosition?: any;
  onClose?: () => void;
  width?: number | string;
}

const QuerySuggestions: React.FC<QuerySuggestionsProps> = ({
  sql,
  serverId,
  onRunSuggestion,
  onInsertSuggestion,
  editorRef,
  position = 'sidebar',
  cursorPosition,
  onClose,
  width = '100%'
}) => {
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [expanded, setExpanded] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<string[]>([]);
  const debouncedSql = useDebounce(sql, 500); // Debounce SQL input
  
  const isTooltip = position === 'tooltip';
  const tooltipRef = useRef<HTMLDivElement>(null);
  
  const suggestionMutation = useMutation(
    (params: any) => queryApi.getQuerySuggestions(params),
    {
      onSuccess: (data) => {
        setSuggestions(data || []);
        setIsLoading(false);
      },
      onError: (error: any) => {
        setError(error.message || 'Error fetching suggestions');
        setIsLoading(false);
      }
    }
  );
  
  // Load favorites from localStorage
  useEffect(() => {
    const storedFavorites = localStorage.getItem('favoriteSuggestions');
    if (storedFavorites) {
      try {
        setFavorites(JSON.parse(storedFavorites));
      } catch (e) {
        setFavorites([]);
      }
    }
  }, []);
  
  // Save favorites to localStorage
  const saveFavorites = (favorites: string[]) => {
    localStorage.setItem('favoriteSuggestions', JSON.stringify(favorites));
    setFavorites(favorites);
  };
  
  // Toggle favorite status for a suggestion
  const toggleFavorite = (suggestion: any) => {
    const suggestionKey = suggestion.sql_text;
    const newFavorites = favorites.includes(suggestionKey)
      ? favorites.filter(fav => fav !== suggestionKey)
      : [...favorites, suggestionKey];
    saveFavorites(newFavorites);
  };
  
  // Check if a suggestion is favorited
  const isFavorite = (suggestion: any) => {
    return favorites.includes(suggestion.sql_text);
  };
  
  // Get suggestions when SQL changes
  useEffect(() => {
    if (!debouncedSql || debouncedSql.length < 3) {
      setSuggestions([]);
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    suggestionMutation.mutate({
      sql: debouncedSql,
      serverId: serverId
    });
  }, [debouncedSql, serverId]);
  
  // Get suggestion type icon
  const getSuggestionTypeIcon = (type: string) => {
    switch (type) {
      case 'frequent':
        return <TrendingUpIcon fontSize="small" />;
      case 'context':
        return <HistoryIcon fontSize="small" />;
      case 'keyword':
        return <CodeIcon fontSize="small" />;
      case 'expression':
        return <FunctionsIcon fontSize="small" />;
      case 'table':
        return <StorageIcon fontSize="small" />;
      default:
        return <HistoryIcon fontSize="small" />;
    }
  };
  
  // Get suggestion type label
  const getSuggestionTypeLabel = (type: string) => {
    switch (type) {
      case 'frequent':
        return 'Frequently Used';
      case 'context':
        return 'Based on Context';
      case 'keyword':
        return 'SQL Keyword';
      case 'expression':
        return 'SQL Expression';
      case 'table':
        return 'Table';
      default:
        return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };
  
  // Handle run suggestion
  const handleRunSuggestion = (suggestion: any) => {
    if (onRunSuggestion) {
      onRunSuggestion(suggestion.sql_text);
    }
    if (isTooltip && onClose) {
      onClose();
    }
  };
  
  // Handle insert suggestion
  const handleInsertSuggestion = (suggestion: any) => {
    if (onInsertSuggestion) {
      onInsertSuggestion(suggestion.sql_text);
    } else if (editorRef?.current) {
      const editor = editorRef.current;
      editor.setValue(suggestion.sql_text);
    }
    if (isTooltip && onClose) {
      onClose();
    }
  };
  
  // Handle copy suggestion
  const handleCopySuggestion = (suggestion: any) => {
    navigator.clipboard.writeText(suggestion.sql_text);
    toast.info('Query copied to clipboard');
    if (isTooltip && onClose) {
      onClose();
    }
  };
  
  // Handle insert completion
  const handleInsertCompletion = (text: string) => {
    if (editorRef?.current && cursorPosition) {
      const editor = editorRef.current;
      const position = cursorPosition;
      
      editor.executeEdits('', [
        {
          range: {
            startLineNumber: position.lineNumber,
            startColumn: position.column,
            endLineNumber: position.lineNumber,
            endColumn: position.column
          },
          text: text + ' '
        }
      ]);
    }
    if (isTooltip && onClose) {
      onClose();
    }
  };
  
  // Determine if we should show completions or full suggestions
  const isCompletionMode = useMemo(() => {
    return isTooltip && cursorPosition && suggestions.some(s => s.type === 'completion' || s.type === 'keyword' || s.type === 'expression');
  }, [isTooltip, cursorPosition, suggestions]);
  
  // Group suggestions by type (for tooltip mode with completions)
  const groupedSuggestions = useMemo(() => {
    if (!isCompletionMode) return { completions: [], fullSuggestions: suggestions };
    
    return {
      completions: suggestions.filter(s => ['completion', 'keyword', 'expression'].includes(s.type)),
      fullSuggestions: suggestions.filter(s => !['completion', 'keyword', 'expression'].includes(s.type))
    };
  }, [suggestions, isCompletionMode]);
  
  // Render the tooltip version (code completion)
  if (isTooltip) {
    return (
      <Popper
        open={true}
        anchorEl={editorRef?.current?.getDomNode() || null}
        placement="bottom-start"
        transition
        style={{ zIndex: 1300 }}
      >
        {({ TransitionProps }) => (
          <Fade {...TransitionProps} timeout={350}>
            <Paper 
              ref={tooltipRef}
              elevation={3}
              sx={{ 
                minWidth: 200, 
                maxWidth: 500, 
                width: width,
                maxHeight: 300,
                overflow: 'auto',
                mt: 1
              }}
            >
              {isLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : error ? (
                <Alert severity="error" sx={{ m: 1 }}>{error}</Alert>
              ) : isCompletionMode ? (
                <List dense disablePadding>
                  {groupedSuggestions.completions.length > 0 ? (
                    groupedSuggestions.completions.map((suggestion, index) => (
                      <ListItem 
                        key={index} 
                        button 
                        dense
                        onClick={() => handleInsertCompletion(suggestion.text)}
                        divider={index < groupedSuggestions.completions.length - 1}
                      >
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          {getSuggestionTypeIcon(suggestion.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={suggestion.text}
                          secondary={getSuggestionTypeLabel(suggestion.type)}
                          primaryTypographyProps={{ fontFamily: 'monospace' }}
                        />
                      </ListItem>
                    ))
                  ) : (
                    <ListItem>
                      <ListItemText primary="No completions available" />
                    </ListItem>
                  )}
                </List>
              ) : (
                <List dense disablePadding>
                  {suggestions.length > 0 ? (
                    suggestions.map((suggestion, index) => (
                      <ListItem 
                        key={index} 
                        button 
                        dense
                        divider={index < suggestions.length - 1}
                      >
                        <ListItemText
                          primary={
                            <Typography 
                              variant="body2" 
                              component="pre" 
                              sx={{
                                fontFamily: 'monospace',
                                whiteSpace: 'pre-wrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                display: '-webkit-box',
                                WebkitLineClamp: 3,
                                WebkitBoxOrient: 'vertical'
                              }}
                            >
                              {suggestion.sql_text}
                            </Typography>
                          }
                          secondary={
                            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                              {getSuggestionTypeIcon(suggestion.type)}
                              <Typography variant="caption" sx={{ ml: 0.5 }}>
                                {getSuggestionTypeLabel(suggestion.type)}
                              </Typography>
                              {suggestion.tables && suggestion.tables.length > 0 && (
                                <Chip 
                                  size="small" 
                                  label={`Tables: ${suggestion.tables.join(', ')}`}
                                  sx={{ ml: 1, height: 20, fontSize: '0.6rem' }}
                                />
                              )}
                            </Box>
                          }
                        />
                        <Box sx={{ display: 'flex' }}>
                          <Tooltip title="Insert">
                            <IconButton 
                              size="small" 
                              onClick={() => handleInsertSuggestion(suggestion)}
                            >
                              <ContentCopyIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          {onRunSuggestion && (
                            <Tooltip title="Run">
                              <IconButton 
                                size="small" 
                                onClick={() => handleRunSuggestion(suggestion)}
                              >
                                <PlayArrowIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Box>
                      </ListItem>
                    ))
                  ) : (
                    <ListItem>
                      <ListItemText primary="No suggestions available" />
                    </ListItem>
                  )}
                </List>
              )}
            </Paper>
          </Fade>
        )}
      </Popper>
    );
  }
  
  // Render the sidebar version
  return (
    <Paper 
      elevation={0} 
      variant="outlined" 
      sx={{ 
        width: width,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      <Box sx={{ 
        p: 1, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        borderBottom: '1px solid',
        borderColor: 'divider'
      }}>
        <Typography variant="subtitle2">
          Query Suggestions
        </Typography>
        <IconButton 
          size="small" 
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      
      <Collapse in={expanded} sx={{ flexGrow: 1, overflow: 'auto' }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
        ) : suggestions.length === 0 ? (
          <Box sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary" align="center">
              No suggestions available. Start typing a query to see suggestions.
            </Typography>
          </Box>
        ) : (
          <List dense disablePadding sx={{ overflow: 'auto' }}>
            {suggestions.map((suggestion, index) => (
              <React.Fragment key={index}>
                <ListItem 
                  alignItems="flex-start"
                  sx={{ 
                    pt: 1, 
                    pb: 1
                  }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography variant="body2" fontWeight="medium">
                          {getSuggestionTypeLabel(suggestion.type)}
                        </Typography>
                        {suggestion.tables && suggestion.tables.length > 0 && (
                          <Chip 
                            size="small" 
                            label={`Tables: ${suggestion.tables.join(', ')}`}
                            variant="outlined"
                            sx={{ ml: 1, height: 20, fontSize: '0.6rem' }}
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Typography 
                        variant="body2" 
                        component="pre" 
                        sx={{
                          fontFamily: 'monospace',
                          whiteSpace: 'pre-wrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          mt: 0.5,
                          p: 1,
                          bgcolor: 'action.hover',
                          borderRadius: 1,
                          fontSize: '0.8rem',
                          display: '-webkit-box',
                          WebkitLineClamp: 6,
                          WebkitBoxOrient: 'vertical'
                        }}
                      >
                        {suggestion.sql_text}
                      </Typography>
                    }
                  />
                </ListItem>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', px: 2, pb: 1 }}>
                  <Tooltip title={isFavorite(suggestion) ? "Remove from favorites" : "Add to favorites"}>
                    <IconButton 
                      size="small" 
                      color={isFavorite(suggestion) ? "primary" : "default"}
                      onClick={() => toggleFavorite(suggestion)}
                    >
                      {isFavorite(suggestion) ? <StarIcon fontSize="small" /> : <StarOutlineIcon fontSize="small" />}
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Copy to clipboard">
                    <IconButton 
                      size="small" 
                      onClick={() => handleCopySuggestion(suggestion)}
                    >
                      <ContentCopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Insert into editor">
                    <IconButton 
                      size="small" 
                      onClick={() => handleInsertSuggestion(suggestion)}
                    >
                      <ContentCopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  
                  {onRunSuggestion && (
                    <Tooltip title="Run query">
                      <IconButton 
                        size="small" 
                        color="primary"
                        onClick={() => handleRunSuggestion(suggestion)}
                      >
                        <PlayArrowIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
                {index < suggestions.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Collapse>
    </Paper>
  );
};

export default QuerySuggestions;

// Son güncelleme: 2025-05-21 07:25:48
// Güncelleyen: Teeksss