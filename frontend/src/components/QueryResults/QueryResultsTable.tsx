/**
 * Query Results Table Component
 * 
 * Displays SQL query results in a table format with sorting, filtering,
 * and data export capabilities.
 * 
 * Last updated: 2025-05-20 12:33:36
 * Updated by: Teeksss
 */

import React, { useState, useMemo, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  CircularProgress, 
  Button, 
  IconButton, 
  Tooltip, 
  TextField,
  Menu,
  MenuItem,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TablePagination,
  Toolbar,
  Divider
} from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';
import GetAppIcon from '@mui/icons-material/GetApp';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DescriptionIcon from '@mui/icons-material/Description';
import BubbleChartIcon from '@mui/icons-material/BubbleChart';
import { CSVLink } from 'react-csv';

import { QueryResult } from '../../types/api';
import { formatCellValue } from '../../utils/formatters';
import QueryResultsVisualization from './QueryResultsVisualization';
import QueryStatistics from './QueryStatistics';
import FilterDialog from './FilterDialog';
import ColumnVisibilityMenu from './ColumnVisibilityMenu';

interface QueryResultsTableProps {
  results: QueryResult | null;
  isLoading: boolean;
  error: string | null;
  onVisualize?: (data: any) => void;
}

type SortDirection = 'asc' | 'desc';

interface SortConfig {
  column: string;
  direction: SortDirection;
}

interface Filter {
  column: string;
  operator: string;
  value: string;
}

