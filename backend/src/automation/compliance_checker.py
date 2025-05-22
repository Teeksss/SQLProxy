from typing import Dict, List
from datetime import datetime
from .models import ComplianceRule, ComplianceCheck
from .policy_validator import PolicyValidator

class ComplianceChecker:
    def __init__(self):
        self.policy_validator = PolicyValidator()
        
    async def check_compliance(self) -> Dict:
        """Compliance kontrolü yapar."""
        # Get compliance rules
        rules = await self._get_compliance_rules()
        
        # Run checks
        results = []
        for rule in rules:
            result = await self._check_rule(rule)
            results.append(result)
            
        # Generate report
        report = await self._generate_report(results)
        
        # Auto-remediation
        if report['violations']:
            await self._auto_remediate(report['violations'])
            
        return report
        
    async def _check_rule(self, rule: ComplianceRule) -> Dict:
        """Tek bir compliance rule'u kontrol eder."""
        try:
            # Get current state
            current_state = await self._get_current_state(
                rule.resource_type
            )
            
            # Validate against rule
            validation = await self.policy_validator.validate(
                current_state, rule.policy
            )
            
            # Check for violations
            violations = self._find_violations(
                validation, rule
            )
            
            return {
                'rule_id': rule.id,
                'status': 'compliant' if not violations else 'violation',
                'violations': violations,
                'checked_at': datetime.utcnow()
            }
            
        except Exception as e:
            return {
                'rule_id': rule.id,
                'status': 'error',
                'error': str(e),
                'checked_at': datetime.utcnow()
            }
            
    async def _auto_remediate(self, violations: List[Dict]) -> None:
        """Tespit edilen ihlalleri otomatik düzeltir."""
        for violation in violations:
            try:
                # Get remediation plan
                plan = await self._create_remediation_plan(
                    violation
                )
                
                # Execute remediation
                if plan['auto_remediable']:
                    await self._execute_remediation(plan)
                    
                # Log remediation
                await self._log_remediation(
                    violation, plan
                )
                
            except Exception as e:
                self.logger.error(
                    f"Auto-remediation failed: {str(e)}"
                )