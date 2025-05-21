/**
 * PowerBI Report Embed Component
 * 
 * Embeds PowerBI reports in the application using the Power BI JavaScript SDK
 * 
 * Last updated: 2025-05-21 05:44:49
 * Updated by: Teeksss
 */

import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography, Alert, Paper, Button } from '@mui/material';
import { service, factories, models, IEmbedConfiguration } from 'powerbi-client';
import { useMutation } from 'react-query';

import { powerbiApi } from '../../services/powerbiService';
import NoDataPlaceholder from '../common/NoDataPlaceholder';

// Create a PowerBI service instance
const powerbi = new service.Service(
  factories.hpmFactory,
  factories.wpmpFactory,
  factories.routerFactory
);

interface PowerBIReportEmbedProps {
  reportId: string;
  embedHeight?: number | string;
  filterPane?: boolean;
  navPane?: boolean;
  onReportPageChange?: (pageName: string) => void;
  onReportLoad?: () => void;
  onReportError?: (error: any) => void;
}

const PowerBIReportEmbed: React.FC<PowerBIReportEmbedProps> = ({
  reportId,
  embedHeight = 600,
  filterPane = true,
  navPane = true,
  onReportPageChange,
  onReportLoad,
  onReportError
}) => {
  const reportContainerRef = useRef<HTMLDivElement>(null);
  const [report, setReport] = useState<any>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Mutation for getting embed token
  const { 
    mutate: getEmbedToken, 
    isLoading, 
    error, 
    data: embedConfig 
  } = useMutation(
    () => powerbiApi.getReportEmbedToken(reportId),
    {
      onError: (error: any) => {
        console.error('Error getting embed token:', error);
        if (onReportError) onReportError(error);
      }
    }
  );

  // Get embed token on component mount
  useEffect(() => {
    if (reportId) {
      getEmbedToken();
    }
  }, [reportId]);

  // Embed report when configuration is available
  useEffect(() => {
    if (embedConfig && reportContainerRef.current) {
      const config: IEmbedConfiguration = {
        type: 'report',
        tokenType: models.TokenType.Embed,
        accessToken: embedConfig.token,
        embedUrl: embedConfig.embed_url,
        id: reportId,
        permissions: models.Permissions.All,
        settings: {
          filterPaneEnabled: filterPane,
          navContentPaneEnabled: navPane,
          background: models.BackgroundType.Transparent
        }
      };

      try {
        // Clear any previous report
        powerbi.reset(reportContainerRef.current);
        
        // Embed the report
        const reportInstance = powerbi.embed(reportContainerRef.current, config) as any;
        setReport(reportInstance);

        // Set up event handlers
        reportInstance.on('loaded', () => {
          console.log('Report loaded');
          if (onReportLoad) onReportLoad();
        });

        reportInstance.on('error', (event: any) => {
          console.error('Report error:', event.detail);
          if (onReportError) onReportError(event.detail);
        });

        reportInstance.on('pageChanged', (event: any) => {
          console.log('Page changed:', event.detail.newPage.displayName);
          if (onReportPageChange) onReportPageChange(event.detail.newPage.displayName);
        });

        // Clean up on unmount
        return () => {
          reportInstance.off('loaded');
          reportInstance.off('error');
          reportInstance.off('pageChanged');
          powerbi.reset(reportContainerRef.current);
        };
      } catch (err) {
        console.error('Error embedding report:', err);
        if (onReportError) onReportError(err);
      }
    }
  }, [embedConfig, reportContainerRef.current, filterPane, navPane]);

  // Handle fullscreen toggle
  const toggleFullscreen = () => {
    if (report) {
      if (!isFullscreen) {
        report.fullscreen();
      } else {
        report.exitFullscreen();
      }
      setIsFullscreen(!isFullscreen);
    }
  };

  // Handle loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: embedHeight }}>
        <CircularProgress />
      </Box>
    );
  }

  // Handle error state
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {(error as Error).message || 'Failed to load PowerBI report'}
      </Alert>
    );
  }

  // Handle missing embed config
  if (!embedConfig) {
    return (
      <NoDataPlaceholder message="PowerBI report configuration not available" />
    );
  }

  return (
    <Box sx={{ width: '100%', mb: 2 }}>
      <Box sx={{ mb: 1, display: 'flex', justifyContent: 'flex-end' }}>
        <Button 
          variant="outlined" 
          size="small" 
          onClick={toggleFullscreen}
        >
          {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
        </Button>
      </Box>
      
      <Paper 
        elevation={0} 
        variant="outlined" 
        ref={reportContainerRef} 
        sx={{ 
          width: '100%', 
          height: embedHeight, 
          position: 'relative',
          overflow: 'hidden'
        }}
      />
    </Box>
  );
};

export default PowerBIReportEmbed;

// Son güncelleme: 2025-05-21 05:44:49
// Güncelleyen: Teeksss