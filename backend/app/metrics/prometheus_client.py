"""
Prometheus Metrics Client for SQL Proxy

This module provides a Prometheus metrics client for SQL Proxy,
enabling integration with Prometheus monitoring systems.

Last updated: 2025-05-20 11:18:07
Updated by: Teeksss
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
import io
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    """Types of Prometheus metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class PrometheusClient:
    """
    Prometheus metrics client
    
    Provides Prometheus metrics integration for SQL Proxy.
    """
    
    def __init__(self):
        """Initialize the Prometheus client"""
        self.enabled = settings.PROMETHEUS_ENABLED
        self.prefix = settings.PROMETHEUS_METRIC_PREFIX
        
        # Storage for metrics
        self.counters = {}      # name -> value
        self.gauges = {}        # name -> value
        self.histograms = {}    # name -> {bucket1: count1, bucket2: count2, ...}
        self.summaries = {}     # name -> {quantile1: value1, quantile2: value2, ...}
        
        # Metric metadata
        self.metric_metadata = {}  # name -> {help, type, labels}
        
        # Default buckets for histograms
        self.default_buckets = [
            1, 5, 10, 25, 50, 75, 100, 250, 500, 
            750, 1000, 2500, 5000, 7500, 10000
        ]
        
        # Default quantiles for summaries
        self.default_quantiles = [0.5, 0.9, 0.95, 0.99]
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Register default metrics
        self._register_default_metrics()
        
        logger.info("Prometheus client initialized")
    
    def _register_default_metrics(self):
        """Register default metrics"""
        # System metrics
        self.register_metric(
            name="process_start_time_seconds",
            metric_type=MetricType.GAUGE,
            help="Start time of the process since unix epoch in seconds",
            labels={}
        )
        self.set_gauge("process_start_time_seconds", time.time())
        
        # HTTP metrics
        self.register_metric(
            name="http_requests_total",
            metric_type=MetricType.COUNTER,
            help="Total number of HTTP requests",
            labels={"method", "path", "status"}
        )
        
        self.register_metric(
            name="http_request_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            help="HTTP request duration in seconds",
            labels={"method", "path"},
            buckets=self.default_buckets
        )
        
        # SQL query metrics
        self.register_metric(
            name="sql_queries_total",
            metric_type=MetricType.COUNTER,
            help="Total number of SQL queries",
            labels={"server_alias", "success"}
        )
        
        self.register_metric(
            name="sql_query_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            help="SQL query duration in seconds",
            labels={"server_alias"},
            buckets=self.default_buckets
        )
    
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        help: str,
        labels: Optional[set] = None,
        buckets: Optional[List[float]] = None,
        quantiles: Optional[List[float]] = None
    ) -> None:
        """
        Register a new metric
        
        Args:
            name: Metric name
            metric_type: Metric type
            help: Help text for the metric
            labels: Set of label names
            buckets: Buckets for histogram metrics
            quantiles: Quantiles for summary metrics
        """
        if not self.enabled:
            return
        
        # Prefix metric name
        prefixed_name = f"{self.prefix}_{name}" if self.prefix else name
        
        with self.lock:
            # Register metric metadata
            self.metric_metadata[prefixed_name] = {
                "help": help,
                "type": metric_type,
                "labels": labels or set(),
                "buckets": buckets or self.default_buckets,
                "quantiles": quantiles or self.default_quantiles
            }
            
            # Initialize metric storage based on type
            if metric_type == MetricType.COUNTER:
                self.counters[prefixed_name] = {}
            elif metric_type == MetricType.GAUGE:
                self.gauges[prefixed_name] = {}
            elif metric_type == MetricType.HISTOGRAM:
                self.histograms[prefixed_name] = {}
            elif metric_type == MetricType.SUMMARY:
                self.summaries[prefixed_name] = {}
    
    def increment(
        self, 
        name: str, 
        value: float = 1.0, 
        labels: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.COUNTER
    ) -> None:
        """
        Increment a counter
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Labels for the metric
            metric_type: Metric type (for compatibility with observe())
        """
        if not self.enabled:
            return
        
        # Prefix metric name
        prefixed_name = f"{self.prefix}_{name}" if self.prefix else name
        
        with self.lock:
            # Skip if metric not registered
            if prefixed_name not in self.metric_metadata:
                logger.warning(f"Metric not registered: {prefixed_name}")
                return
            
            # Check metric type
            metadata = self.metric_metadata[prefixed_name]
            if metadata["type"] != MetricType.COUNTER:
                logger.warning(f"Cannot increment non-counter metric: {prefixed_name}")
                return
            
            # Get counter storage
            if prefixed_name not in self.counters:
                self.counters[prefixed_name] = {}
            
            # Convert labels to string for dict key
            label_key = self._labels_to_key(labels or {})
            
            # Increment counter
            if label_key in self.counters[prefixed_name]:
                self.counters[prefixed_name][label_key] += value
            else:
                self.counters[prefixed_name][label_key] = value
    
    def set_gauge(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge value
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Labels for the metric
        """
        if not self.enabled:
            return
        
        # Prefix metric name
        prefixed_name = f"{self.prefix}_{name}" if self.prefix else name
        
        with self.lock:
            # Skip if metric not registered
            if prefixed_name not in self.metric_metadata:
                logger.warning(f"Metric not registered: {prefixed_name}")
                return
            
            # Check metric type
            metadata = self.metric_metadata[prefixed_name]
            if metadata["type"] != MetricType.GAUGE:
                logger.warning(f"Cannot set non-gauge metric: {prefixed_name}")
                return
            
            # Get gauge storage
            if prefixed_name not in self.gauges:
                self.gauges[prefixed_name] = {}
            
            # Convert labels to string for dict key
            label_key = self._labels_to_key(labels or {})
            
            # Set gauge value
            self.gauges[prefixed_name][label_key] = value
    
    def observe(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.HISTOGRAM
    ) -> None:
        """
        Observe a value (for histogram or summary)
        
        Args:
            name: Metric name
            value: Observed value
            labels: Labels for the metric
            metric_type: Metric type (histogram or summary)
        """
        if not self.enabled:
            return
        
        # Prefix metric name
        prefixed_name = f"{self.prefix}_{name}" if self.prefix else name
        
        with self.lock:
            # Skip if metric not registered
            if prefixed_name not in self.metric_metadata:
                logger.warning(f"Metric not registered: {prefixed_name}")
                return
            
            # Check metric type
            metadata = self.metric_metadata[prefixed_name]
            if metric_type == MetricType.HISTOGRAM and metadata["type"] != MetricType.HISTOGRAM:
                logger.warning(f"Cannot observe non-histogram metric: {prefixed_name}")
                return
            elif metric_type == MetricType.SUMMARY and metadata["type"] != MetricType.SUMMARY:
                logger.warning(f"Cannot observe non-summary metric: {prefixed_name}")
                return
            
            # Convert labels to string for dict key
            label_key = self._labels_to_key(labels or {})
            
            # Process histogram
            if metadata["type"] == MetricType.HISTOGRAM:
                # Get histogram storage
                if prefixed_name not in self.histograms:
                    self.histograms[prefixed_name] = {}
                
                # Initialize bucket counters if needed
                if label_key not in self.histograms[prefixed_name]:
                    buckets = metadata["buckets"]
                    self.histograms[prefixed_name][label_key] = {
                        "buckets": {bucket: 0 for bucket in buckets},
                        "sum": 0,
                        "count": 0
                    }
                
                # Update bucket counters
                histogram = self.histograms[prefixed_name][label_key]
                for bucket in histogram["buckets"]:
                    if value <= bucket:
                        histogram["buckets"][bucket] += 1
                
                # Update sum and count
                histogram["sum"] += value
                histogram["count"] += 1
            
            # Process summary
            elif metadata["type"] == MetricType.SUMMARY:
                # Get summary storage
                if prefixed_name not in self.summaries:
                    self.summaries[prefixed_name] = {}
                
                # Initialize summary if needed
                if label_key not in self.summaries[prefixed_name]:
                    # Simple summary implementation (not accurate for high volume)
                    # For production, use reservoir sampling or t-digest
                    self.summaries[prefixed_name][label_key] = {
                        "values": [],
                        "sum": 0,
                        "count": 0
                    }
                
                # Update summary
                summary = self.summaries[prefixed_name][label_key]
                summary["values"].append(value)
                summary["sum"] += value
                summary["count"] += 1
                
                # Limit stored values to avoid memory issues
                if len(summary["values"]) > 1000:
                    # Simple approach: keep newest values
                    summary["values"] = summary["values"][-1000:]
    
    def get_metrics(self) -> str:
        """
        Get metrics in Prometheus format
        
        Returns:
            Metrics in Prometheus exposition format
        """
        if not self.enabled:
            return ""
        
        with self.lock:
            output = io.StringIO()
            
            # Process counters
            for name, counter in self.counters.items():
                metadata = self.metric_metadata[name]
                
                # Write metric header
                output.write(f"# HELP {name} {metadata['help']}\n")
                output.write(f"# TYPE {name} counter\n")
                
                # Write metric values
                for label_key, value in counter.items():
                    labels_str = self._key_to_labels_string(label_key)
                    output.write(f"{name}{labels_str} {value}\n")
                
                output.write("\n")
            
            # Process gauges
            for name, gauge in self.gauges.items():
                metadata = self.metric_metadata[name]
                
                # Write metric header
                output.write(f"# HELP {name} {metadata['help']}\n")
                output.write(f"# TYPE {name} gauge\n")
                
                # Write metric values
                for label_key, value in gauge.items():
                    labels_str = self._key_to_labels_string(label_key)
                    output.write(f"{name}{labels_str} {value}\n")
                
                output.write("\n")
            
            # Process histograms
            for name, histogram in self.histograms.items():
                metadata = self.metric_metadata[name]
                
                # Write metric header
                output.write(f"# HELP {name} {metadata['help']}\n")
                output.write(f"# TYPE {name} histogram\n")
                
                # Write metric values for each label set
                for label_key, data in histogram.items():
                    labels_str = self._key_to_labels_string(label_key)
                    
                    # Write bucket values
                    for bucket, count in data["buckets"].items():
                        bucket_labels = f"{labels_str[:-1]},le=\"{bucket}\"{labels_str[-1]}"
                        output.write(f"{name}_bucket{bucket_labels} {count}\n")
                    
                    # Write sum and count
                    output.write(f"{name}_sum{labels_str} {data['sum']}\n")
                    output.write(f"{name}_count{labels_str} {data['count']}\n")
                
                output.write("\n")
            
            # Process summaries
            for name, summary in self.summaries.items():
                metadata = self.metric_metadata[name]
                
                # Write metric header
                output.write(f"# HELP {name} {metadata['help']}\n")
                output.write(f"# TYPE {name} summary\n")
                
                # Write metric values for each label set
                for label_key, data in summary.items():
                    labels_str = self._key_to_labels_string(label_key)
                    
                    # Calculate quantiles
                    if data["values"]:
                        sorted_values = sorted(data["values"])
                        for quantile in metadata["quantiles"]:
                            idx = int(quantile * len(sorted_values))
                            if idx >= len(sorted_values):
                                idx = len(sorted_values) - 1
                            
                            value = sorted_values[idx]
                            quantile_labels = f"{labels_str[:-1]},quantile=\"{quantile}\"{labels_str[-1]}"
                            output.write(f"{name}{quantile_labels} {value}\n")
                    
                    # Write sum and count
                    output.write(f"{name}_sum{labels_str} {data['sum']}\n")
                    output.write(f"{name}_count{labels_str} {data['count']}\n")
                
                output.write("\n")
            
            return output.getvalue()
    
    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """
        Convert labels dictionary to a string key
        
        Args:
            labels: Labels dictionary
            
        Returns:
            String key for the labels
        """
        if not labels:
            return ""
        
        # Sort labels by name
        sorted_labels = sorted(labels.items())
        
        # Create key string
        return ",".join(f"{name}={value}" for name, value in sorted_labels)
    
    def _key_to_labels_string(self, key: str) -> str:
        """
        Convert labels key to Prometheus format
        
        Args:
            key: Labels key
            
        Returns:
            Labels in Prometheus format
        """
        if not key:
            return ""
        
        # Split key into labels
        labels = key.split(",")
        
        # Create Prometheus labels string
        return "{" + ",".join(labels) + "}"

# Son güncelleme: 2025-05-20 11:18:07
# Güncelleyen: Teeksss