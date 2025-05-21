/**
 * Formatters Utility
 * 
 * Utility functions for formatting various data types
 * 
 * Last updated: 2025-05-21 07:14:55
 * Updated by: Teeksss
 */

import { format as dateFnsFormat, formatDistanceToNow } from 'date-fns';

/**
 * Format bytes to human-readable format
 * 
 * @param bytes Bytes value
 * @param decimals Number of decimal places
 * @returns Formatted size string
 */
export const formatBytes = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
};

/**
 * Format milliseconds to human-readable duration
 * 
 * @param ms Milliseconds
 * @returns Formatted duration string
 */
export const formatDuration = (ms: number): string => {
  if (ms === undefined || ms === null) return 'N/A';
  
  if (ms < 1000) {
    return `${ms} ms`;
  }
  
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  }
  
  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  }
  
  return `${seconds}s`;
};

/**
 * Format date string to relative time (e.g., 2 hours ago)
 * 
 * @param dateString Date string
 * @param addSuffix Whether to add suffix
 * @returns Relative time string
 */
export const formatRelativeTime = (dateString: string, addSuffix: boolean = true): string => {
  try {
    const date = new Date(dateString);
    return formatDistanceToNow(date, { addSuffix });
  } catch (error) {
    return 'Invalid date';
  }
};

/**
 * Format date string to specified format
 * 
 * @param dateString Date string
 * @param formatString Format string
 * @returns Formatted date string
 */
export const formatDate = (dateString: string, formatString: string = 'yyyy-MM-dd HH:mm:ss'): string => {
  try {
    const date = new Date(dateString);
    return dateFnsFormat(date, formatString);
  } catch (error) {
    return 'Invalid date';
  }
};

/**
 * Format number with comma separators
 * 
 * @param value Number value
 * @param decimals Number of decimal places
 * @returns Formatted number string
 */
export const formatNumber = (value: number, decimals: number = 0): string => {
  try {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  } catch (error) {
    return String(value);
  }
};

/**
 * Format percentage value
 * 
 * @param value Percentage value (0-100)
 * @param decimals Number of decimal places
 * @returns Formatted percentage string
 */
export const formatPercent = (value: number, decimals: number = 1): string => {
  try {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }) + '%';
  } catch (error) {
    return String(value) + '%';
  }
};

/**
 * Format SQL query text for display
 * 
 * @param sql SQL query text
 * @param maxLength Maximum length before truncation
 * @returns Formatted SQL text
 */
export const formatSql = (sql: string, maxLength: number = 100): string => {
  // Remove extra whitespace
  const trimmed = sql.replace(/\s+/g, ' ').trim();
  
  // Truncate if needed
  if (trimmed.length <= maxLength) {
    return trimmed;
  }
  
  return trimmed.substring(0, maxLength) + '...';
};

/**
 * Format boolean value to Yes/No
 * 
 * @param value Boolean value
 * @returns "Yes" or "No"
 */
export const formatBoolean = (value: boolean): string => {
  return value ? 'Yes' : 'No';
};

/**
 * Format database object name
 * 
 * @param schema Schema name
 * @param name Object name
 * @returns Formatted database object name
 */
export const formatDbObjectName = (schema: string | null | undefined, name: string): string => {
  if (schema) {
    return `${schema}.${name}`;
  }
  return name;
};

// Son güncelleme: 2025-05-21 07:14:55
// Güncelleyen: Teeksss