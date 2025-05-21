/**
 * Data Masking Types
 * 
 * Type definitions for data masking functionality
 * 
 * Last updated: 2025-05-20 14:59:32
 * Updated by: Teeksss
 */

/**
 * Types of masking rules
 */
export enum MaskingRuleType {
  GLOBAL = 'global',
  COLUMN = 'column'
}

/**
 * Masking methods
 */
export enum MaskingMethod {
  REDACT = 'redact',
  HASH = 'hash',
  PARTIAL = 'partial',
  TOKENIZE = 'tokenize'
}

/**
 * Masking rule interface
 */
export interface MaskingRule {
  id: number;
  name: string;
  rule_type: MaskingRuleType;
  description: string;
  masking_method: MaskingMethod;
  pattern?: string;
  column_name?: string;
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Masking rules response
 */
export interface MaskingRulesResponse {
  global_rules: MaskingRule[];
  column_rules: MaskingRule[];
}

/**
 * Masking rule test result
 */
export interface MaskingRuleTestResult {
  rule_type: MaskingRuleType;
  masking_method: MaskingMethod;
  pattern?: string;
  column_name?: string;
  results: {
    original: string;
    masked: string;
    matched: boolean;
  }[];
}

// Son güncelleme: 2025-05-20 14:59:32
// Güncelleyen: Teeksss