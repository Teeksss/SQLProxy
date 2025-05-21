/**
 * SQL Proxy TypeScript SDK Client
 * 
 * A TypeScript client for interacting with SQL Proxy API.
 * 
 * Last updated: 2025-05-20 11:25:24
 * Updated by: Teeksss
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { v4 as uuidv4 } from 'uuid';
import * as zlib from 'zlib';
import { promisify } from 'util';

// Configuration interfaces
export interface ServerConfig {
  server_id: number;
  server_alias: string;
  description?: string;
  server_type: string;
  environment: string;
  features: {
    read_only: boolean;
    allowed_operations: string[];
    transaction_support: boolean;
    batch_support: boolean;
    prepared_statements: boolean;
  };
  connection_info: {
    pool_size: number;
    max_overflow: number;
    pool_recycle: number;
  };
}

export interface ClientConfig {
  client_id: string;
  api_version: string;
  generated_at: string;
  expires_at?: string;
  servers: ServerConfig[];
  settings: {
    connect_timeout_seconds: number;
    request_timeout_seconds: number;
    max_retries: number;
    retry_delay_seconds: number;
    enable_response_validation: boolean;
    enable_ssl_verification: boolean;
    enable_compression: boolean;
    cache_ttl_seconds: number;
    max_batch_size: number;
    logging_level: string;
    max_result_size: number;
    result_streaming_threshold: number;
  };
  rate_limit: {
    requests_per_minute: number;
    max_concurrent_requests: number;
  };
  api: {
    base_url: string;
    query_endpoint: string;
    batch_endpoint: string;
    status_endpoint: string;
  };
}

export interface ClientOptions {
  api_key: string;
  config_path?: string;
  client_config?: ClientConfig;
  logger?: any;
  custom_headers?: Record<string, string>;
  on_error?: (error: Error) => void;
  retry_non_idempotent?: boolean;
}

// Query interfaces
export interface QueryParams {
  [key: string]: any;
}

export interface QueryOptions {
  timeout_seconds?: number;
  max_rows?: number;
  include_metadata?: boolean;
  stream_results?: boolean;
  transaction_id?: string;
  server_alias?: string;
}

export interface QueryResult {
  columns: string[];
  data: any[][];
  metadata?: {
    row_count: number;
    execution_time_ms: number;
    cached: boolean;
    query_hash: string;
  };
}

export interface BatchQueryResult {
  results: QueryResult[];
  metadata?: {
    execution_time_ms: number;
    success_count: number;
    error_count: number;
  };
}

export interface TransactionOptions {
  timeout_seconds?: number;
  server_alias: string;
  isolation_level?: 'READ_UNCOMMITTED' | 'READ_COMMITTED' | 'REPEATABLE_READ' | 'SERIALIZABLE';
}

export class SQLProxyError extends Error {
  status_code: number;
  error_code?: string;
  query?: string;
  server_alias?: string;
  
  constructor(message: string, status_code: number, error_code?: string, query?: string, server_alias?: string) {
    super(message);
    this.name = 'SQLProxyError';
    this.status_code = status_code;
    this.error_code = error_code;
    this.query = query;
    this.server_alias = server_alias;
  }
}

/**
 * SQL Proxy Client
 * 
 * A TypeScript client for interacting with SQL Proxy API.
 */
export class SQLProxyClient {
  private api_key: string;
  private client_config: ClientConfig;
  private axios_instance: AxiosInstance;
  private logger: any;
  private request_count: number = 0;
  private last_request_timestamp: number = 0;
  private cache: Map<string, { data: QueryResult, timestamp: number }> = new Map();
  private active_transactions: Map<string, { server_alias: string, start_time: number }> = new Map();
  
