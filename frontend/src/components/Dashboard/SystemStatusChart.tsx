/**
 * System Status Chart Component
 * 
 * Visualizes system service status over time
 * 
 * Last updated: 2025-05-21 06:48:31
 * Updated by: Teeksss
 */

import React from 'react';
import { useTheme } from '@mui/material/styles';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { Box, Typography } from '@mui/material';

// Define service types and statuses for type safety
type ServiceStatus = 'healthy' | 'warning' | 'error' | 'unknown';
type ServiceType = 'powerbi' | 'database' | 'query' | 'auth' | 'scheduler' | 'notification';

interface ServiceInfo {
  id: string;
  name: string;
  type: ServiceType;
  status: ServiceStatus;
  lastChecked: string;
  metrics: {
    responseTime?: number;
    uptime?: number;
    errorRate?: number;
    activeConnections?: number;
    queueSize?: number;
  };
  details?: string;
}

interface SystemStatusChartProps {
  services: ServiceInfo[];
  height?: number | string;
}

const SystemStatusChart: React.FC<SystemStatusChartProps> = ({ 
  services, 
  height = 300 
}) => {
  const theme = useTheme();

  // Count services by status
  const statusCounts = services.reduce((acc: Record<string, number>, service) => {
    acc[service.status] = (acc[service.status] || 0) + 1;
    return acc;
  }, {});

  // Prepare chart data
  const data = Object.entries(statusCounts).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count
  }));

  // Define status colors
  const COLORS = {
    Healthy: theme.palette.success.main,
    Warning: theme.palette.warning.main,
    Error: theme.palette.error.main,
    Unknown: theme.palette.grey[500]
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
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
          <Typography variant="subtitle2">
            {payload[0].name}: {payload[0].value} {payload[0].value === 1 ? 'service' : 'services'}
          </Typography>
        </Box>
      );
    }

    return null;
  };

  return (
    <Box sx={{ width: '100%', height }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            innerRadius={40}
            fill="#8884d8"
            dataKey="value"
            nameKey="name"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || theme.palette.grey[500]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default SystemStatusChart;

// Son güncelleme: 2025-05-21 06:48:31
// Güncelleyen: Teeksss