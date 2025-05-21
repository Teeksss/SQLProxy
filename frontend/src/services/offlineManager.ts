/**
 * Offline Manager Service
 * 
 * Service for managing offline capabilities and synchronization
 * 
 * Last updated: 2025-05-21 07:14:55
 * Updated by: Teeksss
 */

import { openDB, IDBPDatabase, DBSchema } from 'idb';
import { toast } from 'react-toastify';

// Define database schema
interface SQLProxyDB extends DBSchema {
  savedQueries: {
    key: string;
    value: {
      id: string;
      name: string;
      description?: string;
      sql_text: string;
      server_id: string;
      created_at: string;
      updated_at: string;
      user_id: number;
      is_favorite: boolean;
      tags: string[];
      sync_status: 'synced' | 'pending' | 'error';
    };
    indexes: { 'by-user': number; 'by-server': string; 'by-sync-status': string };
  };
  queryHistory: {
    key: string;
    value: {
      id: string;
      sql_text: string;
      server_id: string;
      executed_at: string;
      duration_ms: number;
      row_count?: number;
      status: string;
      error_message?: string;
      user_id: number;
      sync_status: 'synced' | 'pending' | 'error';
    };
    indexes: { 'by-user': number; 'by-server': string; 'by-sync-status': string };
  };
  serverCache: {
    key: string;
    value: {
      id: string;
      host: string;
      port: number;
      database: string;
      username: string;
      db_type: string;
      cached_at: string;
      metadata?: {
        tables: Array<{
          name: string;
          schema?: string;
          columns?: Array<{
            name: string;
            data_type: string;
          }>;
        }>;
      };
    };
  };
  syncQueue: {
    key: string;
    value: {
      id: string;
      entity_type: 'query' | 'history' | 'server';
      entity_id: string;
      action: 'create' | 'update' | 'delete';
      data: any;
      created_at: string;
      retry_count: number;
      error?: string;
    };
    indexes: { 'by-entity-type': string };
  };
  appSettings: {
    key: string;
    value: {
      id: string;
      offline_mode_enabled: boolean;
      last_sync: string;
      cache_expiry_days: number;
      sync_on_startup: boolean;
      max_offline_storage_mb: number;
      user_id?: number;
      ui_preferences?: any;
    };
  };
}

class OfflineManager {
  private db: IDBPDatabase<SQLProxyDB> | null = null;
  private isOnline: boolean = true;
  private syncTimer: number | null = null;
  private initialized: boolean = false;
  
  /**
   * Initialize the offline manager
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }
    
    try {
      // Open IndexedDB database
      this.db = await openDB<SQLProxyDB>('sql-proxy-db', 1, {
        upgrade(db) {
          // Create object stores and indexes
          if (!db.objectStoreNames.contains('savedQueries')) {
            const savedQueriesStore = db.createObjectStore('savedQueries', { keyPath: 'id' });
            savedQueriesStore.createIndex('by-user', 'user_id');
            savedQueriesStore.createIndex('by-server', 'server_id');
            savedQueriesStore.createIndex('by-sync-status', 'sync_status');
          }
          
          if (!db.objectStoreNames.contains('queryHistory')) {
            const historyStore = db.createObjectStore('queryHistory', { keyPath: 'id' });
            historyStore.createIndex('by-user', 'user_id');
            historyStore.createIndex('by-server', 'server_id');
            historyStore.createIndex('by-sync-status', 'sync_status');
          }
          
          if (!db.objectStoreNames.contains('serverCache')) {
            db.createObjectStore('serverCache', { keyPath: 'id' });
          }
          
          if (!db.objectStoreNames.contains('syncQueue')) {
            const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id' });
            syncStore.createIndex('by-entity-type', 'entity_type');
          }
          
          if (!db.objectStoreNames.contains('appSettings')) {
            db.createObjectStore('appSettings', { keyPath: 'id' });
          }
        }
      });
      
      // Initialize default settings if not exists
      await this.initializeSettings();
      
      // Setup online/offline event listeners
      window.addEventListener('online', this.handleOnlineStatusChange.bind(this));
      window.addEventListener('offline', this.handleOnlineStatusChange.bind(this));
      
      // Set initial online status
      this.isOnline = navigator.onLine;
      
      // Start sync timer if online
      if (this.isOnline) {
        this.startSyncTimer();
      }
      
      this.initialized = true;
      console.log('Offline manager initialized successfully');
    } catch (error) {
      console.error('Error initializing offline manager:', error);
      toast.error('Failed to initialize offline storage');
    }
  }
  
  /**
   * Initialize default settings
   */
  private async initializeSettings(): Promise<void> {
    if (!this.db) {
      return;
    }
    
    // Check if settings exist
    const settings = await this.db.get('appSettings', 'settings');
    
    if (!settings) {
      // Create default settings
      await this.db.put('appSettings', {
        id: 'settings',
        offline_mode_enabled: true,
        last_sync: new Date().toISOString(),
        cache_expiry_days: 7,
        sync_on_startup: true,
        max_offline_storage_mb: 100
      });
    }
  }
  
