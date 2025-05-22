from typing import Dict, Any
import json
import os
from datetime import datetime
from pathlib import Path

class TestDataManager:
    def __init__(self, base_path: str = "tests/data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def save_fixture(self, name: str, data: Dict[str, Any]) -> None:
        """Test fixture'ını kaydeder"""
        file_path = self.base_path / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_fixture(self, name: str) -> Dict[str, Any]:
        """Test fixture'ını yükler"""
        file_path = self.base_path / f"{name}.json"
        with open(file_path, 'r') as f:
            return json.load(f)
            
    def create_test_data(self, category: str, size: int = 100) -> Dict[str, Any]:
        """Test verisi oluşturur"""
        if category == "users":
            data = [
                {
                    "id": i,
                    "username": f"user_{i}",
                    "email": f"user_{i}@example.com",
                    "created_at": datetime.utcnow().isoformat()
                }
                for i in range(size)
            ]
        elif category == "queries":
            data = [
                {
                    "id": i,
                    "query": f"SELECT * FROM table_{i}",
                    "params": {"param1": i},
                    "timestamp": datetime.utcnow().isoformat()
                }
                for i in range(size)
            ]
        else:
            raise ValueError(f"Unknown category: {category}")
            
        return {"data": data, "metadata": {"size": size, "category": category}}