  /**
   * Create a new SQL Proxy client instance
   * @param options Client configuration options
   */
  constructor(options: ClientOptions) {
    this.api_key = options.api_key;
    
    // Set up logging
    this.logger = options.logger || console;
    
    // Load configuration
    if (options.client_config) {
      this.client_config = options.client_config;
    } else if (options.config_path) {
      try {
        // In Node.js environment
        if (typeof require !== 'undefined') {
          const fs = require('fs');
          const configData = fs.readFileSync(options.config_path, 'utf8');
          this.client_config = JSON.parse(configData);
        } else {
          throw new Error('Config path provided but unable to load file in browser environment');
        }
      } catch (error) {
        throw new Error(`Failed to load client configuration: ${error.message}`);
      }
    } else {
      throw new Error('Either client_config or config_path must be provided');
    }
    
    // Create axios instance
    const axiosConfig: AxiosRequestConfig = {
      baseURL: this.client_config.api.base_url,
      timeout: this.client_config.settings.request_timeout_seconds * 1000,
      headers: {
        'Authorization': `Bearer ${this.api_key}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Client-ID': this.client_config.client_id,
        'X-SDK-Version': `typescript-${this.client_config.api_version}`,
        ...options.custom_headers
      }
    };
    
    this.axios_instance = axios.create(axiosConfig);
    
    // Add request interceptor for retry logic
    this.axios_instance.interceptors.request.use(
      (config) => {
        // Add request ID for tracing
        config.headers['X-Request-ID'] = uuidv4();
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Add response interceptor for error handling
    this.axios_instance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = error.config;
        
        // Add retry count to config if not present
        if (!config['retryCount']) {
          config['retryCount'] = 0;
        }
        
        // Check if we should retry the request
        if (config['retryCount'] < this.client_config.settings.max_retries) {
          // Only retry idempotent requests by default
          const method = config.method.toUpperCase();
          if (method === 'GET' || method === 'HEAD' || method === 'OPTIONS' || options.retry_non_idempotent) {
            config['retryCount'] += 1;
            
            // Wait before retrying
            const delay = this.client_config.settings.retry_delay_seconds * 1000 * config['retryCount'];
            await new Promise(resolve => setTimeout(resolve, delay));
            
            this.logger.info(`Retrying request (${config['retryCount']}/${this.client_config.settings.max_retries})`);
            return this.axios_instance(config);
          }
        }
        
        // Create custom error
        if (error.response) {
          const status = error.response.status;
          const data = error.response.data;
          const error_code = data.error_code || 'UNKNOWN_ERROR';
          const message = data.detail || data.message || error.message;
          
          throw new SQLProxyError(
            message,
            status,
            error_code,
            config.data?.query,
            config.data?.server_alias
          );
        } else {
          throw new SQLProxyError(
            error.message || 'Network error',
            0,
            'NETWORK_ERROR'
          );
        }
      }
    );
    
    this.logger.info(`SQLProxyClient initialized for client_id: ${this.client_config.client_id}`);
  }
  
  /**
   * Execute a SQL query
   * @param query SQL query to execute
   * @param params Query parameters
   * @param options Query options
   * @returns Query result
   */
  async query(query: string, params: QueryParams = {}, options: QueryOptions = {}): Promise<QueryResult> {
    this._throttle_requests();
    
    // Check cache
    const cache_key = this._get_cache_key(query, params, options);
    if (this.client_config.settings.cache_ttl_seconds > 0 && options.server_alias) {
      const cached = this.cache.get(cache_key);
      if (cached) {
        const now = Date.now();
        const age = now - cached.timestamp;
        if (age < this.client_config.settings.cache_ttl_seconds * 1000) {
          this.logger.debug(`Cache hit for query: ${query.substring(0, 50)}...`);
          return cached.data;
        }
      }
    }
    
    // Find server alias if not provided
    const server_alias = options.server_alias || this._get_default_server_alias();
    
    // Check if server exists
    const server = this._get_server_by_alias(server_alias);
    if (!server) {
      throw new SQLProxyError(`Server not found: ${server_alias}`, 400, 'SERVER_NOT_FOUND');
    }
    
    // Determine if this is part of a transaction
    let transaction_id = options.transaction_id;
    if (transaction_id && !this.active_transactions.has(transaction_id)) {
      throw new SQLProxyError(
        `Transaction not found or expired: ${transaction_id}`,
        400,
        'TRANSACTION_NOT_FOUND'
      );
    }
    
    // Check operation permissions
    const operation = this._get_operation_type(query);
    if (!server.features.allowed_operations.includes(operation)) {
      throw new SQLProxyError(
        `Operation not allowed: ${operation} on server ${server_alias}`,
        403,
        'OPERATION_NOT_ALLOWED'
      );
    }
    
    try {
      // Prepare request
      const endpoint = this.client_config.api.query_endpoint;
      const request_data = {
        query,
        params,
        server_alias,
        transaction_id,
        options: {
          timeout_seconds: options.timeout_seconds || this.client_config.settings.request_timeout_seconds,
          max_rows: options.max_rows || undefined,
          include_metadata: options.include_metadata !== false,  // Default to true
          stream_results: options.stream_results || false
        }
      };
      
      // Check if we should use compression
      let compressed_data: string | undefined;
      if (this.client_config.settings.enable_compression && query.length > 1000) {
        const gzip = promisify(zlib.gzip);
        const buffer = await gzip(Buffer.from(JSON.stringify(request_data)));
        compressed_data = buffer.toString('base64');
      }
      
      // Execute request
      const response = await this.axios_instance.post(
        endpoint,
        compressed_data ? { compressed_data } : request_data,
        {
          headers: compressed_data ? { 'Content-Encoding': 'gzip' } : {},
          timeout: (options.timeout_seconds || this.client_config.settings.request_timeout_seconds) * 1000
        }
      );
      
      const result: QueryResult = response.data;
      
      // Validate result if enabled
      if (this.client_config.settings.enable_response_validation) {
        this._validate_query_result(result);
      }
      
      // Cache result if cacheable (SELECT queries only)
      if (this.client_config.settings.cache_ttl_seconds > 0 && operation === 'SELECT') {
        this.cache.set(cache_key, {
          data: result,
          timestamp: Date.now()
        });
      }
      
      return result;
    } catch (error) {
      if (error instanceof SQLProxyError) {
        throw error;
      } else {
        throw new SQLProxyError(
          `Query execution failed: ${error.message}`,
          error.response?.status || 500,
          'QUERY_EXECUTION_ERROR',
          query,
          server_alias
        );
      }
    }
  }
  
  /**
   * Execute a batch of SQL queries
   * @param queries Array of {query, params, options} objects
   * @param server_alias Server to execute queries on
   * @returns Batch query result
   */
  async batch(
    queries: Array<{query: string, params?: QueryParams, options?: Omit<QueryOptions, 'server_alias'>}>,
    server_alias?: string
  ): Promise<BatchQueryResult> {
    this._throttle_requests();
    
    // Check if batch size is within limits
    if (queries.length > this.client_config.settings.max_batch_size) {
      throw new SQLProxyError(
        `Batch size exceeds limit: ${queries.length} > ${this.client_config.settings.max_batch_size}`,
        400,
        'BATCH_SIZE_EXCEEDED'
      );
    }
    
    // Find server alias if not provided
    const effective_server_alias = server_alias || this._get_default_server_alias();
    
    // Check if server exists
    const server = this._get_server_by_alias(effective_server_alias);
    if (!server) {
      throw new SQLProxyError(`Server not found: ${effective_server_alias}`, 400, 'SERVER_NOT_FOUND');
    }
    
    // Check if server supports batch operations
    if (!server.features.batch_support) {
      throw new SQLProxyError(
        `Server does not support batch operations: ${effective_server_alias}`,
        400,
        'BATCH_NOT_SUPPORTED'
      );
    }
    
    // Check operation permissions for all queries
    for (const [index, query_item] of queries.entries()) {
      const operation = this._get_operation_type(query_item.query);
      if (!server.features.allowed_operations.includes(operation)) {
        throw new SQLProxyError(
          `Operation not allowed: ${operation} on server ${effective_server_alias} (query ${index + 1})`,
          403,
          'OPERATION_NOT_ALLOWED'
        );
      }
    }
    
    try {
      // Prepare request
      const endpoint = this.client_config.api.batch_endpoint;
      const request_data = {
        queries: queries.map(q => ({
          query: q.query,
          params: q.params || {},
          options: q.options || {}
        })),
        server_alias: effective_server_alias
      };
      
      // Execute request
      const response = await this.axios_instance.post(endpoint, request_data);
      
      const result: BatchQueryResult = response.data;
      
      // Validate result if enabled
      if (this.client_config.settings.enable_response_validation) {
        this._validate_batch_result(result);
      }
      
      return result;
    } catch (error) {
      if (error instanceof SQLProxyError) {
        throw error;
      } else {
        throw new SQLProxyError(
          `Batch execution failed: ${error.message}`,
          error.response?.status || 500,
          'BATCH_EXECUTION_ERROR',
          undefined,
          effective_server_alias
        );
      }
    }
  }
  
  /**
   * Begin a new transaction
   * @param options Transaction options
   * @returns Transaction ID
   */
  async beginTransaction(options: TransactionOptions): Promise<string> {
    this._throttle_requests();
    
    // Check if server exists
    const server = this._get_server_by_alias(options.server_alias);
    if (!server) {
      throw new SQLProxyError(`Server not found: ${options.server_alias}`, 400, 'SERVER_NOT_FOUND');
    }
    
    // Check if server supports transactions
    if (!server.features.transaction_support) {
      throw new SQLProxyError(
        `Server does not support transactions: ${options.server_alias}`,
        400,
        'TRANSACTIONS_NOT_SUPPORTED'
      );
    }
    
    try {
      // Prepare request
      const endpoint = `${this.client_config.api.base_url}/v1/transaction/begin`;
      const request_data = {
        server_alias: options.server_alias,
        isolation_level: options.isolation_level,
        timeout_seconds: options.timeout_seconds
      };
      
      // Execute request
      const response = await this.axios_instance.post(endpoint, request_data);
      
      const transaction_id = response.data.transaction_id;
      
      // Track transaction
      this.active_transactions.set(transaction_id, {
        server_alias: options.server_alias,
        start_time: Date.now()
      });
      
      return transaction_id;
    } catch (error) {
      if (error instanceof SQLProxyError) {
        throw error;
      } else {
        throw new SQLProxyError(
          `Failed to begin transaction: ${error.message}`,
          error.response?.status || 500,
          'TRANSACTION_BEGIN_ERROR',
          undefined,
          options.server_alias
        );
      }
    }
  }
  
  /**
   * Commit a transaction
   * @param transaction_id Transaction ID to commit
   * @returns Success status
   */
  async commitTransaction(transaction_id: string): Promise<boolean> {
    this._throttle_requests();
    
    // Check if transaction exists
    const transaction = this.active_transactions.get(transaction_id);
    if (!transaction) {
      throw new SQLProxyError(
        `Transaction not found or expired: ${transaction_id}`,
        400,
        'TRANSACTION_NOT_FOUND'
      );
    }
    
    try {
      // Prepare request
      const endpoint = `${this.client_config.api.base_url}/v1/transaction/commit`;
      const request_data = {
        transaction_id
      };
      
      // Execute request
      const response = await this.axios_instance.post(endpoint, request_data);
      
      // Remove transaction from tracking
      this.active_transactions.delete(transaction_id);
      
      return response.data.success;
    } catch (error) {
      if (error instanceof SQLProxyError) {
        throw error;
      } else {
        throw new SQLProxyError(
          `Failed to commit transaction: ${error.message}`,
          error.response?.status || 500,
          'TRANSACTION_COMMIT_ERROR',
          undefined,
          transaction.server_alias
        );
      }
    }
  }
  
  /**
   * Rollback a transaction
   * @param transaction_id Transaction ID to rollback
   * @returns Success status
   */
  async rollbackTransaction(transaction_id: string): Promise<boolean> {
    this._throttle_requests();
    
    // Check if transaction exists
    const transaction = this.active_transactions.get(transaction_id);
    if (!transaction) {
      throw new SQLProxyError(
        `Transaction not found or expired: ${transaction_id}`,
        400,
        'TRANSACTION_NOT_FOUND'
      );
    }
    
    try {
      // Prepare request
      const endpoint = `${this.client_config.api.base_url}/v1/transaction/rollback`;
      const request_data = {
        transaction_id
      };
      
      // Execute request
      const response = await this.axios_instance.post(endpoint, request_data);
      
      // Remove transaction from tracking
      this.active_transactions.delete(transaction_id);
      
      return response.data.success;
    } catch (error) {
      if (error instanceof SQLProxyError) {
        throw error;
      } else {
        throw new SQLProxyError(
          `Failed to rollback transaction: ${error.message}`,
          error.response?.status || 500,
          'TRANSACTION_ROLLBACK_ERROR',
          undefined,
          transaction.server_alias
        );
      }
    }
  }
  
  /**
   * Check API status
   * @returns Status information
   */
  async getStatus(): Promise<any> {
    try {
      const response = await this.axios_instance.get(this.client_config.api.status_endpoint);
      return response.data;
    } catch (error) {
      throw new SQLProxyError(
        `Failed to get status: ${error.message}`,
        error.response?.status || 500,
        'STATUS_ERROR'
      );
    }
  }
  
  /**
   * Get available servers
   * @returns List of available servers
   */
  getServers(): ServerConfig[] {
    return this.client_config.servers;
  }
  
  /**
   * Clear the query cache
   */
  clearCache(): void {
    this.cache.clear();
    this.logger.info('Query cache cleared');
  }
  
  /**
   * Get client configuration
   * @returns Current client configuration
   */
  getConfig(): ClientConfig {
    return this.client_config;
  }
  
  /**
   * Execute a transaction with automatic commit/rollback
   * @param callback Transaction function that receives a transaction object
   * @param options Transaction options
   * @returns Result of the callback function
   */
  async transaction<T>(
    callback: (tx: { 
      query: (query: string, params?: QueryParams, options?: Omit<QueryOptions, 'server_alias' | 'transaction_id'>) => Promise<QueryResult> 
    }) => Promise<T>,
    options: TransactionOptions
  ): Promise<T> {
    // Begin transaction
    const transaction_id = await this.beginTransaction(options);
    
    try {
      // Create transaction query function
      const txQuery = async (
        query: string,
        params: QueryParams = {},
        options: Omit<QueryOptions, 'server_alias' | 'transaction_id'> = {}
      ) => {
        return this.query(
          query,
          params,
          {
            ...options,
            server_alias: options.server_alias || this.active_transactions.get(transaction_id)?.server_alias,
            transaction_id
          }
        );
      };
      
      // Execute callback
      const result = await callback({ query: txQuery });
      
      // Commit transaction
      await this.commitTransaction(transaction_id);
      
      return result;
    } catch (error) {
      // Rollback transaction on error
      try {
        await this.rollbackTransaction(transaction_id);
      } catch (rollbackError) {
        this.logger.error(`Failed to rollback transaction: ${rollbackError.message}`);
      }
      
      throw error;
    }
  }
  
  /**
   * Throttle requests based on rate limit
   * @private
   */
  private _throttle_requests(): void {
    const now = Date.now();
    const elapsed = now - this.last_request_timestamp;
    
    // Check if we need to throttle
    if (this.request_count >= this.client_config.rate_limit.requests_per_minute) {
      // Reset counter if a minute has passed
      if (elapsed >= 60000) {
        this.request_count = 0;
        this.last_request_timestamp = now;
      } else {
        // Sleep to respect rate limit
        const sleep_time = 60000 - elapsed;
        this.logger.debug(`Rate limit reached, sleeping for ${sleep_time}ms`);
        // In browser environment, we can't block synchronously, but in Node.js we could
        // For now, just warn about rate limit
        throw new SQLProxyError(
          `Rate limit exceeded: ${this.client_config.rate_limit.requests_per_minute} requests per minute`,
          429,
          'RATE_LIMIT_EXCEEDED'
        );
      }
    }
    
    // Update counter
    this.request_count++;
    this.last_request_timestamp = now;
  }
  
  /**
   * Get default server alias
   * @private
   * @returns Default server alias
   */
  private _get_default_server_alias(): string {
    if (this.client_config.servers.length === 0) {
      throw new SQLProxyError('No servers configured', 400, 'NO_SERVERS_CONFIGURED');
    }
    
    return this.client_config.servers[0].server_alias;
  }
  
  /**
   * Get server by alias
   * @private
   * @param alias Server alias
   * @returns Server configuration or undefined if not found
   */
  private _get_server_by_alias(alias: string): ServerConfig | undefined {
    return this.client_config.servers.find(s => s.server_alias === alias);
  }
  
  /**
   * Get operation type from SQL query
   * @private
   * @param query SQL query
   * @returns Operation type (SELECT, INSERT, UPDATE, DELETE, etc.)
   */
  private _get_operation_type(query: string): string {
    const normalized = query.trim().toUpperCase();
    
    if (normalized.startsWith('SELECT')) return 'SELECT';
    if (normalized.startsWith('INSERT')) return 'INSERT';
    if (normalized.startsWith('UPDATE')) return 'UPDATE';
    if (normalized.startsWith('DELETE')) return 'DELETE';
    if (normalized.startsWith('CREATE')) return 'CREATE';
    if (normalized.startsWith('ALTER')) return 'ALTER';
    if (normalized.startsWith('DROP')) return 'DROP';
    if (normalized.startsWith('TRUNCATE')) return 'TRUNCATE';
    if (normalized.startsWith('GRANT')) return 'GRANT';
    if (normalized.startsWith('REVOKE')) return 'REVOKE';
    
    return 'UNKNOWN';
  }
  
  /**
   * Get cache key for a query
   * @private
   * @param query SQL query
   * @param params Query parameters
   * @param options Query options
   * @returns Cache key
   */
  private _get_cache_key(query: string, params: QueryParams, options: QueryOptions): string {
    const key = {
      query,
      params,
      server_alias: options.server_alias,
      max_rows: options.max_rows
    };
    
    return JSON.stringify(key);
  }
  
  /**
   * Validate query result
   * @private
   * @param result Query result to validate
   */
  private _validate_query_result(result: QueryResult): void {
    if (!result || !Array.isArray(result.columns) || !Array.isArray(result.data)) {
      throw new SQLProxyError(
        'Invalid query result format',
        500,
        'INVALID_RESULT_FORMAT'
      );
    }
  }
  
  /**
   * Validate batch query result
   * @private
   * @param result Batch query result to validate
   */
  private _validate_batch_result(result: BatchQueryResult): void {
    if (!result || !Array.isArray(result.results)) {
      throw new SQLProxyError(
        'Invalid batch result format',
        500,
        'INVALID_RESULT_FORMAT'
      );
    }
    
    // Validate each result
    for (const [index, query_result] of result.results.entries()) {
      try {
        this._validate_query_result(query_result);
      } catch (error) {
        throw new SQLProxyError(
          `Invalid result format for query ${index + 1}: ${error.message}`,
          500,
          'INVALID_RESULT_FORMAT'
        );
      }
    }
  }
}

// Son güncelleme: 2025-05-20 11:25:24
// Güncelleyen: Teeksss