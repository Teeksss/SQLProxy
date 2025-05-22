from typing import Dict, List
import yaml
from pathlib import Path
import re

class QueryRulesEngine:
    def __init__(self):
        self.rules = self._load_rules()
        
    def evaluate_query(self, query: str, 
                      context: Dict) -> Dict:
        """Query'yi kurallara göre değerlendirir."""
        results = {
            'violations': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Syntax rules
        syntax_violations = self._check_syntax_rules(query)
        results['violations'].extend(syntax_violations)
        
        # Security rules
        security_issues = self._check_security_rules(query, context)
        results['violations'].extend(security_issues)
        
        # Best practice rules
        practice_warnings = self._check_best_practices(query)
        results['warnings'].extend(practice_warnings)
        
        # Performance rules
        perf_suggestions = self._check_performance_rules(query)
        results['suggestions'].extend(perf_suggestions)
        
        return results
        
    def _load_rules(self) -> Dict:
        """Rule tanımlarını yükler."""
        rules_path = Path('config/query_rules.yml')
        with open(rules_path) as f:
            return yaml.safe_load(f)
            
    def _check_syntax_rules(self, query: str) -> List[Dict]:
        """Syntax kurallarını kontrol eder."""
        violations = []
        
        for rule in self.rules['syntax']:
            pattern = re.compile(rule['pattern'])
            if pattern.search(query):
                violations.append({
                    'type': 'syntax',
                    'rule': rule['name'],
                    'description': rule['description'],
                    'severity': rule['severity']
                })
                
        return violations
        
    def _check_security_rules(self, query: str, 
                            context: Dict) -> List[Dict]:
        """Güvenlik kurallarını kontrol eder."""
        violations = []
        
        # SQL injection kontrolleri
        if self._has_sql_injection_risk(query):
            violations.append({
                'type': 'security',
                'rule': 'sql_injection',
                'description': 'Potential SQL injection risk detected',
                'severity': 'high'
            })
            
        # Permission kontrolleri
        if not self._check_permissions(query, context):
            violations.append({
                'type': 'security',
                'rule': 'insufficient_permissions',
                'description': 'User lacks required permissions',
                'severity': 'high'
            })
            
        return violations