  /**
   * Handle online/offline status changes
   */
  private handleOnlineStatusChange(): void {
    const isCurrentlyOnline = navigator.onLine;
    
    if (isCurrentlyOnline !== this.isOnline) {
      this.isOnline = isCurrentlyOnline;
      
      if (isCurrentlyOnline) {
        console.log('App is back online');
        toast.info('Connection restored. Syncing data...');
        this.syncData();
        this.startSyncTimer();
      } else {
        console.log('App is offline');
        toast.warning('You are now offline. Changes will be synced when connection is restored.');
        this.stopSyncTimer();
      }
    }
  }
  
  /**
   * Start sync timer
   */
  private startSyncTimer(): void {
    if (this.syncTimer !== null) {
      return;
    }
    
    // Sync every 5 minutes
    this.syncTimer = window.setInterval(() => {
      this.syncData();
    }, 5 * 60 * 1000);
  }
  
  /**
   * Stop sync timer
   */
  private stopSyncTimer(): void {
    if (this.syncTimer !== null) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
  }
  
  /**
   * Sync local data with server
   */
  async syncData(): Promise<void> {
    if (!this.db || !this.isOnline) {
      return;
    }
    
    try {
      // Get pending sync items
      const tx = this.db.transaction('syncQueue', 'readonly');
      const index = tx.store.index('by-entity-type');
      const pendingItems = await index.getAll();
      
      if (pendingItems.length === 0) {
        return;
      }
      
      console.log(`Syncing ${pendingItems.length} pending items`);
      
      // Process sync queue
      for (const item of pendingItems) {
        try {
          await this.processSyncItem(item);
          
          // Remove from sync queue on success
          await this.db.delete('syncQueue', item.id);
        } catch (error) {
          console.error(`Error syncing item ${item.id}:`, error);
          
          // Update retry count and error message
          const updatedItem = {
            ...item,
            retry_count: item.retry_count + 1,
            error: (error as Error).message
          };
          
          await this.db.put('syncQueue', updatedItem);
        }
      }
      
      // Update last sync timestamp
      const settings = await this.db.get('appSettings', 'settings');
      if (settings) {
        await this.db.put('appSettings', {
          ...settings,
          last_sync: new Date().toISOString()
        });
      }
      
      console.log('Sync completed successfully');
    } catch (error) {
      console.error('Error during sync:', error);
    }
  }
  
  /**
   * Process a single sync queue item
   */
  private async processSyncItem(item: any): Promise<void> {
    switch (item.entity_type) {
      case 'query':
        await this.syncSavedQuery(item);
        break;
      case 'history':
        await this.syncQueryHistory(item);
        break;
      case 'server':
        await this.syncServerCache(item);
        break;
      default:
        throw new Error(`Unknown entity type: ${item.entity_type}`);
    }
  }
  
  /**
   * Sync a saved query
   */
  private async syncSavedQuery(item: any): Promise<void> {
    // This would connect to the actual API in a real implementation
    switch (item.action) {
      case 'create':
      case 'update':
        // Update synced status in local DB
        const query = await this.db?.get('savedQueries', item.entity_id);
        if (query) {
          await this.db?.put('savedQueries', {
            ...query,
            sync_status: 'synced'
          });
        }
        break;
      case 'delete':
        // Nothing to do for delete action as item is already deleted locally
        break;
    }
  }
  
