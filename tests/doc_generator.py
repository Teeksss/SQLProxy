from typing import Dict, List
import inspect
import pytest
from pathlib import Path
from jinja2 import Template

class TestDocGenerator:
    def __init__(self, output_dir: str = "docs/tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_test_docs(self) -> None:
        """Test dokümantasyonu oluşturur"""
        test_docs = self._collect_test_docs()
        self._write_docs(test_docs)
        
    def _collect_test_docs(self) -> Dict[str, List[Dict]]:
        """Test dokümantasyonunu toplar"""
        docs = {}
        
        for item in pytest.collect_file():
            if item.name.startswith('test_'):
                module = inspect.getmodule(item.module)
                docs[item.name] = []
                
                for name, obj in inspect.getmembers(module):
                    if name.startswith('test_'):
                        docs[item.name].append({
                            'name': name,
                            'doc': inspect.getdoc(obj),
                            'markers': self._get_markers(obj)
                        })
                        
        return docs
        
    def _get_markers(self, obj) -> List[str]:
        """Test markerlarını alır"""
        return [
            marker.name
            for marker in getattr(obj, 'pytestmark', [])
        ]
        
    def _write_docs(self, docs: Dict[str, List[Dict]]) -> None:
        """Dokümantasyonu yazar"""
        template = Template("""
# Test Documentation

{% for file, tests in docs.items() %}
## {{ file }}

{% for test in tests %}
### {{ test.name }}

{{ test.doc }}

**Markers:** {{ test.markers|join(', ') }}

{% endfor %}
{% endfor %}
        """)
        
        output = template.render(docs=docs)
        with open(self.output_dir / "test_documentation.md", 'w') as f:
            f.write(output)