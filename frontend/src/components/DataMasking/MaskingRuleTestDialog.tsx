/**
 * Masking Rule Test Dialog Component
 * 
 * Dialog for testing data masking rules with sample data
 * 
 * Last updated: 2025-05-20 14:59:32
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button,
  TextField,
  Typography,
  Box,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider,
  Grid,
  Alert
} from '@mui/material';
import { useMutation } from 'react-query';

import { MaskingRule, MaskingRuleType } from '../../types/masking';
import { maskingApi } from '../../services/maskingService';

interface MaskingRuleTestDialogProps {
  open: boolean;
  onClose: () => void;
  rule: MaskingRule | null;
}

const DEFAULT_TEST_DATA = [
  'John Doe',
  'jane.doe@example.com',
  '123-45-6789',
  '4111-1111-1111-1111',
  '123 Main St, Anytown, USA 12345',
  '192.168.1.1',
  '2025-01-01',
  'PASSPORT123456',
  'Account Number: 1234567890',
  'My password is: p@ssw0rd123!'
];

const MaskingRuleTestDialog: React.FC<MaskingRuleTestDialogProps> = ({ 
  open, 
  onClose, 
  rule 
}) => {
  const [testData, setTestData] = useState<string>(DEFAULT_TEST_DATA.join('\n'));
  
  // Test rule mutation
  const testMutation = useMutation(
    (data: { rule_type: string; masking_method: string; pattern?: string; column_name?: string; test_data: string[] }) => 
      maskingApi.testMaskingRule(data),
    {
      onError: (error: any) => {
        console.error('Error testing masking rule:', error);
      }
    }
  );
  
  // Run test
  const handleRunTest = () => {
    if (!rule) return;
    
    const testDataArray = testData.split('\n').filter(line => line.trim() !== '');
    
    testMutation.mutate({
      rule_type: rule.rule_type,
      masking_method: rule.masking_method,
      pattern: rule.pattern,
      column_name: rule.column_name,
      test_data: testDataArray
    });
  };
  
  // Reset test data to defaults
  const handleResetTestData = () => {
    setTestData(DEFAULT_TEST_DATA.join('\n'));
  };
  
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        Test Masking Rule
        {rule && (
          <Typography variant="subtitle2" color="text.secondary">
            {rule.name}
          </Typography>
        )}
      </DialogTitle>
      <DialogContent>
        {!rule ? (
          <Alert severity="error">No rule selected</Alert>
        ) : (
          <Box>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Rule Details
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" component="span" color="text.secondary">
                        Type:
                      </Typography>
                      <Chip 
                        label={rule.rule_type === MaskingRuleType.GLOBAL ? 'Global Pattern' : 'Column-Specific'} 
                        size="small" 
                        sx={{ ml: 1 }}
                      />
                    </Box>
                    
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" component="span" color="text.secondary">
                        Masking Method:
                      </Typography>
                      <Chip 
                        label={rule.masking_method} 
                        size="small" 
                        sx={{ ml: 1 }} 
                        color={
                          rule.masking_method === 'redact' ? 'error' :
                          rule.masking_method === 'hash' ? 'primary' :
                          rule.masking_method === 'partial' ? 'warning' :
                          'default'
                        }
                      />
                    </Box>
                    
                    {rule.rule_type === MaskingRuleType.GLOBAL && rule.pattern && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Pattern:
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            p: 1, 
                            bgcolor: 'background.default',
                            borderRadius: 1,
                            fontFamily: 'monospace',
                            wordBreak: 'break-all'
                          }}
                        >
                          {rule.pattern}
                        </Typography>
                      </Box>
                    )}
                    
                    {rule.rule_type === MaskingRuleType.COLUMN && rule.column_name && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" component="span" color="text.secondary">
                          Column:
                        </Typography>
                        <Chip 
                          label={rule.column_name} 
                          size="small" 
                          sx={{ ml: 1 }}
                        />
                      </Box>
                    )}
                  </Paper>
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Test Data
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={10}
                    value={testData}
                    onChange={(e) => setTestData(e.target.value)}
                    placeholder="Enter data to test, one item per line"
                    variant="outlined"
                    size="small"
                  />
                  <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between' }}>
                    <Button 
                      variant="outlined" 
                      size="small" 
                      onClick={handleResetTestData}
                    >
                      Reset to Defaults
                    </Button>
                    <Button 
                      variant="contained" 
                      onClick={handleRunTest}
                      disabled={testMutation.isLoading}
                    >
                      {testMutation.isLoading ? <CircularProgress size={24} /> : 'Run Test'}
                    </Button>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Test Results
                </Typography>
                
                {testMutation.isLoading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
                    <CircularProgress />
                  </Box>
                ) : testMutation.isError ? (
                  <Alert severity="error">
                    Error running test. Please check your rule configuration.
                  </Alert>
                ) : testMutation.data ? (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Original</TableCell>
                          <TableCell>Masked</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {testMutation.data.results.map((result, index) => (
                          <TableRow 
                            key={index}
                            sx={{
                              bgcolor: result.matched ? 'rgba(76, 175, 80, 0.1)' : 'inherit'
                            }}
                          >
                            <TableCell sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {result.original}
                            </TableCell>
                            <TableCell sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {result.masked}
                            </TableCell>
                          </TableRow>
                        ))}
                        
                        {testMutation.data.results.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={2} align="center">
                              No test results
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      p: 3, 
                      display: 'flex', 
                      justifyContent: 'center', 
                      alignItems: 'center',
                      height: 300
                    }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      Run the test to see results
                    </Typography>
                  </Paper>
                )}
              </Grid>
            </Grid>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default MaskingRuleTestDialog;

// Son güncelleme: 2025-05-20 14:59:32
// Güncelleyen: Teeksss