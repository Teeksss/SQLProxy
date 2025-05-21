"""
TypeScript SDK Generator for SQL Proxy

This module generates TypeScript SDK code for SQL Proxy API integration.

Last updated: 2025-05-21 05:35:49
Updated by: Teeksss
"""

import os
import logging
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from app.core.config import settings
from app.schemas.sdk import SDKConfig, APIEndpoint, SDKLanguage
from app.services.openapi import get_openapi_schema

logger = logging.getLogger(__name__)

class TypeScriptSDKGenerator:
    """
    Generator for TypeScript SDK
    
    Creates a TypeScript SDK from OpenAPI specification and custom configurations.
    """
    
    def __init__(self, config: SDKConfig):
        """Initialize TypeScript SDK generator"""
        self.config = config
        self.openapi_schema = get_openapi_schema()
        self.output_dir = Path(settings.SDK_OUTPUT_DIR) / f"typescript-{config.version}"
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self) -> str:
        """
        Generate TypeScript SDK
        
        Returns:
            Path to the generated SDK
        """
        try:
            logger.info(f"Generating TypeScript SDK version {self.config.version}")
            
            # Create directory structure
            self._create_directory_structure()
            
            # Generate type definitions
            self._generate_types()
            
            # Generate API client services
            self._generate_api_services()
            
            # Generate core modules
            self._generate_core_modules()
            
            # Generate index file
            self._generate_index_file()
            
            # Generate package.json
            self._generate_package_json()
            
            # Generate tsconfig.json
            self._generate_tsconfig_json()
            
            # Generate README.md
            self._generate_readme()
            
            logger.info(f"TypeScript SDK generation completed: {self.output_dir}")
            return str(self.output_dir)
            
        except Exception as e:
            logger.error(f"Error generating TypeScript SDK: {e}", exc_info=True)
            raise
    
    def _create_directory_structure(self):
        """Create TypeScript project directory structure"""
        # Main directories
        (self.output_dir / "src").mkdir(exist_ok=True)
        (self.output_dir / "src/api").mkdir(exist_ok=True)
        (self.output_dir / "src/types").mkdir(exist_ok=True)
        (self.output_dir / "src/core").mkdir(exist_ok=True)
    
    def _generate_types(self):
        """Generate TypeScript type definitions from OpenAPI schemas"""
        if not self.openapi_schema or "components" not in self.openapi_schema:
            logger.warning("No components found in OpenAPI schema")
            return
        
        schemas = self.openapi_schema.get("components", {}).get("schemas", {})
        
        types_content = """/**
 * Type definitions for SQL Proxy API
 * 
 * Auto-generated from OpenAPI schema
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

"""
        
        # Process schemas and convert to TypeScript interfaces
        for schema_name, schema in schemas.items():
            # Skip excluded schemas
            if schema_name in self.config.excluded_models:
                continue
            
            # Convert schema to TypeScript interface
            types_content += self._convert_schema_to_typescript(schema_name, schema)
            types_content += "\n\n"
        
        # Write to file
        with open(self.output_dir / "src/types/api.ts", "w") as f:
            f.write(types_content)
    
    def _convert_schema_to_typescript(self, schema_name: str, schema: Dict[str, Any]) -> str:
        """
        Convert OpenAPI schema to TypeScript interface
        
        Args:
            schema_name: Name of the schema
            schema: OpenAPI schema definition
            
        Returns:
            TypeScript interface code
        """
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        result = f"export interface {schema_name} {{\n"
        
        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required
            ts_type = self._get_typescript_type(prop_schema)
            description = prop_schema.get("description", "").replace("\n", " ")
            
            if description:
                result += f"  /** {description} */\n"
            
            result += f"  {prop_name}{'' if is_required else '?'}: {ts_type};\n"
        
        result += "}"
        
        return result
    
    def _get_typescript_type(self, schema: Dict[str, Any]) -> str:
        """
        Get TypeScript type for OpenAPI schema property
        
        Args:
            schema: Property schema
            
        Returns:
            TypeScript type
        """
        schema_type = schema.get("type", "string")
        format_type = schema.get("format", "")
        
        if schema_type == "array":
            item_type = self._get_typescript_type(schema.get("items", {}))
            return f"{item_type}[]"
        elif schema_type == "object":
            if "additionalProperties" in schema:
                value_type = self._get_typescript_type(schema.get("additionalProperties", {}))
                return f"Record<string, {value_type}>"
            else:
                return "Record<string, any>"
        elif schema_type == "integer" or schema_type == "number":
            return "number"
        elif schema_type == "boolean":
            return "boolean"
        elif schema_type == "string":
            if format_type == "date" or format_type == "date-time":
                return "string"  # or "Date" if you want to use Date objects
            else:
                return "string"
        elif "$ref" in schema:
            ref = schema.get("$ref", "")
            model_name = ref.split("/")[-1]
            return model_name
        else:
            return "any"
    
    def _generate_api_services(self):
        """Generate TypeScript API service modules"""
        # Generate service for each endpoint
        for endpoint in self.config.endpoints:
            self._generate_endpoint_service(endpoint)
        
        # Generate api index file
        self._generate_api_index()
    
    def _generate_endpoint_service(self, endpoint: APIEndpoint):
        """
        Generate API service for an endpoint
        
        Args:
            endpoint: API endpoint configuration
        """
        file_name = endpoint.path_prefix.strip("/").replace("/", "-") + ".ts"
        
        content = f"""/**
 * {endpoint.class_name} API Service
 * 
{f' * {endpoint.description}' if endpoint.description else ''}
 */

import {{ api }} from '../core/api';
import {{ AxiosError }} from 'axios';

export const {endpoint.path_prefix.strip("/").replace("/", "")}Api = {{
"""
        
        # Get OpenAPI paths for this endpoint
        paths = self._get_paths_for_endpoint(endpoint)
        
        for path_info in paths:
            # Generate method for this path
            method_name = self._get_method_name(path_info)
            method_params = self._get_method_params(path_info)
            method_return_type = self._get_method_return_type(path_info)
            
            # Add method comment
            content += f"""  /**
   * {path_info.get('summary', 'No description available')}
   *
{f'   * {path_info.get("description", "")}' if path_info.get("description") else ''}
   */
  {method_name}: async ({method_params}): Promise<{method_return_type}> => {{
    try {{
      const response = await api.{path_info.get('method', 'get').lower()}(`{self._format_path_template(path_info.get('path', ''))}`, {self._get_method_body(path_info)});
      return response.data;
    }} catch (error) {{
      throw handleApiError(error);
    }}
  }},

"""
        
        # Add error handler
        content += """};

/**
 * Handle API errors
 */
function handleApiError(error: any) {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || error.message;
    return new Error(message);
  }
  return error;
}
"""
        
        # Write to file
        with open(self.output_dir / f"src/api/{file_name}", "w") as f:
            f.write(content)
    
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
                    paths.append({
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation.get("operationId", ""),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "parameters": operation.get("parameters", []),
                        "request_body": operation.get("requestBody", None),
                        "responses": operation.get("responses", {})
                    })
        
        return paths
    
    def _get_method_name(self, path_info: Dict[str, Any]) -> str:
        """
        Generate method name from path info
        
        Args:
            path_info: OpenAPI path info
            
        Returns:
            Method name
        """
        if path_info.get("operation_id"):
            return self._camel_case(path_info["operation_id"])
        
        # Fallback: generate from path and method
        method = path_info.get("method", "get").lower()
        path = path_info.get("path", "")
        
        # Extract meaningful parts from path
        path_parts = [p for p in path.split("/") if p and not p.startswith("{")]
        
        if path_parts:
            resource = path_parts[-1]
            
            # Handle common patterns
            if method == "get" and "{id}" in path:
                return f"get{self._pascal_case(resource[:-1] if resource.endswith('s') else resource)}"
            elif method == "get":
                return f"get{self._pascal_case(resource)}"
            elif method == "post":
                return f"create{self._pascal_case(resource[:-1] if resource.endswith('s') else resource)}"
            elif method == "put" or method == "patch":
                return f"update{self._pascal_case(resource[:-1] if resource.endswith('s') else resource)}"
            elif method == "delete":
                return f"delete{self._pascal_case(resource[:-1] if resource.endswith('s') else resource)}"
        
        # Last resort
        return f"{method}{self._pascal_case(path.replace('/', '_'))}"
    
    def _get_method_params(self, path_info: Dict[str, Any]) -> str:
        """
        Generate method parameters from path info
        
        Args:
            path_info: OpenAPI path info
            
        Returns:
            Method parameters
        """
        params = []
        path_params = []
        query_params = []
        header_params = []
        has_request_body = False
        
        # Process parameters
        for param in path_info.get("parameters", []):
            param_name = param.get("name", "")
            param_in = param.get("in", "")
            param_required = param.get("required", False)
            param_schema = param.get("schema", {})
            param_type = self._get_typescript_type(param_schema)
            
            if param_in == "path":
                path_params.append(param_name)
                params.append(f"{param_name}: {param_type}")
            elif param_in == "query":
                query_params.append(param_name)
                params.append(f"{param_name}{'' if param_required else '?'}: {param_type}")
            elif param_in == "header":
                header_params.append(param_name)
                params.append(f"{param_name}{'' if param_required else '?'}: {param_type}")
        
        # Process request body
        if path_info.get("request_body"):
            has_request_body = True
            content = path_info["request_body"].get("content", {})
            content_type = next(iter(content.keys()), "application/json")
            body_schema = content.get(content_type, {}).get("schema", {})
            body_type = self._get_typescript_type(body_schema)
            
            params.append(f"data: {body_type}")
        
        # Add options parameter for query and header params
        options_params = []
        
        if query_params:
            options_params.append(f"params?: {{ {', '.join([f'{p}?: any' for p in query_params])} }}")
        
        if header_params:
            options_params.append(f"headers?: {{ {', '.join([f'{p}?: string' for p in header_params])} }}")
        
        if options_params and not has_request_body:
            params.append(f"options?: {{ {'; '.join(options_params)} }}")
        
        return ", ".join(params)
    
    def _get_method_return_type(self, path_info: Dict[str, Any]) -> str:
        """
        Generate method return type from path info
        
        Args:
            path_info: OpenAPI path info
            
        Returns:
            Method return type
        """
        responses = path_info.get("responses", {})
        success_response = responses.get("200", {}) or responses.get("201", {})
        
        if not success_response:
            return "any"
        
        content = success_response.get("content", {})
        content_type = next(iter(content.keys()), "application/json")
        response_schema = content.get(content_type, {}).get("schema", {})
        
        return self._get_typescript_type(response_schema)
    
    def _get_method_body(self, path_info: Dict[str, Any]) -> str:
        """
        Generate method body from path info
        
        Args:
            path_info: OpenAPI path info
            
        Returns:
            Method body
        """
        method = path_info.get("method", "get").lower()
        query_params = [p for p in path_info.get("parameters", []) if p.get("in") == "query"]
        
        if method in ["post", "put", "patch"] and path_info.get("request_body"):
            if query_params:
                return "data, { params: options?.params, headers: options?.headers }"
            else:
                return "data"
        else:
            if query_params:
                return "{ params: options?.params, headers: options?.headers }"
            else:
                return ""
    
    def _format_path_template(self, path: str) -> str:
        """
        Format path template for TypeScript template literals
        
        Args:
            path: API path
            
        Returns:
            Formatted path template
        """
        # Replace {param} with ${param}
        return path.replace("{", "${")
    
    def _generate_api_index(self):
        """Generate API services index file"""
        content = "/**\n * API Services index\n */\n\n"
        
        for endpoint in self.config.endpoints:
            file_name = endpoint.path_prefix.strip("/").replace("/", "-")
            service_name = endpoint.path_prefix.strip("/").replace("/", "") + "Api"
            
            content += f"export {{ {service_name} }} from './{file_name}';\n"
        
        # Write to file
        with open(self.output_dir / "src/api/index.ts", "w") as f:
            f.write(content)
    
    def _generate_core_modules(self):
        """Generate core modules for the SDK"""
        # Generate API client module
        self._generate_api_client()
        
        # Generate config module
        self._generate_config_module()
    
    def _generate_api_client(self):
        """Generate API client module"""
        content = """/**
 * API Client configuration
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { config } from './config';

/**
 * Configure axios instance with base URL and default headers
 */
export const api: AxiosInstance = axios.create({
  baseURL: config.baseURL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

/**
 * Set authentication token
 * 
 * @param token JWT token
 */
export const setAuthToken = (token: string | null): void => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

/**
 * Configure API client
 * 
 * @param options Configuration options
 */
export const configureApi = (options: { baseURL?: string, timeout?: number, headers?: Record<string, string> }): void => {
  if (options.baseURL) {
    api.defaults.baseURL = options.baseURL;
  }
  
  if (options.timeout) {
    api.defaults.timeout = options.timeout;
  }
  
  if (options.headers) {
    Object.entries(options.headers).forEach(([key, value]) => {
      api.defaults.headers.common[key] = value;
    });
  }
};
"""
        
        # Write to file
        with open(self.output_dir / "src/core/api.ts", "w") as f:
            f.write(content)
    
    def _generate_config_module(self):
        """Generate configuration module"""
        content = f"""/**
 * SDK Configuration
 */

export interface SQLProxyConfig {{
  /**
   * Base URL for the API
   */
  baseURL: string;
  
  /**
   * Request timeout in milliseconds
   */
  timeout: number;
  
  /**
   * SDK version
   */
  version: string;
}}

/**
 * Default configuration
 */
export const config: SQLProxyConfig = {{
  baseURL: '{self.config.base_url}',
  timeout: 30000,
  version: '{self.config.version}'
}};
"""
        
        # Write to file
        with open(self.output_dir / "src/core/config.ts", "w") as f:
            f.write(content)
    
    def _generate_index_file(self):
        """Generate main index file"""
        content = """/**
 * SQL Proxy TypeScript SDK
 */

// Export API services
export * from './api';

// Export types
export * from './types/api';

// Export core functionality
export { api, setAuthToken, configureApi } from './core/api';
export { config, SQLProxyConfig } from './core/config';
"""
        
        # Write to file
        with open(self.output_dir / "src/index.ts", "w") as f:
            f.write(content)
    
    def _generate_package_json(self):
        """Generate package.json file"""
        package_name = self.config.package_name
        if not package_name.startswith("@"):
            package_name = package_name.replace("/", "-").lower()
        
        dependencies = {
            "axios": "^1.5.0"
        }
        
        dev_dependencies = {
            "typescript": "^5.0.4",
            "@types/node": "^18.16.0",
            "rimraf": "^5.0.1"
        }
        
        # Add custom dependencies
        dependencies.update(self.config.dependencies)
        
        package_json = {
            "name": package_name,
            "version": self.config.version,
            "description": self.config.description,
            "author": self.config.author,
            "license": self.config.license,
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "files": [
                "dist",
                "README.md"
            ],
            "scripts": {
                "build": "rimraf dist && tsc",
                "prepublishOnly": "npm run build"
            },
            "dependencies": dependencies,
            "devDependencies": dev_dependencies
        }
        
        # Write to file
        with open(self.output_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
    
    def _generate_tsconfig_json(self):
        """Generate tsconfig.json file"""
        tsconfig = {
            "compilerOptions": {
                "target": "es2017",
                "module": "commonjs",
                "declaration": True,
                "outDir": "./dist",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True
            },
            "include": [
                "src/**/*"
            ],
            "exclude": [
                "node_modules",
                "dist"
            ]
        }
        
        # Write to file
        with open(self.output_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)
    
    def _generate_readme(self):
        """Generate README.md file"""
        readme = f"""# {self.config.name}

{self.config.description}

## Installation

```bash
npm install {self.config.package_name}