from typing import Dict, List
import re
from datetime import datetime
from .models import QueryPolicy
from .context_evaluator import ContextEvaluator

class QueryPolicyEngine:
    def __init__(self):
        self.context_evaluator = ContextEvaluator()
        
    async def evaluate_policies(self, query: str,
                              context: Dict) -> Dict:
        """Query policy'lerini değerlendirir."""
        # Get applicable policies
        policies = await self._get_applicable_policies(query)
        
        # Evaluate each policy
        evaluations = []
        for policy in policies:
            result = await self._evaluate_policy(
                policy, query, context
            )
            evaluations.append(result)
            
        # Combine results
        allowed = all(e['allowed'] for e in evaluations)
        
        return {
            'allowed': allowed,
            'evaluations': evaluations,
            'applied_policies': len(evaluations),
            'timestamp': datetime.utcnow()
        }
        
    async def _evaluate_policy(self, policy: QueryPolicy,
                             query: str, context: Dict) -> Dict:
        """Tek bir policy'yi değerlendirir."""
        evaluation = {
            'policy_id': policy.id,
            'name': policy.name,
            'allowed': True,
            'violations': []
        }
        
        # Pattern matching
        if not self._match_patterns(query, policy.patterns):
            evaluation['allowed'] = False
            evaluation['violations'].append('pattern_mismatch')
            
        # Resource limits
        if not await self._check_resource_limits(query, policy.limits):
            evaluation['allowed'] = False
            evaluation['violations'].append('resource_limit_exceeded')
            
        # Time restrictions
        if not await self._check_time_restrictions(context, policy.restrictions):
            evaluation['allowed'] = False
            evaluation['violations'].append('time_restriction_violation')
            
        return evaluation
        
    def _match_patterns(self, query: str, patterns: List[str]) -> bool:
        """Query pattern matching."""
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False