/**
 * Query Suggestion Panel Component
 * 
 * Component for displaying ML-powered query suggestions
 * 
 * Last updated: 2025-05-21 07:20:45
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Chip,
  CircularProgress,
  IconButton,
  Collapse,
  Button,
  Tooltip,
  Divider,
  alpha
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import CodeIcon from '@mui/icons-material/Code';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useQuery } from 'react-query';
import { formatSql } from '../../utils/formatters';

import { queryApi } from '../../services/queryService';

interface QuerySuggestionPanelProps {
  sql: string;
  serverId?: string;
  onSelectSuggestion: (sql: string) => void;
  onHide?: () => void;
  minimalMode?: boolean;
}

const QuerySuggestionPanel: React.FC<QuerySuggestionPanelProps> = ({
  sql,
  serverId,
  onSelectSuggestion,
  onHide,
  minimalMode = false
}) => {
  const theme = useTheme();
  const [expanded, setExpanded] = useState<boolean>(!minimalMode);
  
  // Query for fetching suggestions
  const {
    data: suggestions,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['query-suggestions', serverId, sql],
    () => queryApi.getQuerySuggestions({ 
      serverId, 
      currentQuery: sql,
      limit: minimalMode ? 3 : 10
    }),
    {
      enabled: sql.length > 5,  // Only fetch suggestions when query is longer than 5 chars
      staleTime: 10000, // 10 seconds
      refetchOnWindowFocus: false
    }
  );
  
  // Refresh suggestions when SQL changes
  useEffect(() => {
    if (sql.length > 5) {
      refetch();
    }
  }, [sql, serverId]);
  
  // Handle suggestion selection
  const handleSelectSuggestion = (suggestion: any) => {
    onSelectSuggestion(suggestion.sql_text);
  };
  
  // Get source icon
  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'recent_query':
        return <AccessTimeIcon fontSize="small" />;
      case 'similar_query':
        return <TrendingUpIcon fontSize="small" />;
      case 'user_cluster':
        return <CodeIcon fontSize="small" />;
      case 'completion':
        return <CheckCircleIcon fontSize="small" />;
      default:
        return <CodeIcon fontSize="small" />;
    }
  };
  
  // Get source label
  const getSourceLabel = (source: string): string => {
    switch (source) {
      case 'recent_query':
        return 'Recent Query';
      case 'similar_query':
        return 'Similar Query';
      case 'user_cluster':
        return 'Popular Query';
      case 'completion':
        return 'Completion';
      default:
        return source;
    }
  };
  
  // Get source color
  const getSourceColor = (source: string): string => {
    switch (source) {
      case 'recent_query':
        return theme.palette.info.main;
      case 'similar_query':
        return theme.palette.success.main;
      case 'user_cluster':
        return theme.palette.warning.main;
      case 'completion':
        return theme.palette.primary.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  // Format relevance score
  const formatRelevanceScore = (score: number): string => {
    if (score >= 90) return 'Very High';
    if (score >= 70) return 'High';
    if (score >= 50) return 'Medium';
    if (score >= 30) return 'Low';
    return 'Very Low';
  };
  
  // If in minimal mode and not expanded, show compact view
  if (minimalMode && !expanded) {
    return (
      <Box 
        sx={{ 
          p: 1, 
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 1,
          backgroundColor: theme.palette.background.paper
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle2" color="text.secondary">
            Query Suggestions
          </Typography>
          <IconButton
            size="small"
            onClick={() => setExpanded(true)}
            aria-label="expand suggestions"
          >
            <ExpandMoreIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>
    );
  }
  
  return (
    <Paper 
      variant="outlined" 
      sx={{ 
        width: '100%',
        overflow: 'hidden'
      }}
    >
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        p: 1,
        borderBottom: `1px solid ${theme.palette.divider}`
      }}>
        <Typography 
          variant={minimalMode ? "subtitle2" : "subtitle1"} 
          fontWeight="medium"
        >
          Query Suggestions
        </Typography>
        
        <Box>
          {isLoading && (
            <CircularProgress size={16} sx={{ mr: 1 }} />
          )}
          
          {minimalMode && (
            <IconButton
              size="small"
              onClick={() => setExpanded(false)}
              aria-label="collapse suggestions"
            >
              <ExpandLessIcon fontSize="small" />
            </IconButton>
          )}
          
          {onHide && (
            <IconButton
              size="small"
              onClick={onHide}
              aria-label="hide suggestions"
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
      </Box>
      
      <Box sx={{ maxHeight: minimalMode ? 300 : 400, overflow: 'auto' }}>
        {isLoading && !suggestions && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 3 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        
        {error && (
          <Box sx={{ p: 2 }}>
            <Typography color="error" variant="body2">
              Error loading suggestions
            </Typography>
          </Box>
        )}
        
        {!isLoading && !error && suggestions?.length === 0 && (
          <Box sx={{ p: 2 }}>
            <Typography color="text.secondary" variant="body2">
              No suggestions available. Continue typing to get personalized query suggestions.
            </Typography>
          </Box>
        )}
        
        {suggestions && suggestions.length > 0 && (
          <List disablePadding dense={minimalMode}>
            {suggestions.map((suggestion, index) => (
              <React.Fragment key={index}>
                <ListItemButton
                  onClick={() => handleSelectSuggestion(suggestion)}
                  sx={{
                    borderLeft: `3px solid ${getSourceColor(suggestion.source)}`,
                    '&:hover': {
                      backgroundColor: alpha(getSourceColor(suggestion.source), 0.1)
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getSourceIcon(suggestion.source)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography 
                        variant="body2" 
                        component="div" 
                        sx={{ 
                          fontFamily: 'monospace',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                      >
                        {formatSql(suggestion.sql_text, 100)}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                        <Chip
                          label={getSourceLabel(suggestion.source)}
                          size="small"
                          sx={{ 
                            height: 20,
                            fontSize: '0.7rem',
                            mr: 1,
                            backgroundColor: alpha(getSourceColor(suggestion.source), 0.1),
                            color: getSourceColor(suggestion.source),
                            border: `1px solid ${getSourceColor(suggestion.source)}`
                          }}
                        />
                        {suggestion.relevance_score && (
                          <Typography variant="caption" color="text.secondary">
                            Relevance: {formatRelevanceScore(suggestion.relevance_score)}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItemButton>
                {index < suggestions.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Box>
    </Paper>
  );
};

export default QuerySuggestionPanel;

// Son güncelleme: 2025-05-21 07:20:45
// Güncelleyen: Teeksss