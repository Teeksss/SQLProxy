from typing import Dict, List, Optional
import time
import logging
from datetime import datetime
from .parser import SQLParser
from .optimizer import SQLOptimizer

class SQLDebugger:
    def __init__(self):
        self.parser = SQLParser()
        self.optimizer = SQLOptimizer()
        self.logger = logging.getLogger('sql_debugger')
        
    def debug_query(self, query: str) -> Dict:
        """Query'yi debug eder ve detaylı analiz sağlar."""
        start_time = time.time()
        debug_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'query': query,
            'steps': []
        }
        
        try:
            # Parse analizi
            parse_start = time.time()
            parsed_info = self.parser.parse_query(query)
            debug_info['steps'].append({
                'stage': 'PARSE',
                'duration': time.time() - parse_start,
                'details': parsed_info
            })
            
            # Syntax kontrolü
            syntax_start = time.time()
            is_valid, syntax_error = self.parser.validate_query(query)
            debug_info['steps'].append({
                'stage': 'SYNTAX_CHECK',
                'duration': time.time() - syntax_start,
                'is_valid': is_valid,
                'error': syntax_error
            })
            
            if not is_valid:
                raise ValueError(syntax_error)
                
            # Optimization analizi
            opt_start = time.time()
            optimization = self.optimizer.optimize(query)
            debug_info['steps'].append({
                'stage': 'OPTIMIZATION',
                'duration': time.time() - opt_start,
                'suggestions': optimization['optimizations']
            })
            
            # Execution plan
            plan_start = time.time()
            execution_plan = self._analyze_execution_plan(parsed_info)
            debug_info['steps'].append({
                'stage': 'EXECUTION_PLAN',
                'duration': time.time() - plan_start,
                'plan': execution_plan
            })
            
            # Performance metrics
            debug_info['performance'] = self._analyze_performance(parsed_info)
            
            return debug_info
            
        except Exception as e:
            self.logger.error(f"Debug error: {str(e)}")
            debug_info['error'] = str(e)
            return debug_info
        finally:
            debug_info['total_duration'] = time.time() - start_time
            
    def _analyze_execution_plan(self, parsed_info: Dict) -> Dict:
        """Detaylı execution plan analizi yapar."""
        return {
            'steps': self._get_execution_steps(parsed_info),
            'cost_analysis': self._analyze_cost(parsed_info),
            'index_usage': self._analyze_indexes(parsed_info),
            'table_access': self._analyze_table_access(parsed_info)
        }
        
    def _analyze_performance(self, parsed_info: Dict) -> Dict:
        """Query performance metrikleri hesaplar."""
        return {
            'estimated_rows': self._estimate_row_count(parsed_info),
            'memory_usage': self._estimate_memory_usage(parsed_info),
            'cpu_cost': self._estimate_cpu_cost(parsed_info),
            'io_cost': self._estimate_io_cost(parsed_info)
        }