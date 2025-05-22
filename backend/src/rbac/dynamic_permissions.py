from typing import Dict, List, Any
from datetime import datetime, time
import asyncio
from dataclasses import dataclass
from .context_evaluator import ContextEvaluator
from .condition_matcher import ConditionMatcher

@dataclass
class DynamicContext:
    user_id: str
    timestamp: datetime
    location: Dict
    environment: Dict
    request_metadata: Dict
    session_data: Dict

class DynamicPermissionEngine:
    def __init__(self):
        self.context_evaluator = ContextEvaluator()
        self.condition_matcher = ConditionMatcher()
        
    async def evaluate_permissions(self, 
                                 user_permissions: List[Dict],
                                 context: DynamicContext) -> Dict:
        """Dinamik permission değerlendirmesi yapar."""
        try:
            # Context enrichment
            enriched_context = await self._enrich_context(context)
            
            # Permission evaluation
            evaluations = []
            for permission in user_permissions:
                result = await self._evaluate_permission(
                    permission, enriched_context
                )
                evaluations.append(result)
                
            # Final decision
            allowed = self._make_final_decision(evaluations)
            
            return {
                'allowed': allowed,
                'evaluations': evaluations,
                'context': enriched_context,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Permission evaluation error: {str(e)}")
            return {'allowed': False, 'error': str(e)}
            
    async def _evaluate_permission(self, permission: Dict,
                                context: DynamicContext) -> Dict:
        """Tek bir permission'ı değerlendirir."""
        evaluation = {
            'permission_id': permission['id'],
            'conditions_met': [],
            'conditions_failed': []
        }
        
        # Time-based conditions
        if time_result := await self._evaluate_time_conditions(
            permission, context
        ):
            if time_result['met']:
                evaluation['conditions_met'].append(time_result)
            else:
                evaluation['conditions_failed'].append(time_result)
                
        # Location-based conditions
        if loc_result := await self._evaluate_location_conditions(
            permission, context
        ):
            if loc_result['met']:
                evaluation['conditions_met'].append(loc_result)
            else:
                evaluation['conditions_failed'].append(loc_result)
                
        # Environment conditions
        if env_result := await self._evaluate_environment_conditions(
            permission, context
        ):
            if env_result['met']:
                evaluation['conditions_met'].append(env_result)
            else:
                evaluation['conditions_failed'].append(env_result)
                
        # Custom conditions
        if custom_results := await self._evaluate_custom_conditions(
            permission, context
        ):
            for result in custom_results:
                if result['met']:
                    evaluation['conditions_met'].append(result)
                else:
                    evaluation['conditions_failed'].append(result)
                    
        evaluation['allowed'] = len(evaluation['conditions_failed']) == 0
        
        return evaluation