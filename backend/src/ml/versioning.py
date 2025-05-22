from typing import Dict, List
import git
import json
from datetime import datetime
from .models import ModelVersion, ModelMetadata
from .storage import ModelStorage

class ModelVersionManager:
    def __init__(self):
        self.storage = ModelStorage()
        self.repo = git.Repo('.')
        
    async def save_version(self, model_name: str,
                          artifacts: Dict,
                          metadata: ModelMetadata) -> str:
        """Model versiyonu kaydeder."""
        try:
            # Generate version ID
            version_id = self._generate_version_id(model_name)
            
            # Save artifacts
            artifact_paths = await self._save_artifacts(
                version_id, artifacts
            )
            
            # Create version record
            version = ModelVersion(
                id=version_id,
                model_name=model_name,
                artifacts=artifact_paths,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            
            # Save to storage
            await self.storage.save_version(version)
            
            # Commit to version control
            await self._commit_version(version)
            
            return version_id
            
        except Exception as e:
            await self._cleanup_failed_save(version_id)
            raise
            
    async def get_version(self, version_id: str) -> ModelVersion:
        """Model versiyonu getirir."""
        return await self.storage.get_version(version_id)
        
    async def compare_versions(self, version_1: str,
                             version_2: str) -> Dict:
        """Model versiyonlarını karşılaştırır."""
        v1 = await self.get_version(version_1)
        v2 = await self.get_version(version_2)
        
        return {
            'metric_differences': self._compare_metrics(
                v1.metadata.metrics,
                v2.metadata.metrics
            ),
            'config_differences': self._compare_configs(
                v1.metadata.config,
                v2.metadata.config
            ),
            'performance_comparison': await self._compare_performance(
                v1, v2
            )
        }