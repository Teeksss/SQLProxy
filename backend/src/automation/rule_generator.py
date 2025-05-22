from typing import Dict, List
import pandas as pd
from sklearn.cluster import DBSCAN
from .models import AutomationRule
from .pattern_analyzer import PatternAnalyzer

class RuleGenerator:
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.min_confidence = 0.8
        
    async def generate_rules(self, historical_data: Dict) -> List[Dict]:
        """Usage pattern'lerine göre rule üretir."""
        # Pattern analysis
        patterns = await self.pattern_analyzer.analyze_patterns(
            historical_data
        )
        
        # Generate rules from patterns
        rules = await self._generate_rules_from_patterns(patterns)
        
        # Validate and refine rules
        validated_rules = await self._validate_rules(rules)
        
        # Optimize rule set
        optimized_rules = await self._optimize_rules(validated_rules)
        
        return {
            'rules': optimized_rules,
            'metadata': {
                'confidence': self._calculate_confidence(optimized_rules),
                'coverage': self._calculate_coverage(optimized_rules),
                'generated_at': datetime.utcnow()
            }
        }
        
    async def _generate_rules_from_patterns(self,
                                          patterns: List[Dict]) -> List[Dict]:
        """Pattern'lerden rule'lar üretir."""
        rules = []
        
        for pattern in patterns:
            if pattern['confidence'] >= self.min_confidence:
                # Create base rule
                rule = await self._create_base_rule(pattern)
                
                # Add conditions
                conditions = await self._generate_conditions(
                    pattern
                )
                rule['conditions'] = conditions
                
                # Add actions
                actions = await self._generate_actions(
                    pattern
                )
                rule['actions'] = actions
                
                rules.append(rule)
                
        return rules
        
    async def _optimize_rules(self, rules: List[Dict]) -> List[Dict]:
        """Rule set'i optimize eder."""
        # Remove duplicates
        unique_rules = self._remove_duplicate_rules(rules)
        
        # Merge similar rules
        merged_rules = self._merge_similar_rules(unique_rules)
        
        # Sort by priority
        sorted_rules = sorted(
            merged_rules,
            key=lambda x: x['priority'],
            reverse=True
        )
        
        return sorted_rules