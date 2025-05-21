"""
Kubernetes Integration for SQL Proxy

This module provides integration with Kubernetes for container 
orchestration, enabling automated deployment, scaling, and management
of SQL Proxy components.

Last updated: 2025-05-20 10:49:41
Updated by: Teeksss
"""

import logging
import yaml
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from kubernetes import client, config, watch
import os
from datetime import datetime, timedelta
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

class KubernetesClient:
    """
    Kubernetes client for SQL Proxy orchestration
    
    Provides methods to interact with Kubernetes API for deployment management,
    scaling, monitoring, and configuration.
    """
    
    def __init__(self):
        """Initialize the Kubernetes client"""
        self.configured = False
        self.namespace = settings.K8S_NAMESPACE
        self.app_label = settings.K8S_APP_LABEL
        self.component_map = {
            "api": settings.K8S_API_NAME,
            "worker": settings.K8S_WORKER_NAME,
            "db": settings.K8S_DB_NAME,
            "redis": settings.K8S_REDIS_NAME,
            "webui": settings.K8S_WEBUI_NAME
        }
        
        # API clients
        self.core_v1 = None
        self.apps_v1 = None
        self.autoscaling_v1 = None
        self.batch_v1 = None
        
        # Cache for Kubernetes resources
        self.resource_cache = {}
        self.cache_lock = threading.RLock()
        self.cache_last_updated = {}
        self.cache_ttl = 60  # Cache TTL in seconds
        
        # Initialize client if configuration exists
        self._configure_client()
        
        logger.info("Kubernetes client initialized")
    
    def _configure_client(self):
        """Configure the Kubernetes client"""
        try:
            # Check for in-cluster configuration
            if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
                config.load_incluster_config()
                logger.info("Using in-cluster Kubernetes configuration")
            else:
                # Use kubeconfig file
                config.load_kube_config()
                logger.info("Using kubeconfig for Kubernetes configuration")
            
            # Initialize API clients
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.autoscaling_v1 = client.AutoscalingV1Api()
            self.batch_v1 = client.BatchV1Api()
            
            self.configured = True
            
        except Exception as e:
            logger.error(f"Error configuring Kubernetes client: {str(e)}")
            self.configured = False
    
    def is_configured(self) -> bool:
        """
        Check if Kubernetes client is properly configured
        
        Returns:
            True if configured, False otherwise
        """
        if not self.configured:
            # Try to configure again if not already configured
            self._configure_client()
        
        return self.configured
    
    def get_deployment_status(self, component: str = None) -> Dict[str, Any]:
        """
        Get status of all deployments or a specific component
        
        Args:
            component: Optional component name (api, worker, db, redis, webui)
            
        Returns:
            Dictionary with deployment status
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        try:
            # Get deployments from cache or API
            deployments = self._get_cached_resource("deployments", self._fetch_deployments)
            
            # Filter by component if specified
            if component:
                if component not in self.component_map:
                    return {"error": f"Unknown component: {component}"}
                
                component_name = self.component_map[component]
                filtered_deployments = [d for d in deployments if d["name"] == component_name]
                
                if not filtered_deployments:
                    return {"error": f"Component not found: {component}"}
                
                return {
                    "component": component,
                    "deployments": filtered_deployments
                }
            
            # Group deployments by component
            component_status = {}
            for comp_key, comp_name in self.component_map.items():
                component_deployments = [d for d in deployments if d["name"] == comp_name]
                if component_deployments:
                    component_status[comp_key] = component_deployments
            
            return {
                "deployments": component_status
            }
            
        except Exception as e:
            logger.error(f"Error getting deployment status: {str(e)}")
            return {"error": str(e)}
    
    def get_pod_status(self, component: str = None) -> Dict[str, Any]:
        """
        Get status of all pods or pods for a specific component
        
        Args:
            component: Optional component name (api, worker, db, redis, webui)
            
        Returns:
            Dictionary with pod status
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        try:
            # Get pods from cache or API
            pods = self._get_cached_resource("pods", self._fetch_pods)
            
            # Filter by component if specified
            if component:
                if component not in self.component_map:
                    return {"error": f"Unknown component: {component}"}
                
                component_name = self.component_map[component]
                filtered_pods = [p for p in pods if component_name in p["name"]]
                
                return {
                    "component": component,
                    "pods": filtered_pods
                }
            
            # Group pods by component
            component_pods = {}
            for comp_key, comp_name in self.component_map.items():
                comp_pods = [p for p in pods if comp_name in p["name"]]
                if comp_pods:
                    component_pods[comp_key] = comp_pods
            
            return {
                "pods": component_pods
            }
            
        except Exception as e:
            logger.error(f"Error getting pod status: {str(e)}")
            return {"error": str(e)}
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of all services
        
        Returns:
            Dictionary with service status
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        try:
            # Get services from cache or API
            services = self._get_cached_resource("services", self._fetch_services)
            
            # Group services by component
            component_services = {}
            for comp_key, comp_name in self.component_map.items():
                comp_services = [s for s in services if comp_name in s["name"]]
                if comp_services:
                    component_services[comp_key] = comp_services
            
            return {
                "services": component_services
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {str(e)}")
            return {"error": str(e)}
    
    def scale_component(
        self, 
        component: str, 
        replicas: int
    ) -> Dict[str, Any]:
        """
        Scale a component to a specific number of replicas
        
        Args:
            component: Component name (api, worker)
            replicas: Number of replicas
            
        Returns:
            Dictionary with scaling result
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        if component not in ["api", "worker"]:
            return {"error": f"Cannot scale component: {component}. Only api and worker can be scaled."}
        
        try:
            component_name = self.component_map[component]
            
            # Get deployment
            try:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=component_name,
                    namespace=self.namespace
                )
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    return {"error": f"Deployment not found: {component_name}"}
                else:
                    raise
            
            # Update replica count
            deployment.spec.replicas = replicas
            
            # Apply update
            self.apps_v1.patch_namespaced_deployment(
                name=component_name,
                namespace=self.namespace,
                body=deployment
            )
            
            # Invalidate cache
            self._invalidate_cache("deployments")
            
            return {
                "component": component,
                "replicas": replicas,
                "status": "scaling"
            }
            
        except Exception as e:
            logger.error(f"Error scaling component {component}: {str(e)}")
            return {"error": str(e)}
    
    def restart_component(self, component: str) -> Dict[str, Any]:
        """
        Restart a component by rolling update
        
        Args:
            component: Component name (api, worker, webui)
            
        Returns:
            Dictionary with restart result
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        if component not in ["api", "worker", "webui"]:
            return {"error": f"Cannot restart component: {component}. Only api, worker, and webui can be restarted."}
        
        try:
            component_name = self.component_map[component]
            
            # Get deployment
            try:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=component_name,
                    namespace=self.namespace
                )
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    return {"error": f"Deployment not found: {component_name}"}
                else:
                    raise
            
            # Add restart annotation
            if deployment.spec.template.metadata.annotations is None:
                deployment.spec.template.metadata.annotations = {}
            
            deployment.spec.template.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = datetime.utcnow().isoformat()
            
            # Apply update
            self.apps_v1.patch_namespaced_deployment(
                name=component_name,
                namespace=self.namespace,
                body=deployment
            )
            
            # Invalidate cache
            self._invalidate_cache("deployments")
            self._invalidate_cache("pods")
            
            return {
                "component": component,
                "status": "restarting"
            }
            
        except Exception as e:
            logger.error(f"Error restarting component {component}: {str(e)}")
            return {"error": str(e)}
    
    def get_component_logs(
        self, 
        component: str,
        pod_name: Optional[str] = None,
        tail_lines: int = 100
    ) -> Dict[str, Any]:
        """
        Get logs for a component
        
        Args:
            component: Component name
            pod_name: Optional pod name (if None, gets logs from first pod)
            tail_lines: Number of log lines to retrieve
            
        Returns:
            Dictionary with logs
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        if component not in self.component_map:
            return {"error": f"Unknown component: {component}"}
        
        try:
            component_name = self.component_map[component]
            
            # Get pods for this component
            pods = self._get_cached_resource("pods", self._fetch_pods)
            component_pods = [p for p in pods if component_name in p["name"]]
            
            if not component_pods:
                return {"error": f"No pods found for component: {component}"}
            
            # Find specific pod or use first one
            target_pod = None
            if pod_name:
                target_pod = next((p for p in component_pods if p["name"] == pod_name), None)
                if not target_pod:
                    return {"error": f"Pod not found: {pod_name}"}
            else:
                # Use first running pod
                running_pods = [p for p in component_pods if p["status"] == "Running"]
                if running_pods:
                    target_pod = running_pods[0]
                else:
                    target_pod = component_pods[0]
            
            # Get logs
            logs = self.core_v1.read_namespaced_pod_log(
                name=target_pod["name"],
                namespace=self.namespace,
                tail_lines=tail_lines
            )
            
            return {
                "component": component,
                "pod_name": target_pod["name"],
                "logs": logs.split("\n")
            }
            
        except Exception as e:
            logger.error(f"Error getting logs for component {component}: {str(e)}")
            return {"error": str(e)}
    
    def get_component_metrics(self, component: str) -> Dict[str, Any]:
        """
        Get metrics for a component
        
        Args:
            component: Component name
            
        Returns:
            Dictionary with metrics
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        if component not in self.component_map:
            return {"error": f"Unknown component: {component}"}
        
        try:
            component_name = self.component_map[component]
            
            # Get pods for this component
            pods = self._get_cached_resource("pods", self._fetch_pods)
            component_pods = [p for p in pods if component_name in p["name"]]
            
            if not component_pods:
                return {"error": f"No pods found for component: {component}"}
            
            # Get metrics for each pod
            pod_metrics = []
            metrics_api = client.CustomObjectsApi()
            
            for pod in component_pods:
                try:
                    # This requires metrics-server to be installed
                    metrics = metrics_api.get_namespaced_custom_object(
                        group="metrics.k8s.io",
                        version="v1beta1",
                        namespace=self.namespace,
                        plural="pods",
                        name=pod["name"]
                    )
                    
                    # Process metrics
                    pod_metric = {
                        "pod_name": pod["name"],
                        "cpu": {},
                        "memory": {}
                    }
                    
                    # Process container metrics
                    for container in metrics.get("containers", []):
                        container_name = container.get("name")
                        cpu = container.get("usage", {}).get("cpu", "0")
                        memory = container.get("usage", {}).get("memory", "0")
                        
                        # Convert CPU to millicores
                        if cpu.endswith("n"):
                            cpu_millicores = float(cpu[:-1]) / 1000000
                        else:
                            cpu_millicores = float(cpu)
                        
                        # Convert memory to MB
                        if memory.endswith("Ki"):
                            memory_mb = float(memory[:-2]) / 1024
                        elif memory.endswith("Mi"):
                            memory_mb = float(memory[:-2])
                        elif memory.endswith("Gi"):
                            memory_mb = float(memory[:-2]) * 1024
                        else:
                            memory_mb = float(memory) / (1024 * 1024)
                        
                        pod_metric["cpu"][container_name] = cpu_millicores
                        pod_metric["memory"][container_name] = memory_mb
                    
                    pod_metrics.append(pod_metric)
                    
                except Exception as e:
                    logger.warning(f"Error getting metrics for pod {pod['name']}: {str(e)}")
                    # Continue with next pod
            
            return {
                "component": component,
                "pod_count": len(component_pods),
                "pod_metrics": pod_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics for component {component}: {str(e)}")
            return {"error": str(e)}
    
    def update_config_map(
        self, 
        name: str, 
        data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update a ConfigMap
        
        Args:
            name: ConfigMap name
            data: ConfigMap data
            
        Returns:
            Dictionary with update result
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        try:
            # Check if ConfigMap exists
            try:
                config_map = self.core_v1.read_namespaced_config_map(
                    name=name,
                    namespace=self.namespace
                )
                
                # Update existing ConfigMap
                config_map.data = data
                
                self.core_v1.patch_namespaced_config_map(
                    name=name,
                    namespace=self.namespace,
                    body=config_map
                )
                
                return {
                    "name": name,
                    "status": "updated"
                }
                
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    # Create new ConfigMap
                    config_map = client.V1ConfigMap(
                        metadata=client.V1ObjectMeta(name=name),
                        data=data
                    )
                    
                    self.core_v1.create_namespaced_config_map(
                        namespace=self.namespace,
                        body=config_map
                    )
                    
                    return {
                        "name": name,
                        "status": "created"
                    }
                else:
                    raise
                
        except Exception as e:
            logger.error(f"Error updating ConfigMap {name}: {str(e)}")
            return {"error": str(e)}
    
    def update_secret(
        self, 
        name: str, 
        data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update a Secret
        
        Args:
            name: Secret name
            data: Secret data (plaintext, will be base64 encoded)
            
        Returns:
            Dictionary with update result
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        try:
            # Encode data as base64
            import base64
            encoded_data = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}
            
            # Check if Secret exists
            try:
                secret = self.core_v1.read_namespaced_secret(
                    name=name,
                    namespace=self.namespace
                )
                
                # Update existing Secret
                secret.data = encoded_data
                
                self.core_v1.patch_namespaced_secret(
                    name=name,
                    namespace=self.namespace,
                    body=secret
                )
                
                return {
                    "name": name,
                    "status": "updated"
                }
                
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    # Create new Secret
                    secret = client.V1Secret(
                        metadata=client.V1ObjectMeta(name=name),
                        data=encoded_data
                    )
                    
                    self.core_v1.create_namespaced_secret(
                        namespace=self.namespace,
                        body=secret
                    )
                    
                    return {
                        "name": name,
                        "status": "created"
                    }
                else:
                    raise
                
        except Exception as e:
            logger.error(f"Error updating Secret {name}: {str(e)}")
            return {"error": str(e)}
    
    def execute_command_in_pod(
        self, 
        pod_name: str, 
        container_name: Optional[str] = None,
        command: List[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a command in a pod
        
        Args:
            pod_name: Pod name
            container_name: Container name (if None, uses first container)
            command: Command to execute (list of strings)
            
        Returns:
            Dictionary with command output
        """
        if not self.is_configured():
            return {"error": "Kubernetes client not configured"}
        
        if not command:
            return {"error": "No command specified"}
        
        try:
            # Get pod
            try:
                pod = self.core_v1.read_namespaced_pod(
                    name=pod_name,
                    namespace=self.namespace
                )
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    return {"error": f"Pod not found: {pod_name}"}
                else:
                    raise
            
            # If container name is not specified, use first container
            if not container_name:
                if not pod.spec.containers:
                    return {"error": f"No containers found in pod: {pod_name}"}
                
                container_name = pod.spec.containers[0].name
            else:
                # Verify container exists
                if not any(c.name == container_name for c in pod.spec.containers):
                    return {"error": f"Container not found in pod: {container_name}"}
            
            # Execute command
            exec_command = self.core_v1.connect_get_namespaced_pod_exec(
                name=pod_name,
                namespace=self.namespace,
                container=container_name,
                command=command,
                stdout=True,
                stderr=True,
                stdin=False,
                tty=False
            )
            
            return {
                "pod_name": pod_name,
                "container_name": container_name,
                "command": command,
                "output": exec_command
            }
            
        except Exception as e:
            logger.error(f"Error executing command in pod {pod_name}: {str(e)}")
            return {"error": str(e)}
    
    def _fetch_deployments(self) -> List[Dict[str, Any]]:
        """
        Fetch deployments from Kubernetes API
        
        Returns:
            List of deployments
        """
        try:
            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=self.namespace,
                label_selector=f"app={self.app_label}"
            )
            
            # Process deployments
            deployment_list = []
            
            for deployment in deployments.items:
                # Extract deployment info
                deployment_info = {
                    "name": deployment.metadata.name,
                    "ready_replicas": deployment.status.ready_replicas or 0,
                    "replicas": deployment.status.replicas or 0,
                    "available_replicas": deployment.status.available_replicas or 0,
                    "unavailable_replicas": deployment.status.unavailable_replicas or 0,
                    "updated_replicas": deployment.status.updated_replicas or 0,
                    "strategy": deployment.spec.strategy.type,
                    "labels": deployment.metadata.labels,
                    "created_at": deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else None,
                    "conditions": []
                }
                
                # Add conditions
                if deployment.status.conditions:
                    for condition in deployment.status.conditions:
                        deployment_info["conditions"].append({
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "last_transition_time": condition.last_transition_time.isoformat() if condition.last_transition_time else None
                        })
                
                deployment_list.append(deployment_info)
            
            return deployment_list
            
        except Exception as e:
            logger.error(f"Error fetching deployments: {str(e)}")
            return []
    
    def _fetch_pods(self) -> List[Dict[str, Any]]:
        """
        Fetch pods from Kubernetes API
        
        Returns:
            List of pods
        """
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"app={self.app_label}"
            )
            
            # Process pods
            pod_list = []
            
            for pod in pods.items:
                # Extract pod info
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "ip": pod.status.pod_ip,
                    "labels": pod.metadata.labels,
                    "created_at": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    "containers": [],
                    "ready": all(container.ready for container in (pod.status.container_statuses or [])),
                    "restarts": sum(container.restart_count for container in (pod.status.container_statuses or [])),
                    "conditions": []
                }
                
                # Add container info
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        container_info = {
                            "name": container.name,
                            "ready": container.ready,
                            "restart_count": container.restart_count,
                            "image": container.image
                        }
                        
                        # Add state info
                        if container.state.running:
                            container_info["state"] = "running"
                            container_info["started_at"] = container.state.running.started_at.isoformat() if container.state.running.started_at else None
                        elif container.state.waiting:
                            container_info["state"] = "waiting"
                            container_info["reason"] = container.state.waiting.reason
                            container_info["message"] = container.state.waiting.message
                        elif container.state.terminated:
                            container_info["state"] = "terminated"
                            container_info["reason"] = container.state.terminated.reason
                            container_info["exit_code"] = container.state.terminated.exit_code
                        
                        pod_info["containers"].append(container_info)
                
                # Add conditions
                if pod.status.conditions:
                    for condition in pod.status.conditions:
                        pod_info["conditions"].append({
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "last_transition_time": condition.last_transition_time.isoformat() if condition.last_transition_time else None
                        })
                
                pod_list.append(pod_info)
            
            return pod_list
            
        except Exception as e:
            logger.error(f"Error fetching pods: {str(e)}")
            return []
    
    def _fetch_services(self) -> List[Dict[str, Any]]:
        """
        Fetch services from Kubernetes API
        
        Returns:
            List of services
        """
        try:
            services = self.core_v1.list_namespaced_service(
                namespace=self.namespace,
                label_selector=f"app={self.app_label}"
            )
            
            # Process services
            service_list = []
            
            for service in services.items:
                # Extract service info
                service_info = {
                    "name": service.metadata.name,
                    "type": service.spec.type,
                    "cluster_ip": service.spec.cluster_ip,
                    "external_ip": [ip.ip for ip in service.status.load_balancer.ingress] if service.status.load_balancer and service.status.load_balancer.ingress else None,
                    "ports": [],
                    "labels": service.metadata.labels,
                    "created_at": service.metadata.creation_timestamp.isoformat() if service.metadata.creation_timestamp else None
                }
                
                # Add port info
                if service.spec.ports:
                    for port in service.spec.ports:
                        service_info["ports"].append({
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "node_port": port.node_port,
                            "protocol": port.protocol
                        })
                
                service_list.append(service_info)
            
            return service_list
            
        except Exception as e:
            logger.error(f"Error fetching services: {str(e)}")
            return []
    
    def _get_cached_resource(
        self,
        resource_type: str,
        fetch_function: callable
    ) -> List[Dict[str, Any]]:
        """
        Get resource from cache or fetch from API
        
        Args:
            resource_type: Type of resource (deployments, pods, services)
            fetch_function: Function to fetch resource
            
        Returns:
            List of resources
        """
        with self.cache_lock:
            # Check if cache is fresh
            if (
                resource_type in self.resource_cache and
                resource_type in self.cache_last_updated and
                (time.time() - self.cache_last_updated[resource_type]) < self.cache_ttl
            ):
                return self.resource_cache[resource_type]
        
        # Fetch from API
        resources = fetch_function()
        
        # Update cache
        with self.cache_lock:
            self.resource_cache[resource_type] = resources
            self.cache_last_updated[resource_type] = time.time()
        
        return resources
    
    def _invalidate_cache(self, resource_type: Optional[str] = None):
        """
        Invalidate cache for a specific resource type or all resources
        
        Args:
            resource_type: Type of resource to invalidate (None for all)
        """
        with self.cache_lock:
            if resource_type:
                if resource_type in self.resource_cache:
                    del self.resource_cache[resource_type]
                if resource_type in self.cache_last_updated:
                    del self.cache_last_updated[resource_type]
            else:
                self.resource_cache = {}
                self.cache_last_updated = {}

# Create singleton instance
kubernetes_client = KubernetesClient()

# Son güncelleme: 2025-05-20 10:49:41
# Güncelleyen: Teeksss