  /**
   * Sync a query history item
   */
  private async syncQueryHistory(item: any): Promise<void> {
    // This would connect to the actual API in a real implementation
    switch (item.action) {
      case 'create':
      case 'update':
        // Update synced status in local DB
        const history = await this.db?.get('queryHistory', item.entity_id);
        if (history) {
          await this.db?.put('queryHistory', {
            ...history,
            sync_status: 'synced'
          });
        }
        break;
      case 'delete':
        // Nothing to do for delete action as item is already deleted locally
        break;
    }
  }
  
  /**
   * Sync server cache
   */
  private async syncServerCache(item: any): Promise<void> {
    // This would fetch updated server metadata from the API in a real implementation
    // For now, just mark as synced
    console.log('Server cache sync not implemented yet');
  }
  
  /**
   * Save query to offline storage
   */
  async saveQuery(query: any): Promise<string> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      // Generate ID if not provided
      if (!query.id) {
        query.id = crypto.randomUUID();
      }
      
      // Add sync status and timestamps
      const queryToSave = {
        ...query,
        sync_status: this.isOnline ? 'synced' : 'pending',
        created_at: query.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      // Save to IndexedDB
      await this.db.put('savedQueries', queryToSave);
      
      // Add to sync queue if offline
      if (!this.isOnline) {
        await this.addToSyncQueue({
          entity_type: 'query',
          entity_id: query.id,
          action: 'create',
          data: queryToSave
        });
      }
      
      return query.id;
    } catch (error) {
      console.error('Error saving query to offline storage:', error);
      throw error;
    }
  }
  
  /**
   * Add query execution to history
   */
  async addQueryHistory(queryExecution: any): Promise<string> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      // Generate ID if not provided
      if (!queryExecution.id) {
        queryExecution.id = crypto.randomUUID();
      }
      
      // Add sync status
      const historyToSave = {
        ...queryExecution,
        sync_status: this.isOnline ? 'synced' : 'pending',
        executed_at: queryExecution.executed_at || new Date().toISOString()
      };
      
      // Save to IndexedDB
      await this.db.put('queryHistory', historyToSave);
      
      // Add to sync queue if offline
      if (!this.isOnline) {
        await this.addToSyncQueue({
          entity_type: 'history',
          entity_id: queryExecution.id,
          action: 'create',
          data: historyToSave
        });
      }
      
      return queryExecution.id;
    } catch (error) {
      console.error('Error adding query to history in offline storage:', error);
      throw error;
    }
  }
  
  /**
   * Get saved queries
   */
  async getSavedQueries(userId: number): Promise<any[]> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      const tx = this.db.transaction('savedQueries', 'readonly');
      const index = tx.store.index('by-user');
      return await index.getAll(userId);
    } catch (error) {
      console.error('Error getting saved queries from offline storage:', error);
      throw error;
    }
  }
  
  /**
   * Get query history
   */
  async getQueryHistory(userId: number, limit: number = 100): Promise<any[]> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      const tx = this.db.transaction('queryHistory', 'readonly');
      const index = tx.store.index('by-user');
      const allHistory = await index.getAll(userId);
      
      // Sort by executed_at (newest first) and limit
      return allHistory
        .sort((a, b) => new Date(b.executed_at).getTime() - new Date(a.executed_at).getTime())
        .slice(0, limit);
    } catch (error) {
      console.error('Error getting query history from offline storage:', error);
      throw error;
    }
  }
  
  /**
   * Cache server metadata
   */
  async cacheServerMetadata(serverId: string, metadata: any): Promise<void> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      // Get existing server cache
      const existingCache = await this.db.get('serverCache', serverId);
      
      // Update or create cache
      const serverCache = {
        ...(existingCache || {}),
        id: serverId,
        metadata,
        cached_at: new Date().toISOString()
      };
      
      // Save to IndexedDB
      await this.db.put('serverCache', serverCache);
    } catch (error) {
      console.error('Error caching server metadata:', error);
      throw error;
    }
  }
  
  /**
   * Get cached server metadata
   */
  async getServerMetadata(serverId: string): Promise<any | null> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      const serverCache = await this.db.get('serverCache', serverId);
      
      if (!serverCache) {
        return null;
      }
      
      // Check cache expiry
      const settings = await this.db.get('appSettings', 'settings');
      const expiryDays = settings?.cache_expiry_days || 7;
      
      const cachedDate = new Date(serverCache.cached_at);
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() - expiryDays);
      
      if (cachedDate < expiryDate) {
        console.log(`Server cache expired for server ${serverId}`);
        return null;
      }
      
      return serverCache.metadata;
    } catch (error) {
      console.error('Error getting server metadata from cache:', error);
      throw error;
    }
  }
  
  /**
   * Add item to sync queue
   */
  private async addToSyncQueue(item: any): Promise<void> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      const syncItem = {
        id: crypto.randomUUID(),
        ...item,
        created_at: new Date().toISOString(),
        retry_count: 0
      };
      
      await this.db.add('syncQueue', syncItem);
    } catch (error) {
      console.error('Error adding item to sync queue:', error);
      throw error;
    }
  }
  
  /**
   * Get offline mode status
   */
  async isOfflineModeEnabled(): Promise<boolean> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      const settings = await this.db.get('appSettings', 'settings');
      return settings?.offline_mode_enabled || false;
    } catch (error) {
      console.error('Error getting offline mode status:', error);
      return false;
    }
  }
  
  /**
   * Set offline mode status
   */
  async setOfflineModeEnabled(enabled: boolean): Promise<void> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      const settings = await this.db.get('appSettings', 'settings');
      
      if (settings) {
        await this.db.put('appSettings', {
          ...settings,
          offline_mode_enabled: enabled
        });
      }
    } catch (error) {
      console.error('Error setting offline mode status:', error);
      throw error;
    }
  }
  
  /**
   * Check if app is online
   */
  isAppOnline(): boolean {
    return this.isOnline;
  }
  
  /**
   * Manually trigger data synchronization
   */
  async forceSyncData(): Promise<void> {
    if (!this.isOnline) {
      toast.warning('Cannot sync while offline');
      return;
    }
    
    try {
      toast.info('Syncing data...');
      await this.syncData();
      toast.success('Data synchronized successfully');
    } catch (error) {
      console.error('Error forcing sync:', error);
      toast.error('Error synchronizing data');
    }
  }
  
  /**
   * Clean up expired cache items
   */
  async cleanupExpiredCache(): Promise<void> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      // Get cache expiry setting
      const settings = await this.db.get('appSettings', 'settings');
      const expiryDays = settings?.cache_expiry_days || 7;
      
      // Calculate expiry date
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() - expiryDays);
      
      // Get all server cache items
      const tx = this.db.transaction('serverCache', 'readwrite');
      const serverCacheItems = await tx.store.getAll();
      
      // Delete expired items
      for (const item of serverCacheItems) {
        const cachedDate = new Date(item.cached_at);
        
        if (cachedDate < expiryDate) {
          await tx.store.delete(item.id);
        }
      }
      
      // Commit transaction
      await tx.done;
      
      console.log('Expired cache cleanup completed');
    } catch (error) {
      console.error('Error cleaning up expired cache:', error);
    }
  }
  
  /**
   * Get storage usage statistics
   */
  async getStorageStats(): Promise<any> {
    if (!this.db) {
      throw new Error('Offline storage not initialized');
    }
    
    try {
      // Get counts from each store
      const savedQueriesCount = await this.db.count('savedQueries');
      const queryHistoryCount = await this.db.count('queryHistory');
      const serverCacheCount = await this.db.count('serverCache');
      const syncQueueCount = await this.db.count('syncQueue');
      
      // Get last sync time
      const settings = await this.db.get('appSettings', 'settings');
      const lastSync = settings?.last_sync || null;
      
      // Estimate storage usage (very approximate)
      const totalItems = savedQueriesCount + queryHistoryCount + serverCacheCount + syncQueueCount;
      const estimatedSizeKB = totalItems * 5; // Rough estimate: 5KB per item average
      
      return {
        savedQueries: savedQueriesCount,
        queryHistory: queryHistoryCount,
        serverCache: serverCacheCount,
        syncQueue: syncQueueCount,
        totalItems,
        estimatedSizeKB,
        lastSync
      };
    } catch (error) {
      console.error('Error getting storage stats:', error);
      throw error;
    }
  }
}

// Create singleton instance
const offlineManager = new OfflineManager();

export default offlineManager;

// Son güncelleme: 2025-05-21 07:14:55
// Güncelleyen: Teeksss