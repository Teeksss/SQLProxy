/**
 * Masking Rule Form Component
 * 
 * Form for creating and editing data masking rules
 * 
 * Last updated: 2025-05-20 14:59:32
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  FormHelperText,
  Grid,
  Typography,
  Divider,
  Paper,
  Alert,
  Button
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useQuery } from 'react-query';

import { MaskingRule, MaskingRuleType, MaskingMethod } from '../../types/masking';
import { queryApi } from '../../services/queryService';

interface MaskingRuleFormProps {
  initialData?: MaskingRule;
  onSubmit: (values: Partial<MaskingRule>) => void;
  isSubmitting?: boolean;
}

// Validation schema for masking rule form
const validationSchema = Yup.object().shape({
  name: Yup.string().required('Name is required'),
  rule_type: Yup.string().required('Rule type is required'),
  description: Yup.string(),
  masking_method: Yup.string().required('Masking method is required'),
  pattern: Yup.string().when('rule_type', {
    is: MaskingRuleType.GLOBAL,
    then: Yup.string().required('Pattern is required for global rules')
  }),
  column_name: Yup.string().when('rule_type', {
    is: MaskingRuleType.COLUMN,
    then: Yup.string().required('Column name is required for column rules')
  })
});

const MaskingRuleForm: React.FC<MaskingRuleFormProps> = ({ 
  initialData, 
  onSubmit,
  isSubmitting = false
}) => {
  const [testPattern, setTestPattern] = useState('');
  const [testResult, setTestResult] = useState<string | null>(null);
  
  // Query for getting column names (for autocomplete)
  const { data: columnSuggestions } = useQuery(
    ['columnSuggestions'],
    () => queryApi.getCommonColumnNames(),
    {
      enabled: true,
      staleTime: 3600000, // 1 hour
    }
  );
  
  // Initialize form with default values or initial data
  const formik = useFormik({
    initialValues: {
      name: initialData?.name || '',
      rule_type: initialData?.rule_type || MaskingRuleType.GLOBAL,
      description: initialData?.description || '',
      masking_method: initialData?.masking_method || MaskingMethod.REDACT,
      pattern: initialData?.pattern || '',
      column_name: initialData?.column_name || ''
    },
    validationSchema,
    onSubmit: (values) => {
      onSubmit(values);
    }
  });
  
  // Test pattern against sample text
  const handleTestPattern = () => {
    if (!formik.values.pattern || !testPattern) {
      setTestResult('Please enter both a pattern and test text');
      return;
    }
    
    try {
      const regex = new RegExp(formik.values.pattern);
      const matches = testPattern.match(regex);
      
      if (matches && matches.length > 0) {
        // Apply a simple masking to show the match
        let maskedText = testPattern;
        for (const match of matches) {
          maskedText = maskedText.replace(match, '[REDACTED]');
        }
        setTestResult(`Pattern matched! Result: ${maskedText}`);
      } else {
        setTestResult('Pattern did not match any part of the test text');
      }
    } catch (error) {
      setTestResult(`Invalid regular expression: ${(error as Error).message}`);
    }
  };
  
  return (
    <Box component="form" id="masking-rule-form" onSubmit={formik.handleSubmit} sx={{ mt: 1 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="name"
            name="name"
            label="Rule Name"
            value={formik.values.name}
            onChange={formik.handleChange}
            error={formik.touched.name && Boolean(formik.errors.name)}
            helperText={formik.touched.name && formik.errors.name}
            disabled={isSubmitting}
            margin="normal"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControl 
            fullWidth 
            margin="normal"
            error={formik.touched.rule_type && Boolean(formik.errors.rule_type)}
          >
            <InputLabel id="rule-type-label">Rule Type</InputLabel>
            <Select
              labelId="rule-type-label"
              id="rule_type"
              name="rule_type"
              value={formik.values.rule_type}
              onChange={formik.handleChange}
              disabled={isSubmitting || !!initialData}
              label="Rule Type"
            >
              <MenuItem value={MaskingRuleType.GLOBAL}>Global Pattern Rule</MenuItem>
              <MenuItem value={MaskingRuleType.COLUMN}>Column-Specific Rule</MenuItem>
            </Select>
            {formik.touched.rule_type && formik.errors.rule_type && (
              <FormHelperText>{formik.errors.rule_type}</FormHelperText>
            )}
          </FormControl>
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            id="description"
            name="description"
            label="Description"
            value={formik.values.description}
            onChange={formik.handleChange}
            error={formik.touched.description && Boolean(formik.errors.description)}
            helperText={formik.touched.description && formik.errors.description}
            disabled={isSubmitting}
            margin="normal"
            multiline
            rows={2}
          />
        </Grid>
        
        <Grid item xs={12}>
          <FormControl 
            fullWidth 
            margin="normal"
            error={formik.touched.masking_method && Boolean(formik.errors.masking_method)}
          >
            <InputLabel id="masking-method-label">Masking Method</InputLabel>
            <Select
              labelId="masking-method-label"
              id="masking_method"
              name="masking_method"
              value={formik.values.masking_method}
              onChange={formik.handleChange}
              disabled={isSubmitting}
              label="Masking Method"
            >
              <MenuItem value={MaskingMethod.REDACT}>Redact (Replace with [REDACTED])</MenuItem>
              <MenuItem value={MaskingMethod.HASH}>Hash (Cryptographic hash)</MenuItem>
              <MenuItem value={MaskingMethod.PARTIAL}>Partial (Show only first/last characters)</MenuItem>
              <MenuItem value={MaskingMethod.TOKENIZE}>Tokenize (Consistent replacement)</MenuItem>
            </Select>
            {formik.touched.masking_method && formik.errors.masking_method && (
              <FormHelperText>{formik.errors.masking_method}</FormHelperText>
            )}
          </FormControl>
        </Grid>
        
        {formik.values.rule_type === MaskingRuleType.GLOBAL && (
          <Grid item xs={12}>
            <Box>
              <TextField
                fullWidth
                id="pattern"
                name="pattern"
                label="Regex Pattern"
                value={formik.values.pattern}
                onChange={formik.handleChange}
                error={formik.touched.pattern && Boolean(formik.errors.pattern)}
                helperText={
                  (formik.touched.pattern && formik.errors.pattern) || 
                  "Regular expression pattern to match sensitive data (e.g., \\b\\d{3}-\\d{2}-\\d{4}\\b for SSN)"
                }
                disabled={isSubmitting}
                margin="normal"
              />
              
              <Paper elevation={0} variant="outlined" sx={{ p: 2, mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Test Pattern
                </Typography>
                <TextField
                  fullWidth
                  label="Test Text"
                  value={testPattern}
                  onChange={(e) => setTestPattern(e.target.value)}
                  margin="normal"
                  size="small"
                  placeholder="Enter text to test the pattern against"
                />
                <Box sx={{ mt: 1, mb: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={handleTestPattern}
                    disabled={!formik.values.pattern || !testPattern}
                  >
                    Test Pattern
                  </Button>
                </Box>
                {testResult && (
                  <Alert 
                    severity={testResult.includes('Invalid') || testResult.includes('did not match') ? 'error' : 'success'}
                    sx={{ mt: 1 }}
                  >
                    {testResult}
                  </Alert>
                )}
              </Paper>
              
              <Typography variant="subtitle2" sx={{ mt: 2 }}>
                Common Pattern Examples:
              </Typography>
              <Grid container spacing={1} sx={{ mt: 0.5 }}>
                <Grid item xs={12} md={6}>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    fullWidth
                    onClick={() => formik.setFieldValue('pattern', '\\b(?:\\d{4}[ -]?){3}\\d{4}\\b|\\b\\d{16}\\b')}
                    sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                  >
                    Credit Card Numbers
                  </Button>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    fullWidth
                    onClick={() => formik.setFieldValue('pattern', '\\b\\d{3}[-]?\\d{2}[-]?\\d{4}\\b')}
                    sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                  >
                    Social Security Numbers
                  </Button>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    fullWidth
                    onClick={() => formik.setFieldValue('pattern', '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b')}
                    sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                  >
                    Email Addresses
                  </Button>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    fullWidth
                    onClick={() => formik.setFieldValue('pattern', '\\b(?:\\+\\d{1,3}[-\\.\\s]?)?\\(?\\d{3}\\)?[-\\.\\s]?\\d{3}[-\\.\\s]?\\d{4}\\b')}
                    sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                  >
                    Phone Numbers
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </Grid>
        )}
        
        {formik.values.rule_type === MaskingRuleType.COLUMN && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              id="column_name"
              name="column_name"
              label="Column Name"
              value={formik.values.column_name}
              onChange={formik.handleChange}
              error={formik.touched.column_name && Boolean(formik.errors.column_name)}
              helperText={
                (formik.touched.column_name && formik.errors.column_name) ||
                "Name of the database column to mask (e.g., 'email', 'credit_card', 'ssn')"
              }
              disabled={isSubmitting}
              margin="normal"
              select={!!columnSuggestions && columnSuggestions.length > 0}
            >
              {columnSuggestions && columnSuggestions.map((column: string) => (
                <MenuItem key={column} value={column}>
                  {column}
                </MenuItem>
              ))}
            </TextField>
            
            <Typography variant="subtitle2" sx={{ mt: 2 }}>
              Common Column Examples:
            </Typography>
            <Grid container spacing={1} sx={{ mt: 0.5 }}>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  onClick={() => formik.setFieldValue('column_name', 'email')}
                  sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                >
                  email
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  onClick={() => formik.setFieldValue('column_name', 'credit_card')}
                  sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                >
                  credit_card
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  onClick={() => formik.setFieldValue('column_name', 'ssn')}
                  sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                >
                  ssn
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  onClick={() => formik.setFieldValue('column_name', 'password')}
                  sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                >
                  password
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  onClick={() => formik.setFieldValue('column_name', 'phone')}
                  sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                >
                  phone
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  fullWidth
                  onClick={() => formik.setFieldValue('column_name', 'address')}
                  sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                >
                  address
                </Button>
              </Grid>
            </Grid>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default MaskingRuleForm;

// Son güncelleme: 2025-05-20 14:59:32
// Güncelleyen: Teeksss