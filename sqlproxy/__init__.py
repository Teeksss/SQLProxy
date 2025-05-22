"""
SQLProxy - SQL Query Proxy Service
--------------------------------

High performance SQL proxy service with security, monitoring and caching features.

:copyright: (c) 2025 by Teeksss
:license: MIT
"""

__version__ = '0.1.0'
__author__ = 'Teeksss'

from sqlproxy.core import Database, QueryExecutor, RedisClient
from sqlproxy.performance import BenchmarkRunner, PerformanceAnalyzer, Profiler
from sqlproxy.security import SQLInjectionChecker

__all__ = [
    'Database',
    'QueryExecutor',
    'RedisClient',
    'BenchmarkRunner',
    'PerformanceAnalyzer',
    'Profiler',
    'SQLInjectionChecker'
]