/**
 * System Resources Chart Component
 * 
 * Visualizes system resource usage (CPU, Memory, Disk)
 * 
 * Last updated: 2025-05-21 06:48:31
 * Updated by: Teeksss
 */

import React from 'react';
import { useTheme } from '@mui/material/styles';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from 'recharts';
import { Box, Typography } from '@mui/material';

interface SystemResourcesChartProps {
  data: {
    cpu?: number;
    memory?: number;
    disk?: number;
    network?: number;
  };
  height?: number | string;
}

const SystemResourcesChart: React.FC<SystemResourcesChartProps> = ({ 
  data, 
  height = 300 
}) => {
  const theme = useTheme();

  // Prepare chart data
  const chartData = [
    {
      name: 'CPU',
      usage: data.cpu || 0,
      limit: 100,
      color: theme.palette.primary.main
    },
    {
      name: 'Memory',
      usage: data.memory || 0,
      limit: 100,
      color: theme.palette.secondary.main
    },
    {
      name: 'Disk',
      usage: data.disk || 0,
      limit: 100,
      color: theme.palette.info.main
    },
    {
      name: 'Network',
      usage: data.network || 0,
      limit: 100,
      color: theme.palette.success.main
    }
  ];

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            backgroundColor: 'background.paper',
            p: 1.5,
            border: '1px solid',
            borderColor: 'divider',
            boxShadow: 1,
            borderRadius: 1
          }}
        >
          <Typography variant="subtitle2" color="text.primary">
            {label}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Usage: {payload[0].value}%
          </Typography>
        </Box>
      );
    }

    return null;
  };

  return (
    <Box sx={{ width: '100%', height }}>
      <ResponsiveContainer>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis 
            label={{ value: 'Usage %', angle: -90, position: 'insideLeft' }} 
            domain={[0, 100]} 
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar 
            dataKey="usage" 
            name="Current Usage (%)" 
            fill={theme.palette.primary.main}
            radius={[4, 4, 0, 0]} 
          />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default SystemResourcesChart;

// Son güncelleme: 2025-05-21 06:48:31
// Güncelleyen: Teeksss