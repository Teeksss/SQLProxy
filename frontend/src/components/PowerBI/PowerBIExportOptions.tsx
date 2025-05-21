/**
 * PowerBI Export Options Component
 * 
 * Provides options for exporting PowerBI reports in different formats
 * 
 * Last updated: 2025-05-21 06:23:45
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  FormControlLabel,
  Checkbox,
  RadioGroup,
  Radio,
  TextField
} from '@mui/material';
import { useMutation } from 'react-query';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import ImageIcon from '@mui/icons-material/Image';
import SlideshowIcon from '@mui/icons-material/Slideshow';
import TableChartIcon from '@mui/icons-material/TableChart';
import { toast } from 'react-toastify';

import { powerbiApi } from '../../services/powerbiService';

interface PowerBIExportOptionsProps {
  reportId: string;
  reportName: string;
  workspaceId?: string;
  pages?: { name: string; displayName: string }[];
}

const PowerBIExportOptions: React.FC<PowerBIExportOptionsProps> = ({
  reportId,
  reportName,
  workspaceId,
  pages = []
}) => {
  const [selectedFormat, setSelectedFormat] = useState<string | null>(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [selectedPages, setSelectedPages] = useState<string[]>([]);
  const [allPages, setAllPages] = useState(true);
  const [imageOptions, setImageOptions] = useState({
    width: 1920,
    height: 1080,
    pageName: pages.length > 0 ? pages[0].name : ''
  });

  // Mutation for exporting to PDF
  const exportToPdfMutation = useMutation(
    (pageNames: string[] | undefined) => 
      powerbiApi.exportReportToPdf(reportId, pageNames, workspaceId),
    {
      onSuccess: () => {
        toast.success('Report exported to PDF successfully');
        setExportDialogOpen(false);
      },
      onError: (error: any) => {
        toast.error(`Error exporting to PDF: ${error.message}`);
      }
    }
  );

  // Mutation for exporting to PowerPoint
  const exportToPptxMutation = useMutation(
    (pageNames: string[] | undefined) => 
      powerbiApi.exportReportToPptx(reportId, pageNames, workspaceId),
    {
      onSuccess: () => {
        toast.success('Report exported to PowerPoint successfully');
        setExportDialogOpen(false);
      },
      onError: (error: any) => {
        toast.error(`Error exporting to PowerPoint: ${error.message}`);
      }
    }
  );

  // Mutation for exporting to PNG
  const exportToPngMutation = useMutation(
    (options: { pageName: string; width: number; height: number }) => 
      powerbiApi.exportReportPageToPng(
        reportId, 
        options.pageName, 
        options.width, 
        options.height, 
        workspaceId
      ),
    {
      onSuccess: () => {
        toast.success('Report page exported to PNG successfully');
        setExportDialogOpen(false);
      },
      onError: (error: any) => {
        toast.error(`Error exporting to PNG: ${error.message}`);
      }
    }
  );

  // Handle format selection
  const handleFormatSelect = (format: string) => {
    setSelectedFormat(format);
    setExportDialogOpen(true);
    
    // Reset selections
    setSelectedPages([]);
    setAllPages(true);
  };

  // Handle page selection
  const handlePageSelection = (pageName: string) => {
    if (selectedPages.includes(pageName)) {
      setSelectedPages(selectedPages.filter(name => name !== pageName));
    } else {
      setSelectedPages([...selectedPages, pageName]);
    }
  };

  // Handle all pages toggle
  const handleAllPagesToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setAllPages(event.target.checked);
    if (event.target.checked) {
      setSelectedPages([]);
    }
  };

  // Handle image option change
  const handleImageOptionChange = (field: string, value: any) => {
    setImageOptions({
      ...imageOptions,
      [field]: value
    });
  };

  // Handle export
  const handleExport = () => {
    const pageNames = allPages ? undefined : selectedPages;
    
    if (selectedFormat === 'pdf') {
      exportToPdfMutation.mutate(pageNames);
    } else if (selectedFormat === 'pptx') {
      exportToPptxMutation.mutate(pageNames);
    } else if (selectedFormat === 'png') {
      exportToPngMutation.mutate({
        pageName: imageOptions.pageName,
        width: imageOptions.width,
        height: imageOptions.height
      });
    } else if (selectedFormat === 'data') {
      // This is handled differently - we notify user in UI
      setExportDialogOpen(false);
    }
  };

  // Determine if export button should be disabled
  const isExportDisabled = () => {
    if (selectedFormat === 'pdf' || selectedFormat === 'pptx') {
      return !allPages && selectedPages.length === 0;
    } else if (selectedFormat === 'png') {
      return !imageOptions.pageName || imageOptions.width <= 0 || imageOptions.height <= 0;
    }
    return false;
  };

  // Determine if any export mutation is loading
  const isLoading = 
    exportToPdfMutation.isLoading || 
    exportToPptxMutation.isLoading || 
    exportToPngMutation.isLoading;

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom>
        Export Options
      </Typography>
      
      <Paper variant="outlined">
        <List>
          <ListItem disablePadding>
            <ListItemButton onClick={() => handleFormatSelect('pdf')}>
              <ListItemIcon>
                <PictureAsPdfIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary="Export to PDF" secondary="Export the entire report or selected pages as PDF" />
            </ListItemButton>
          </ListItem>
          
          <Divider component="li" />
          
          <ListItem disablePadding>
            <ListItemButton onClick={() => handleFormatSelect('png')}>
              <ListItemIcon>
                <ImageIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary="Export as Image (PNG)" secondary="Export a specific page as a high-resolution image" />
            </ListItemButton>
          </ListItem>
          
          <Divider component="li" />
          
          <ListItem disablePadding>
            <ListItemButton onClick={() => handleFormatSelect('pptx')}>
              <ListItemIcon>
                <SlideshowIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary="Export to PowerPoint" secondary="Export the report as a PowerPoint presentation" />
            </ListItemButton>
          </ListItem>
          
          <Divider component="li" />
          
          <ListItem disablePadding>
            <ListItemButton onClick={() => handleFormatSelect('data')}>
              <ListItemIcon>
                <TableChartIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary="Export Data" secondary="Export the underlying data as CSV, Excel or JSON" />
            </ListItemButton>
          </ListItem>
        </List>
      </Paper>
      
      {/* Export Dialog */}
      <Dialog 
        open={exportDialogOpen} 
        onClose={() => setExportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Export Report: {selectedFormat?.toUpperCase()}
        </DialogTitle>
        
        <DialogContent dividers>
          {/* PDF and PowerPoint Options */}
          {(selectedFormat === 'pdf' || selectedFormat === 'pptx') && (
            <Box>
              <FormControl fullWidth component="fieldset">
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={allPages}
                      onChange={handleAllPagesToggle}
                    />
                  }
                  label="Include all pages"
                />
              </FormControl>
              
              {!allPages && pages.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Select pages to include:
                  </Typography>
                  
                  <List dense>
                    {pages.map((page) => (
                      <ListItem key={page.name} disablePadding>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={selectedPages.includes(page.name)}
                              onChange={() => handlePageSelection(page.name)}
                            />
                          }
                          label={page.displayName}
                        />
                      </ListItem>
                    ))}
                  </List>
                  
                  {selectedPages.length === 0 && (
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      Please select at least one page or choose "Include all pages"
                    </Alert>
                  )}
                </Box>
              )}
            </Box>
          )}
          
          {/* PNG Options */}
          {selectedFormat === 'png' && (
            <Box>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Select page to export:
                </Typography>
                
                <RadioGroup
                  value={imageOptions.pageName}
                  onChange={(e) => handleImageOptionChange('pageName', e.target.value)}
                >
                  {pages.map((page) => (
                    <FormControlLabel
                      key={page.name}
                      value={page.name}
                      control={<Radio />}
                      label={page.displayName}
                    />
                  ))}
                </RadioGroup>
              </FormControl>
              
              <Typography variant="subtitle2" gutterBottom>
                Image dimensions:
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
                <TextField
                  label="Width (px)"
                  type="number"
                  size="small"
                  value={imageOptions.width}
                  onChange={(e) => handleImageOptionChange('width', parseInt(e.target.value))}
                  InputProps={{ inputProps: { min: 100, max: 3840 } }}
                />
                
                <TextField
                  label="Height (px)"
                  type="number"
                  size="small"
                  value={imageOptions.height}
                  onChange={(e) => handleImageOptionChange('height', parseInt(e.target.value))}
                  InputProps={{ inputProps: { min: 100, max: 2160 } }}
                />
              </Box>
              
              {(!imageOptions.pageName || imageOptions.width <= 0 || imageOptions.height <= 0) && (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  Please select a page and specify valid dimensions
                </Alert>
              )}
            </Box>
          )}
          
          {/* Data Export Options */}
          {selectedFormat === 'data' && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Data export is handled directly through the PowerBI report interface. 
                Please use the "Export data" option in the report.
              </Alert>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>
            Cancel
          </Button>
          
          <Button
            variant="contained"
            onClick={handleExport}
            disabled={isExportDisabled() || isLoading}
          >
            {isLoading ? (
              <CircularProgress size={24} />
            ) : (
              'Export'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PowerBIExportOptions;

// Son güncelleme: 2025-05-21 06:23:45
// Güncelleyen: Teeksss