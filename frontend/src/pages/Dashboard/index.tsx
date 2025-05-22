import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import styled from 'styled-components';
import { getQueryStats } from '../../services/api';
import { Card, LoadingSpinner } from '../../components/UI';

const DashboardContainer = styled.div`
  padding: 2rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
`;

const StatsCard = styled(Card)`
  padding: 1rem;
`;

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchStats = async () => {
      const data = await getQueryStats();
      setStats(data);
      setLoading(false);
    };
    
    fetchStats();
  }, []);
  
  if (loading) return <LoadingSpinner />;
  
  return (
    <DashboardContainer>
      <StatsCard>
        <h3>Query Execution Times</h3>
        <Line data={stats.executionTimes} />
      </StatsCard>
      
      <StatsCard>
        <h3>Query Types Distribution</h3>
        <Pie data={stats.queryTypes} />
      </StatsCard>
      
      <StatsCard>
        <h3>Error Rate</h3>
        <Line data={stats.errorRates} />
      </StatsCard>
      
      <StatsCard>
        <h3>Database Usage</h3>
        <Bar data={stats.databaseUsage} />
      </StatsCard>
    </DashboardContainer>
  );
};