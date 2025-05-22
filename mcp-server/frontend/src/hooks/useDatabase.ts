import { useState, useCallback } from 'react';
import { SQLProxyClient } from '../services/sqlproxy';

export const useDatabase = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const executeQuery = useCallback(async (
    query: string,
    params?: Record<string, any>
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await SQLProxyClient.executeQuery(
        query,
        params
      );
      
      setLoading(false);
      return result;
      
    } catch (err) {
      setError(err as Error);
      setLoading(false);
      throw err;
    }
  }, []);
  
  const getAnalytics = useCallback(async (
    timeframe: string = '24h'
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await SQLProxyClient.getAnalytics(
        timeframe
      );
      
      setLoading(false);
      return result;
      
    } catch (err) {
      setError(err as Error);
      setLoading(false);
      throw err;
    }
  }, []);
  
  return {
    executeQuery,
    getAnalytics,
    loading,
    error
  };
};