from typing import List
import pytest
from xdist.workermanage import WorkerController

def pytest_configure_node(node: WorkerController) -> None:
    """Worker node konfigürasyonu"""
    node.slaveinput['worker_id'] = node.workerid
    
def pytest_xdist_make_scheduler(config, log):
    """Test scheduler konfigürasyonu"""
    from xdist.scheduler import LoadScheduling
    return LoadScheduling(config, log)

class ParallelTestConfig:
    @staticmethod
    def get_test_groups() -> List[str]:
        """Parallel test gruplarını döndürür"""
        return [
            'unit',
            'integration',
            'performance',
            'security'
        ]
        
    @staticmethod
    def worker_setup(worker_id: str) -> None:
        """Worker setup işlemleri"""
        import os
        os.environ['WORKER_ID'] = worker_id