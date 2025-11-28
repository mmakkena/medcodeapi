"""
AWS Systems Manager Parameter Store integration
Loads configuration and secrets from Parameter Store
"""

import os
import boto3
from botocore.exceptions import ClientError
from functools import lru_cache
from typing import Optional, Dict


class ParameterStoreConfig:
    """Load configuration from AWS Parameter Store"""

    def __init__(
        self,
        app_name: str = "nuvii",
        environment: str = "production",
        region: str = "us-east-2",
        use_parameter_store: bool = True
    ):
        self.app_name = app_name
        self.environment = environment
        self.region = region
        self.use_parameter_store = use_parameter_store
        self.parameter_prefix = f"/{app_name}/{environment}"
        self._cache: Dict[str, str] = {}

        if self.use_parameter_store:
            try:
                self.ssm_client = boto3.client('ssm', region_name=self.region)
            except Exception as e:
                print(f"Warning: Could not initialize Parameter Store client: {e}")
                print("Falling back to environment variables")
                self.use_parameter_store = False

    @lru_cache(maxsize=128)
    def get_parameter(self, parameter_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a parameter from Parameter Store or environment variable

        Args:
            parameter_name: Name of the parameter (without prefix)
            default: Default value if parameter not found

        Returns:
            Parameter value or default
        """
        # First check if already in cache
        cache_key = f"{self.parameter_prefix}/{parameter_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try Parameter Store if enabled
        if self.use_parameter_store:
            try:
                full_param_name = f"{self.parameter_prefix}/{parameter_name}"
                response = self.ssm_client.get_parameter(
                    Name=full_param_name,
                    WithDecryption=True  # Decrypt SecureString parameters
                )
                value = response['Parameter']['Value']
                self._cache[cache_key] = value
                return value
            except ClientError as e:
                if e.response['Error']['Code'] == 'ParameterNotFound':
                    print(f"Parameter {cache_key} not found in Parameter Store")
                else:
                    print(f"Error fetching parameter {cache_key}: {e}")
            except Exception as e:
                print(f"Unexpected error fetching parameter {cache_key}: {e}")

        # Fall back to environment variable
        env_value = os.getenv(parameter_name, default)
        if env_value:
            self._cache[cache_key] = env_value
        return env_value

    def get_all_parameters(self) -> Dict[str, str]:
        """
        Get all parameters under the prefix path

        Returns:
            Dictionary of parameter names to values
        """
        if not self.use_parameter_store:
            return {}

        try:
            parameters = {}
            paginator = self.ssm_client.get_paginator('get_parameters_by_path')

            for page in paginator.paginate(
                Path=self.parameter_prefix,
                Recursive=True,
                WithDecryption=True
            ):
                for param in page['Parameters']:
                    # Remove prefix from parameter name
                    param_name = param['Name'].replace(f"{self.parameter_prefix}/", "")
                    parameters[param_name] = param['Value']
                    self._cache[param['Name']] = param['Value']

            return parameters
        except Exception as e:
            print(f"Error fetching all parameters: {e}")
            return {}

    def reload_cache(self):
        """Clear the cache and reload all parameters"""
        self._cache.clear()
        self.get_parameter.cache_clear()
        return self.get_all_parameters()


# Global parameter store instance
_parameter_store: Optional[ParameterStoreConfig] = None


def get_parameter_store() -> ParameterStoreConfig:
    """Get or create the global Parameter Store instance"""
    global _parameter_store

    if _parameter_store is None:
        # Check if we should use Parameter Store
        use_ps = os.getenv('USE_PARAMETER_STORE', 'true').lower() == 'true'
        environment = os.getenv('ENVIRONMENT', 'production')
        app_name = os.getenv('APP_NAME', 'nuvii')
        region = os.getenv('AWS_REGION', 'us-east-2')

        _parameter_store = ParameterStoreConfig(
            app_name=app_name,
            environment=environment,
            region=region,
            use_parameter_store=use_ps
        )

    return _parameter_store


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get configuration value

    Args:
        key: Configuration key name
        default: Default value if not found

    Returns:
        Configuration value
    """
    ps = get_parameter_store()
    return ps.get_parameter(key, default)
