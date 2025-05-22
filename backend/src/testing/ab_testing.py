from typing import Dict, List
import numpy as np
from scipy import stats
from datetime import datetime
from .models import ABTest, TestResult, Variant

class ABTestingManager:
    def __init__(self):
        self.active_tests: Dict[str, ABTest] = {}
        self.results: Dict[str, TestResult] = {}
        
    async def create_test(self, config: Dict) -> str:
        """A/B test oluşturur."""
        try:
            # Generate test ID
            test_id = self._generate_test_id()
            
            # Create test
            test = ABTest(
                id=test_id,
                variants=self._create_variants(config),
                config=config,
                start_time=datetime.utcnow()
            )
            
            # Save test
            self.active_tests[test_id] = test
            
            return test_id
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def record_event(self, test_id: str,
                          variant_id: str,
                          event: Dict) -> None:
        """Test eventi kaydeder."""
        if test_id not in self.active_tests:
            raise ValueError(f"Unknown test: {test_id}")
            
        test = self.active_tests[test_id]
        await test.record_event(variant_id, event)
        
    async def analyze_results(self, test_id: str) -> Dict:
        """Test sonuçlarını analiz eder."""
        test = self.active_tests.get(test_id)
        if not test:
            raise ValueError(f"Unknown test: {test_id}")
            
        try:
            # Calculate statistics
            stats = await self._calculate_statistics(test)
            
            # Perform significance testing
            significance = await self._test_significance(
                test, stats
            )
            
            # Generate insights
            insights = await self._generate_insights(
                test, stats, significance
            )
            
            result = TestResult(
                test_id=test_id,
                statistics=stats,
                significance=significance,
                insights=insights,
                completed_at=datetime.utcnow()
            )
            
            self.results[test_id] = result
            
            return {
                'status': 'success',
                'result': result.dict()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }