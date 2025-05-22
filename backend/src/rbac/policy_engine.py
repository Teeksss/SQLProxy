from typing import Dict, List
import json
from datetime import datetime
from .models import Policy, PolicyEffect

class PolicyEngine:
    def __init__(self):
        self.cache_ttl = 300  # seconds
        self.policy_cache = {}
        
    async def evaluate_policies(self, context: Dict) -> Dict:
        """Policy değerlendirmesi yapar."""
        # Get applicable policies
        policies = await self._get_applicable_policies(context)
        
        # Evaluate each policy
        results = []
        for policy in policies:
            evaluation = await self._evaluate_policy(
                policy, context
            )
            results.append(evaluation)
            
        # Combine results
        final_effect = self._determine_final_effect(results)
        
        return {
            'allowed': final_effect == PolicyEffect.ALLOW,
            'reason': self._get_denial_reason(results),
            'applied_policies': [r['policy_id'] for r in results]
        }
        
    async def _evaluate_policy(self, policy: Policy,
                             context: Dict) -> Dict:
        """Tek bir policy değerlendirir."""
        try:
            # Check conditions
            conditions_met = all(
                self._evaluate_condition(c, context)
                for c in policy.conditions
            )
            
            # Check resource match
            resource_match = self._match_resource(
                policy.resource,
                context['resource']
            )
            
            # Check action match
            action_match = self._match_action(
                policy.action,
                context['action']
            )
            
            return {
                'policy_id': policy.id,
                'effect': policy.effect if (
                    conditions_met and 
                    resource_match and 
                    action_match
                ) else PolicyEffect.DENY,
                'reason': self._get_evaluation_reason(
                    conditions_met,
                    resource_match,
                    action_match
                )
            }
            
        except Exception as e:
            self.logger.error(f"Policy evaluation error: {str(e)}")
            return {
                'policy_id': policy.id,
                'effect': PolicyEffect.DENY,
                'reason': 'Evaluation error'
            }