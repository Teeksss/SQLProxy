/**
 * Circular Progress with Label Component
 * 
 * Displays a circular progress indicator with a percentage label
 * 
 * Last updated: 2025-05-21 05:32:06
 * Updated by: Teeksss
 */

import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

interface CircularProgressWithLabelProps {
  value: number;
  size?: number;
  thickness?: number;
  color?: 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
}

const CircularProgressWithLabel: React.FC<CircularProgressWithLabelProps> = ({
  value,
  size = 40,
  thickness = 4,
  color = 'primary'
}) => {
  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <CircularProgress
        variant="determinate"
        value={value}
        size={size}
        thickness={thickness}
        color={color}
      />
      <Box
        sx={{
          top: 0,
          left: 0,
          bottom: 0,
          right: 0,
          position: 'absolute',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography
          variant="caption"
          component="div"
          color="text.secondary"
          sx={{ 
            fontSize: size / 4, // Scale font size proportionally to circle size
            fontWeight: 'bold' 
          }}
        >
          {`${Math.round(value)}%`}
        </Typography>
      </Box>
    </Box>
  );
};

export default CircularProgressWithLabel;

// Son güncelleme: 2025-05-21 05:32:06
// Güncelleyen: Teeksss