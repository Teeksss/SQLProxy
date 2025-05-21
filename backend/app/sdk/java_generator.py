"""
Java SDK Generator for SQL Proxy

This module generates Java SDK code for SQL Proxy API integration.

Last updated: 2025-05-21 05:11:29
Updated by: Teeksss
"""

import os
import logging
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.schemas.sdk import SDKConfig, APIEndpoint, SDKLanguage
from app.services.openapi import get_openapi_schema

logger = logging.getLogger(__name__)

class JavaSDKGenerator:
    """
    Generator for Java SDK
    
    Creates a Java SDK from OpenAPI specification and custom configurations.
    """
    
    def __init__(self, config: SDKConfig):
        """Initialize Java SDK generator"""
        self.config = config
        self.openapi_schema = get_openapi_schema()
        self.output_dir = Path(settings.SDK_OUTPUT_DIR) / f"java-{config.version}"
        self.template_dir = Path("app/sdk/templates/java")
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load Java-specific templates
        self._load_templates()
        
    def _load_templates(self):
        """Load Jinja templates for Java code generation"""
        self.templates = {
            "pom": self.jinja_env.get_template("pom.xml.j2"),
            "client": self.jinja_env.get_template("SQLProxyClient.java.j2"),
            "config": self.jinja_env.get_template("SQLProxyConfig.java.j2"),
            "model": self.jinja_env.get_template("model.java.j2"),
            "api": self.jinja_env.get_template("api.java.j2"),
            "readme": self.jinja_env.get_template("README.md.j2"),
            "exception": self.jinja_env.get_template("SQLProxyException.java.j2"),
            "auth": self.jinja_env.get_template("Authentication.java.j2")
        }
    
    def generate(self) -> str:
        """
        Generate Java SDK
        
        Returns:
            Path to the generated SDK
        """
        try:
            logger.info(f"Generating Java SDK version {self.config.version}")
            
            # Create directory structure
            self._create_directory_structure()
            
            # Generate project files
            self._generate_project_files()
            
            # Generate models
            self._generate_models()
            
            # Generate API client
            self._generate_api_client()
            
            # Generate README
            self._generate_readme()
            
            # Package as JAR (optional)
            if self.config.package_as_jar:
                self._package_as_jar()
            
            logger.info(f"Java SDK generation completed: {self.output_dir}")
            return str(self.output_dir)
            
        except Exception as e:
            logger.error(f"Error generating Java SDK: {e}", exc_info=True)
            raise
    
    def _create_directory_structure(self):
        """Create Java project directory structure"""
        # Main structure
        package_path = self.config.package_name.replace(".", "/")
        src_main_java = self.output_dir / "src/main/java" / package_path
        src_main_resources = self.output_dir / "src/main/resources"
        src_test_java = self.output_dir / "src/test/java" / package_path
        src_test_resources = self.output_dir / "src/test/resources"
        
        # Create directories
        for dir_path in [src_main_java, src_main_resources, src_test_java, src_test_resources]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create model and api subdirectories
        (src_main_java / "model").mkdir(exist_ok=True)
        (src_main_java / "api").mkdir(exist_ok=True)
        (src_main_java / "auth").mkdir(exist_ok=True)
        (src_main_java / "exception").mkdir(exist_ok=True)
    
    def _generate_project_files(self):
        """Generate Maven project files"""
        # Generate pom.xml
        pom_xml = self.templates["pom"].render(
            group_id=self.config.package_name.split(".")[0],
            artifact_id=self.config.package_name.split(".")[-1].lower(),
            version=self.config.version,
            name=self.config.name,
            description=self.config.description,
            author=self.config.author,
            dependencies=self.config.dependencies
        )
        
        with open(self.output_dir / "pom.xml", "w") as f:
            f.write(pom_xml)
    
    def _generate_models(self):
        """Generate Java model classes from OpenAPI schemas"""
        if not self.openapi_schema or "components" not in self.openapi_schema:
            logger.warning("No components found in OpenAPI schema")
            return
        
        schemas = self.openapi_schema.get("components", {}).get("schemas", {})
        
        for schema_name, schema in schemas.items():
            # Skip excluded schemas
            if schema_name in self.config.excluded_models:
                continue
            
            # Convert OpenAPI schema to Java class
            java_class = self._convert_schema_to_java(schema_name, schema)
            
            # Write to file
            package_path = self.config.package_name.replace(".", "/")
            model_path = self.output_dir / f"src/main/java/{package_path}/model/{schema_name}.java"
            
            with open(model_path, "w") as f:
                f.write(java_class)
    
    def _convert_schema_to_java(self, schema_name: str, schema: Dict[str, Any]) -> str:
        """
        Convert OpenAPI schema to Java class
        
        Args:
            schema_name: Name of the schema
            schema: OpenAPI schema definition
            
        Returns:
            Java class code
        """
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        imports = set(["java.util.Objects"])
        fields = []
        
        for prop_name, prop_schema in properties.items():
            java_type, prop_imports = self._get_java_type(prop_schema, prop_name in required)
            imports.update(prop_imports)
            
            fields.append({
                "name": prop_name,
                "type": java_type,
                "required": prop_name in required,
                "description": prop_schema.get("description", ""),
                "example": prop_schema.get("example", "")
            })
        
        # Render the model template
        return self.templates["model"].render(
            package_name=f"{self.config.package_name}.model",
            class_name=schema_name,
            description=schema.get("description", ""),
            imports=sorted(imports),
            fields=fields
        )
    
    def _get_java_type(self, schema: Dict[str, Any], required: bool) -> tuple:
        """
        Get Java type for OpenAPI schema property
        
        Args:
            schema: Property schema
            required: Whether the property is required
            
        Returns:
            Tuple of (java_type, imports)
        """
        schema_type = schema.get("type", "string")
        format_type = schema.get("format", "")
        imports = set()
        
        if schema_type == "array":
            item_type, item_imports = self._get_java_type(schema.get("items", {}), True)
            imports.update(item_imports)
            imports.add("java.util.List")
            java_type = f"List<{item_type}>"
        elif schema_type == "object":
            if "additionalProperties" in schema:
                imports.add("java.util.Map")
                value_type, value_imports = self._get_java_type(schema.get("additionalProperties", {}), True)
                imports.update(value_imports)
                java_type = f"Map<String, {value_type}>"
            else:
                # Inline object, use Map<String, Object>
                imports.add("java.util.Map")
                java_type = "Map<String, Object>"
        elif schema_type == "integer":
            if format_type == "int64":
                java_type = "Long"
            else:
                java_type = "Integer"
        elif schema_type == "number":
            if format_type == "float":
                java_type = "Float"
            else:
                java_type = "Double"
        elif schema_type == "boolean":
            java_type = "Boolean"
        elif schema_type == "string":
            if format_type == "date":
                imports.add("java.time.LocalDate")
                java_type = "LocalDate"
            elif format_type == "date-time":
                imports.add("java.time.LocalDateTime")
                java_type = "LocalDateTime"
            elif format_type == "binary":
                imports.add("java.io.File")
                java_type = "File"
            elif format_type == "uuid":
                imports.add("java.util.UUID")
                java_type = "UUID"
            else:
                java_type = "String"
        elif "$ref" in schema:
            ref = schema.get("$ref", "")
            model_name = ref.split("/")[-1]
            java_type = model_name
        else:
            java_type = "Object"
        
        # Wrap in Optional if not required
        if not required and not schema_type == "array" and not schema_type == "object":
            imports.add("java.util.Optional")
            java_type = f"Optional<{java_type}>"
            
        return java_type, imports
    
    def _generate_api_client(self):
        """Generate Java API client classes"""
        # Generate main client class
        self._generate_main_client()
        
        # Generate config class
        self._generate_config_class()
        
        # Generate exception class
        self._generate_exception_class()
        
        # Generate auth classes
        self._generate_auth_classes()
        
        # Generate API endpoint classes
        self._generate_api_endpoint_classes()
    
    def _generate_main_client(self):
        """Generate main client class"""
        package_path = self.config.package_name.replace(".", "/")
        client_path = self.output_dir / f"src/main/java/{package_path}/SQLProxyClient.java"
        
        client_code = self.templates["client"].render(
            package_name=self.config.package_name,
            endpoints=self.config.endpoints,
            base_url=self.config.base_url,
            version=self.config.version
        )
        
        with open(client_path, "w") as f:
            f.write(client_code)
    
    def _generate_config_class(self):
        """Generate configuration class"""
        package_path = self.config.package_name.replace(".", "/")
        config_path = self.output_dir / f"src/main/java/{package_path}/SQLProxyConfig.java"
        
        config_code = self.templates["config"].render(
            package_name=self.config.package_name,
            version=self.config.version
        )
        
        with open(config_path, "w") as f:
            f.write(config_code)
    
    def _generate_exception_class(self):
        """Generate exception class"""
        package_path = self.config.package_name.replace(".", "/")
        exception_path = self.output_dir / f"src/main/java/{package_path}/exception/SQLProxyException.java"
        
        exception_code = self.templates["exception"].render(
            package_name=f"{self.config.package_name}.exception"
        )
        
        with open(exception_path, "w") as f:
            f.write(exception_code)
    
    def _generate_auth_classes(self):
        """Generate authentication classes"""
        package_path = self.config.package_name.replace(".", "/")
        auth_path = self.output_dir / f"src/main/java/{package_path}/auth/Authentication.java"
        
        auth_code = self.templates["auth"].render(
            package_name=f"{self.config.package_name}.auth"
        )
        
        with open(auth_path, "w") as f:
            f.write(auth_code)
    
    def _generate_api_endpoint_classes(self):
        """Generate API endpoint classes"""
        for endpoint in self.config.endpoints:
            self._generate_endpoint_class(endpoint)
    
    def _generate_endpoint_class(self, endpoint: APIEndpoint):
        """
        Generate API endpoint class
        
        Args:
            endpoint: API endpoint configuration
        """
        package_path = self.config.package_name.replace(".", "/")
        endpoint_path = self.output_dir / f"src/main/java/{package_path}/api/{endpoint.class_name}.java"
        
        # Get OpenAPI paths for this endpoint
        paths = self._get_paths_for_endpoint(endpoint)
        
        endpoint_code = self.templates["api"].render(
            package_name=f"{self.config.package_name}.api",
            parent_package=self.config.package_name,
            endpoint=endpoint,
            paths=paths
        )
        
        with open(endpoint_path, "w") as f:
            f.write(endpoint_code)
    
    def _get_paths_for_endpoint(self, endpoint: APIEndpoint) -> List[Dict[str, Any]]:
        """
        Get OpenAPI paths for an endpoint
        
        Args:
            endpoint: API endpoint configuration
            
        Returns:
            List of path objects
        """
        if not self.openapi_schema or "paths" not in self.openapi_schema:
            return []
        
        paths = []
        
        for path, methods in self.openapi_schema.get("paths", {}).items():
            for method, operation in methods.items():
                # Check if this operation belongs to this endpoint
                if path.startswith(endpoint.path_prefix):
                    # Extract parameters
                    parameters = operation.get("parameters", [])
                    
                    # Extract request body
                    request_body = None
                    if "requestBody" in operation:
                        request_body = operation["requestBody"]
                    
                    # Extract responses
                    responses = operation.get("responses", {})
                    
                    paths.append({
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation.get("operationId", ""),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "parameters": parameters,
                        "request_body": request_body,
                        "responses": responses,
                        "tags": operation.get("tags", [])
                    })
        
        return paths
    
    def _generate_readme(self):
        """Generate README.md file"""
        readme_path = self.output_dir / "README.md"
        
        readme_content = self.templates["readme"].render(
            name=self.config.name,
            description=self.config.description,
            version=self.config.version,
            author=self.config.author,
            base_url=self.config.base_url,
            package_name=self.config.package_name
        )
        
        with open(readme_path, "w") as f:
            f.write(readme_content)
    
    def _package_as_jar(self):
        """Package the SDK as a JAR file"""
        try:
            # Run Maven to package
            os.chdir(self.output_dir)
            result = os.system("mvn clean package")
            
            if result != 0:
                logger.error("Failed to package SDK as JAR")
                return
            
            # Copy JAR to output directory
            artifact_id = self.config.package_name.split(".")[-1].lower()
            jar_path = self.output_dir / f"target/{artifact_id}-{self.config.version}.jar"
            shutil.copy(jar_path, self.output_dir)
            
            logger.info(f"JAR packaged successfully: {jar_path}")
            
        except Exception as e:
            logger.error(f"Error packaging JAR: {e}", exc_info=True)
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            # Clean up target directory
            target_dir = self.output_dir / "target"
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)

# Son güncelleme: 2025-05-21 05:11:29
# Güncelleyen: Teeksss