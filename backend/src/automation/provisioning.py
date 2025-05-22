from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from .models import ProvisioningRule, ResourceTemplate
from .template_engine import TemplateEngine

class AutoProvisioner:
    def __init__(self):
        self.template_engine = TemplateEngine()
        
    async def auto_provision(self, trigger_data: Dict) -> Dict:
        """Otomatik provisioning yapar."""
        try:
            # Get applicable rules
            rules = await self._get_applicable_rules(trigger_data)
            
            # Process rules
            results = []
            for rule in rules:
                result = await self._process_rule(rule, trigger_data)
                results.append(result)
                
            # Apply templates
            provisioned = await self._apply_templates(results)
            
            # Validate results
            await self._validate_provisioning(provisioned)
            
            return {
                'status': 'success',
                'provisioned_resources': provisioned,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow()
            }
            
    async def _process_rule(self, rule: ProvisioningRule,
                          data: Dict) -> Dict:
        """Rule'u işler ve gerekli kaynakları oluşturur."""
        resources = []
        
        # Resource templates
        for template in rule.resource_templates:
            # Template parametrelerini hazırla
            params = self._prepare_template_params(
                template, data
            )
            
            # Template'i işle
            resource = await self.template_engine.process_template(
                template, params
            )
            
            # Resource validasyonu
            if await self._validate_resource(resource):
                resources.append(resource)
                
        return {
            'rule_id': rule.id,
            'resources': resources,
            'metadata': {
                'trigger': data,
                'timestamp': datetime.utcnow()
            }
        }
        
    async def _validate_resource(self, resource: Dict) -> bool:
        """Resource validasyonu yapar."""
        validations = []
        
        # Schema validation
        validations.append(
            await self._validate_schema(resource)
        )
        
        # Dependency check
        validations.append(
            await self._check_dependencies(resource)
        )
        
        # Quota check
        validations.append(
            await self._check_quotas(resource)
        )
        
        return all(validations)