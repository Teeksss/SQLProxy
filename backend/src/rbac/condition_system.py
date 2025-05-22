from typing import Dict, List, Any
import re
from datetime import datetime, time
from geopy.distance import geodesic
from .models import Condition, ConditionType

class ConditionSystem:
    def __init__(self):
        self.condition_handlers = {
            ConditionType.TIME: self._evaluate_time_condition,
            ConditionType.LOCATION: self._evaluate_location_condition,
            ConditionType.ENVIRONMENT: self._evaluate_environment_condition,
            ConditionType.RESOURCE: self._evaluate_resource_condition,
            ConditionType.USER_ATTRIBUTE: self._evaluate_user_attribute_condition,
            ConditionType.CUSTOM: self._evaluate_custom_condition
        }
        
    async def evaluate_condition(self, condition: Condition,
                               context: Dict) -> Dict:
        """Condition değerlendirmesi yapar."""
        handler = self.condition_handlers.get(condition.type)
        if not handler:
            raise ValueError(f"Unknown condition type: {condition.type}")
            
        result = await handler(condition, context)
        
        return {
            'condition_id': condition.id,
            'type': condition.type,
            'met': result['met'],
            'details': result['details']
        }
        
    async def _evaluate_time_condition(self, condition: Condition,
                                    context: Dict) -> Dict:
        """Zaman bazlı koşul değerlendirmesi."""
        current_time = context['timestamp']
        
        # Time window check
        if 'time_window' in condition.parameters:
            window = condition.parameters['time_window']
            start_time = time.fromisoformat(window['start'])
            end_time = time.fromisoformat(window['end'])
            
            current_time_of_day = current_time.time()
            in_window = (
                start_time <= current_time_of_day <= end_time
                if start_time <= end_time
                else (
                    start_time <= current_time_of_day or
                    current_time_of_day <= end_time
                )
            )
            
            if not in_window:
                return {
                    'met': False,
                    'details': 'Outside allowed time window'
                }
                
        # Day of week check
        if 'allowed_days' in condition.parameters:
            if current_time.strftime('%A') not in condition.parameters['allowed_days']:
                return {
                    'met': False,
                    'details': 'Not allowed on this day'
                }
                
        return {'met': True, 'details': 'Time conditions met'}
        
    async def _evaluate_location_condition(self, condition: Condition,
                                        context: Dict) -> Dict:
        """Lokasyon bazlı koşul değerlendirmesi."""
        user_location = context['location']
        
        # Geo-fence check
        if 'geo_fence' in condition.parameters:
            fence = condition.parameters['geo_fence']
            user_coords = (user_location['latitude'],
                         user_location['longitude'])
            
            for allowed_area in fence['allowed_areas']:
                center = (allowed_area['lat'], allowed_area['lng'])
                radius = allowed_area['radius']  # meters
                
                if geodesic(user_coords, center).meters <= radius:
                    return {'met': True, 'details': 'Within allowed area'}
                    
            return {
                'met': False,
                'details': 'Outside allowed areas'
            }
            
        return {'met': True, 'details': 'Location conditions met'}