const QueryResultsTable: React.FC<QueryResultsTableProps> = ({
  results,
  isLoading,
  error,
  onVisualize
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
  const [filters, setFilters] = useState<Filter[]>([]);
  const [showFilterDialog, setShowFilterDialog] = useState(false);
  const [activeFilter, setActiveFilter] = useState<Filter | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showVisualization, setShowVisualization] = useState(false);
  const [showStatistics, setShowStatistics] = useState(false);
  const [copyFormat, setCopyFormat] = useState<'csv' | 'json'>('csv');
  const [copiedData, setCopiedData] = useState<string | null>(null);
  const [copiedRowIndex, setCopiedRowIndex] = useState<number | null>(null);

  // Initialize visible columns when results change
  useEffect(() => {
    if (results?.columns) {
      setVisibleColumns(results.columns);
    }
  }, [results?.columns]);

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    if (!results || !results.data) return [];

    let processedData = [...results.data];

    // Apply filters
    if (filters.length > 0) {
      processedData = processedData.filter(row => {
        return filters.every(filter => {
          const columnIndex = results.columns.indexOf(filter.column);
          if (columnIndex === -1) return true;

          const cellValue = row[columnIndex];
          const filterValue = filter.value;

          switch (filter.operator) {
            case 'equals':
              return String(cellValue) === filterValue;
            case 'contains':
              return String(cellValue).toLowerCase().includes(filterValue.toLowerCase());
            case 'startsWith':
              return String(cellValue).toLowerCase().startsWith(filterValue.toLowerCase());
            case 'endsWith':
              return String(cellValue).toLowerCase().endsWith(filterValue.toLowerCase());
            case 'greaterThan':
              return Number(cellValue) > Number(filterValue);
            case 'lessThan':
              return Number(cellValue) < Number(filterValue);
            case 'isEmpty':
              return cellValue === null || cellValue === undefined || cellValue === '';
            case 'isNotEmpty':
              return cellValue !== null && cellValue !== undefined && cellValue !== '';
            default:
              return true;
          }
        });
      });
    }

    // Apply global search
    if (searchTerm) {
      processedData = processedData.filter(row => {
        return row.some((cell, index) => {
          // Only search in visible columns
          if (!visibleColumns.includes(results.columns[index])) return false;
          return String(cell).toLowerCase().includes(searchTerm.toLowerCase());
        });
      });
    }

    // Apply sorting
    if (sortConfig) {
      const columnIndex = results.columns.indexOf(sortConfig.column);
      if (columnIndex !== -1) {
        processedData.sort((a, b) => {
          const aValue = a[columnIndex];
          const bValue = b[columnIndex];

          // Handle null/undefined values
          if (aValue === null || aValue === undefined) return sortConfig.direction === 'asc' ? -1 : 1;
          if (bValue === null || bValue === undefined) return sortConfig.direction === 'asc' ? 1 : -1;

          // Compare values
          if (typeof aValue === 'number' && typeof bValue === 'number') {
            return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
          }

          // Default string comparison
          const aString = String(aValue).toLowerCase();
          const bString = String(bValue).toLowerCase();
          return sortConfig.direction === 'asc'
            ? aString.localeCompare(bString)
            : bString.localeCompare(aString);
        });
      }
    }

    return processedData;
  }, [results, sortConfig, filters, searchTerm, visibleColumns]);

  // Handle sort request
  const handleSort = (column: string) => {
    let direction: SortDirection = 'asc';
    
    if (sortConfig && sortConfig.column === column) {
      direction = sortConfig.direction === 'asc' ? 'desc' : 'asc';
    }
    
    setSortConfig({ column, direction });
  };

  // Pagination handlers
  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Filter handlers
  const handleAddFilter = () => {
    setActiveFilter(null);
    setShowFilterDialog(true);
  };

  const handleEditFilter = (filter: Filter) => {
    setActiveFilter(filter);
    setShowFilterDialog(true);
  };

  const handleRemoveFilter = (filter: Filter) => {
    setFilters(filters.filter(f => f !== filter));
  };

  const handleFilterSubmit = (filter: Filter) => {
    if (activeFilter) {
      // Edit existing filter
      setFilters(filters.map(f => f === activeFilter ? filter : f));
    } else {
      // Add new filter
      setFilters([...filters, filter]);
    }
    setShowFilterDialog(false);
  };

  // Column visibility handlers
  const handleToggleColumnVisibility = (column: string) => {
    if (visibleColumns.includes(column)) {
      // Remove column if it's currently visible
      setVisibleColumns(visibleColumns.filter(col => col !== column));
    } else {
      // Add column if it's currently hidden
      setVisibleColumns([...visibleColumns, column]);
    }
  };

  const handleShowAllColumns = () => {
    if (results?.columns) {
      setVisibleColumns(results.columns);
    }
  };

  const handleHideAllColumns = () => {
    setVisibleColumns([]);
  };

  // Menu handlers
  const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Copy data handlers
  const handleCopyAsCSV = () => {
    if (!results) return;

    const header = visibleColumns.join(',');
    const visibleColumnIndices = visibleColumns.map(col => results.columns.indexOf(col));
    
    const dataRows = filteredAndSortedData.map(row => 
      visibleColumnIndices.map(index => `"${String(row[index]).replace(/"/g, '""')}"`).join(',')
    );
    
    const csv = [header, ...dataRows].join('\n');
    navigator.clipboard.writeText(csv);
    
    setCopiedData('CSV data copied to clipboard');
    handleMenuClose();
  };

  const handleCopyAsJSON = () => {
    if (!results) return;

    const visibleColumnIndices = visibleColumns.map(col => results.columns.indexOf(col));
    
    const jsonData = filteredAndSortedData.map(row => {
      const obj: Record<string, any> = {};
      visibleColumnIndices.forEach(index => {
        obj[results.columns[index]] = row[index];
      });
      return obj;
    });
    
    navigator.clipboard.writeText(JSON.stringify(jsonData, null, 2));
    
    setCopiedData('JSON data copied to clipboard');
    handleMenuClose();
  };

  const handleCopyRow = (rowIndex: number) => {
    if (!results) return;

    const row = filteredAndSortedData[rowIndex];
    const visibleColumnIndices = visibleColumns.map(col => results.columns.indexOf(col));
    
    if (copyFormat === 'csv') {
      const csvRow = visibleColumnIndices
        .map(index => `"${String(row[index]).replace(/"/g, '""')}"`)
        .join(',');
      navigator.clipboard.writeText(csvRow);
    } else {
      const jsonRow: Record<string, any> = {};
      visibleColumnIndices.forEach(index => {
        jsonRow[results.columns[index]] = row[index];
      });
      navigator.clipboard.writeText(JSON.stringify(jsonRow, null, 2));
    }
    
    setCopiedRowIndex(rowIndex);
    setTimeout(() => setCopiedRowIndex(null), 1500);
  };

  // CSV export data preparation
  const csvData = useMemo(() => {
    if (!results) return [];

    const visibleColumnIndices = visibleColumns.map(col => results.columns.indexOf(col));
    
    // Header row
    const header = visibleColumns;
    
    // Data rows
    const dataRows = filteredAndSortedData.map(row => {
      const csvRow: Record<string, any> = {};
      visibleColumnIndices.forEach((index, i) => {
        csvRow[visibleColumns[i]] = row[index];
      });
      return csvRow;
    });
    
    return [header, ...dataRows];
  }, [results, filteredAndSortedData, visibleColumns]);

  // Render empty state
  if (!results && !isLoading && !error) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="textSecondary">
          Run a query to see results
        </Typography>
      </Box>
    );
  }

  // Render loading state
  if (isLoading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Executing query...
        </Typography>
      </Box>
    );
  }

  // Render error state
  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography variant="h6" color="error" gutterBottom>
          Error executing query
        </Typography>
        <Typography variant="body1">{error}</Typography>
      </Box>
    );
  }

  // Render visualization if enabled
  if (showVisualization && results) {
    return (
      <Box sx={{ p: 2 }}>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
          <Button 
            variant="outlined" 
            onClick={() => setShowVisualization(false)}
          >
            Back to Results Table
          </Button>
          {onVisualize && (
            <Button 
              variant="contained" 
              onClick={() => onVisualize(filteredAndSortedData)}
            >
              Export Visualization
            </Button>
          )}
        </Box>
        <QueryResultsVisualization 
          data={filteredAndSortedData} 
          columns={results.columns} 
          visibleColumns={visibleColumns}
        />
      </Box>
    );
  }

  // Render statistics if enabled
  if (showStatistics && results) {
    return (
      <Box sx={{ p: 2 }}>
        <Box sx={{ mb: 2 }}>
          <Button 
            variant="outlined" 
            onClick={() => setShowStatistics(false)}
          >
            Back to Results Table
          </Button>
        </Box>
        <QueryStatistics 
          data={filteredAndSortedData} 
          columns={results.columns}
          metadata={results.metadata}
        />
      </Box>
    );
  }

  // Render results table
  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <Toolbar sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', width: '100%', alignItems: 'center' }}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 0, mr: 2 }}>
            Results
          </Typography>
          
          {results && (
            <Chip 
              label={`${filteredAndSortedData.length} rows`} 
              size="small" 
              color="primary" 
              sx={{ mr: 2 }} 
            />
          )}
          
          <Box sx={{ flexGrow: 1 }}>
            <TextField
              placeholder="Search results..."
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              sx={{ minWidth: 200 }}
              InputProps={{
                startAdornment: (
                  <Box sx={{ mr: 1, display: 'flex' }}>
                    <FilterListIcon fontSize="small" />
                  </Box>
                ),
              }}
            />
          </Box>
          
          <Box>
            {filters.map((filter, index) => (
              <Chip
                key={index}
                label={`${filter.column} ${filter.operator} ${filter.value}`}
                onDelete={() => handleRemoveFilter(filter)}
                onClick={() => handleEditFilter(filter)}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>
          
          <Tooltip title="Add Filter">
            <IconButton onClick={handleAddFilter}>
              <FilterListIcon />
            </IconButton>
          </Tooltip>
          
          <ColumnVisibilityMenu
            columns={results?.columns || []}
            visibleColumns={visibleColumns}
            onToggleColumn={handleToggleColumnVisibility}
            onShowAll={handleShowAllColumns}
            onHideAll={handleHideAllColumns}
          />
          
          {results && (
            <CSVLink
              data={csvData}
              filename={`query_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`}
              className="hidden-link"
            >
              <Tooltip title="Export as CSV">
                <IconButton>
                  <GetAppIcon />
                </IconButton>
              </Tooltip>
            </CSVLink>
          )}
          
          <Tooltip title="More Options">
            <IconButton
              onClick={handleMenuOpen}
              aria-controls="results-menu"
              aria-haspopup="true"
            >
              <MoreVertIcon />
            </IconButton>
          </Tooltip>
          
          <Menu
            id="results-menu"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => { setShowVisualization(true); handleMenuClose(); }}>
              <BubbleChartIcon fontSize="small" sx={{ mr: 1 }} />
              Visualize Data
            </MenuItem>
            <MenuItem onClick={() => { setShowStatistics(true); handleMenuClose(); }}>
              <DescriptionIcon fontSize="small" sx={{ mr: 1 }} />
              Show Statistics
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleCopyAsCSV}>
              <ContentCopyIcon fontSize="small" sx={{ mr: 1 }} />
              Copy as CSV
            </MenuItem>
            <MenuItem onClick={handleCopyAsJSON}>
              <ContentCopyIcon fontSize="small" sx={{ mr: 1 }} />
              Copy as JSON
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
      
      {copiedData && (
        <Box sx={{ p: 1, bgcolor: 'success.light', color: 'success.contrastText' }}>
          <Typography variant="body2">{copiedData}</Typography>
        </Box>
      )}
      
      <TableContainer sx={{ maxHeight: 'calc(100vh - 300px)' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: 50 }}>#</TableCell>
              {results?.columns.map((column, index) => (
                visibleColumns.includes(column) && (
                  <TableCell key={index}>
                    <TableSortLabel
                      active={sortConfig?.column === column}
                      direction={sortConfig?.column === column ? sortConfig.direction : 'asc'}
                      onClick={() => handleSort(column)}
                    >
                      {column}
                    </TableSortLabel>
                  </TableCell>
                )
              ))}
              <TableCell sx={{ width: 50 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAndSortedData
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row, rowIndex) => (
                <TableRow 
                  key={rowIndex}
                  hover
                  sx={{
                    backgroundColor: copiedRowIndex === rowIndex + page * rowsPerPage ? 'action.selected' : 'inherit',
                    transition: 'background-color 0.3s'
                  }}
                >
                  <TableCell>{rowIndex + 1 + page * rowsPerPage}</TableCell>
                  {results?.columns.map((column, colIndex) => (
                    visibleColumns.includes(column) && (
                      <TableCell key={colIndex} sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {formatCellValue(row[colIndex])}
                      </TableCell>
                    )
                  ))}
                  <TableCell>
                    <Tooltip title="Copy Row">
                      <IconButton 
                        size="small" 
                        onClick={() => handleCopyRow(rowIndex + page * rowsPerPage)}
                      >
                        <ContentCopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            {filteredAndSortedData.length === 0 && (
              <TableRow>
                <TableCell colSpan={visibleColumns.length + 2} align="center">
                  No results found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={filteredAndSortedData.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      
      {/* Filter Dialog */}
      {showFilterDialog && (
        <FilterDialog
          open={showFilterDialog}
          columns={results?.columns || []}
          initialFilter={activeFilter}
          onClose={() => setShowFilterDialog(false)}
          onSubmit={handleFilterSubmit}
        />
      )}
    </Paper>
  );
};

export default QueryResultsTable;

// Son güncelleme: 2025-05-20 12:33:36
// Güncelleyen: Teeksss