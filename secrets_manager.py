"""
Secrets Manager for Think-Tank.

This module provides secure handling of API keys and other sensitive information.
It supports multiple backend storage options and implements best practices for
secret management in different environments.

Features:
- Secure loading of secrets from various sources
- Encryption of sensitive values
- Rotation and versioning support
- Audit logging for secret access
- Fallback mechanisms for development environments
"""

import os
import json
import logging
import base64
import hashlib
from typing import Dict, Any, Optional, Union
from functools import lru_cache
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secrets_manager")

# Import settings after logger configuration to avoid circular imports
from config import settings

class SecretNotFoundError(Exception):
    """Exception raised when a requested secret is not found."""
    pass

class SecretAccessError(Exception):
    """Exception raised when there's an error accessing a secret."""
    pass

class SecretBackendError(Exception):
    """Exception raised when there's an error with the secret backend."""
    pass

class SecretsManager:
    """
    Manages secure storage and retrieval of sensitive information.
    
    This class provides a unified interface for accessing secrets from
    various backend storage options, with support for encryption,
    caching, and audit logging.
    """
    
    def __init__(self, backend: str = "env"):
        """
        Initialize the secrets manager.
        
        Args:
            backend: The backend storage to use ('env', 'file', 'vault', 'aws')
        """
        self.backend = backend
        self._cache = {}
        self._cache_ttl = {}
        self._default_ttl = 3600  # 1 hour
        self._encryption_key = self._derive_encryption_key()
        logger.info(f"Secrets manager initialized with {backend} backend")
    
    def _derive_encryption_key(self) -> bytes:
        """
        Derive an encryption key from the application secret key.
        
        Returns:
            bytes: The derived encryption key
        """
        try:
            # Use the application secret key as the base for deriving an encryption key
            base_key = settings.SECRET_KEY.encode()
            salt = b"think-tank-secrets-manager"  # Static salt
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(base_key))
            return key
        except Exception as e:
            logger.error(f"Failed to derive encryption key: {e}")
            # Fallback to a development key (only in non-production)
            if settings.ENVIRONMENT != "production":
                logger.warning("Using fallback encryption key for development")
                return base64.urlsafe_b64encode(b"development-only-key-do-not-use-in-prod-00")
            raise SecretBackendError("Could not derive encryption key") from e
    
    def _encrypt(self, value: str) -> str:
        """
        Encrypt a value using Fernet symmetric encryption.
        
        Args:
            value: The value to encrypt
            
        Returns:
            str: The encrypted value as a base64 string
        """
        try:
            f = Fernet(self._encryption_key)
            encrypted = f.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise SecretBackendError("Failed to encrypt value") from e
    
    def _decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt a value using Fernet symmetric encryption.
        
        Args:
            encrypted_value: The encrypted value as a base64 string
            
        Returns:
            str: The decrypted value
        """
        try:
            f = Fernet(self._encryption_key)
            decoded = base64.urlsafe_b64decode(encrypted_value)
            decrypted = f.decrypt(decoded)
            return decrypted.decode()
        except InvalidToken:
            logger.error("Invalid token or wrong key")
            raise SecretAccessError("Could not decrypt value: invalid token")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise SecretBackendError("Failed to decrypt value") from e
    
    def _get_from_env(self, key: str) -> Optional[str]:
        """
        Get a secret from environment variables.
        
        Args:
            key: The secret key
            
        Returns:
            Optional[str]: The secret value or None if not found
        """
        return os.environ.get(key)
    
    def _get_from_file(self, key: str) -> Optional[str]:
        """
        Get a secret from a local secrets file.
        
        Args:
            key: The secret key
            
        Returns:
            Optional[str]: The secret value or None if not found
        """
        try:
            secrets_file = os.path.join(os.path.dirname(__file__), "secrets.json")
            if not os.path.exists(secrets_file):
                logger.warning(f"Secrets file not found: {secrets_file}")
                return None
                
            with open(secrets_file, "r") as f:
                secrets = json.load(f)
            
            encrypted_value = secrets.get(key)
            if not encrypted_value:
                return None
                
            return self._decrypt(encrypted_value)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in secrets file")
            return None
        except Exception as e:
            logger.error(f"Error reading from secrets file: {e}")
            return None
    
    def _get_from_vault(self, key: str) -> Optional[str]:
        """
        Get a secret from HashiCorp Vault.
        
        Args:
            key: The secret key
            
        Returns:
            Optional[str]: The secret value or None if not found
        """
        # This is a placeholder for Vault integration
        # In a real implementation, you would use the hvac library
        logger.warning("Vault backend not fully implemented")
        return None
    
    def _get_from_aws(self, key: str) -> Optional[str]:
        """
        Get a secret from AWS Secrets Manager.
        
        Args:
            key: The secret key
            
        Returns:
            Optional[str]: The secret value or None if not found
        """
        # This is a placeholder for AWS Secrets Manager integration
        # In a real implementation, you would use boto3
        logger.warning("AWS Secrets Manager backend not fully implemented")
        return None
    
    def _log_access(self, key: str, success: bool) -> None:
        """
        Log access to a secret for audit purposes.
        
        Args:
            key: The secret key
            success: Whether the access was successful
        """
        # In a production system, this would write to a secure audit log
        if settings.ENVIRONMENT == "production":
            # Mask the key name in logs if it contains sensitive terms
            sensitive_terms = ["password", "secret", "key", "token", "credential"]
            log_key = key
            for term in sensitive_terms:
                if term.lower() in key.lower():
                    log_key = f"{key[:3]}***{key[-3:]}"
                    break
                    
            logger.info(
                f"Secret access: {log_key} - "
                f"Success: {success} - "
                f"User: system - "  # In a real app, include the authenticated user
                f"IP: local"  # In a real app, include the request IP
            )
    
    def get_secret(self, key: str, default: Any = None, ttl: int = None) -> Any:
        """
        Get a secret from the configured backend.
        
        Args:
            key: The secret key
            default: Default value if secret is not found
            ttl: Cache TTL in seconds (None uses default)
            
        Returns:
            Any: The secret value or default if not found
        """
        # Check cache first
        if key in self._cache and key in self._cache_ttl:
            if datetime.now() < self._cache_ttl[key]:
                return self._cache[key]
            else:
                # Expired cache
                del self._cache[key]
                del self._cache_ttl[key]
        
        # Get from appropriate backend
        value = None
        try:
            if self.backend == "env":
                value = self._get_from_env(key)
            elif self.backend == "file":
                value = self._get_from_file(key)
            elif self.backend == "vault":
                value = self._get_from_vault(key)
            elif self.backend == "aws":
                value = self._get_from_aws(key)
            else:
                logger.error(f"Unknown backend: {self.backend}")
                self._log_access(key, False)
                return default
            
            if value is None:
                self._log_access(key, False)
                return default
                
            # Cache the value
            self._cache[key] = value
            cache_ttl = ttl if ttl is not None else self._default_ttl
            self._cache_ttl[key] = datetime.now() + timedelta(seconds=cache_ttl)
            
            self._log_access(key, True)
            return value
            
        except Exception as e:
            logger.error(f"Error retrieving secret {key}: {e}")
            self._log_access(key, False)
            return default
    
    def set_secret(self, key: str, value: str) -> bool:
        """
        Set a secret in the configured backend.
        
        Args:
            key: The secret key
            value: The secret value
            
        Returns:
            bool: True if successful, False otherwise
        """
        # This is primarily for the file backend
        # Other backends might be read-only or have different APIs
        if self.backend != "file":
            logger.warning(f"Setting secrets not supported for {self.backend} backend")
            return False
            
        try:
            secrets_file = os.path.join(os.path.dirname(__file__), "secrets.json")
            secrets = {}
            
            # Read existing secrets
            if os.path.exists(secrets_file):
                with open(secrets_file, "r") as f:
                    try:
                        secrets = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in secrets file, creating new file")
            
            # Encrypt and store the value
            encrypted_value = self._encrypt(value)
            secrets[key] = encrypted_value
            
            # Write back to file
            with open(secrets_file, "w") as f:
                json.dump(secrets, f, indent=2)
            
            # Update cache
            self._cache[key] = value
            self._cache_ttl[key] = datetime.now() + timedelta(seconds=self._default_ttl)
            
            logger.info(f"Secret {key} stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error storing secret {key}: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """
        Delete a secret from the configured backend.
        
        Args:
            key: The secret key
            
        Returns:
            bool: True if successful, False otherwise
        """
        # This is primarily for the file backend
        if self.backend != "file":
            logger.warning(f"Deleting secrets not supported for {self.backend} backend")
            return False
            
        try:
            secrets_file = os.path.join(os.path.dirname(__file__), "secrets.json")
            if not os.path.exists(secrets_file):
                return False
                
            # Read existing secrets
            with open(secrets_file, "r") as f:
                try:
                    secrets = json.load(f)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in secrets file")
                    return False
            
            # Remove the key if it exists
            if key in secrets:
                del secrets[key]
                
                # Write back to file
                with open(secrets_file, "w") as f:
                    json.dump(secrets, f, indent=2)
                
                # Remove from cache
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_ttl:
                    del self._cache_ttl[key]
                
                logger.info(f"Secret {key} deleted successfully")
                return True
            else:
                logger.warning(f"Secret {key} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting secret {key}: {e}")
            return False
    
    def rotate_encryption_key(self, new_key: str) -> bool:
        """
        Rotate the encryption key used for the file backend.
        
        Args:
            new_key: The new encryption key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.backend != "file":
            logger.warning(f"Key rotation not supported for {self.backend} backend")
            return False
            
        try:
            secrets_file = os.path.join(os.path.dirname(__file__), "secrets.json")
            if not os.path.exists(secrets_file):
                logger.warning("No secrets file to rotate keys for")
                return True
                
            # Read existing secrets
            with open(secrets_file, "r") as f:
                try:
                    secrets = json.load(f)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in secrets file")
                    return False
            
            # Decrypt all values with old key and re-encrypt with new key
            old_key = self._encryption_key
            self._encryption_key = new_key.encode()
            
            rotated_secrets = {}
            for key, encrypted_value in secrets.items():
                try:
                    # Decrypt with old key
                    f = Fernet(old_key)
                    decoded = base64.urlsafe_b64decode(encrypted_value)
                    decrypted = f.decrypt(decoded).decode()
                    
                    # Re-encrypt with new key
                    rotated_secrets[key] = self._encrypt(decrypted)
                except Exception as e:
                    logger.error(f"Failed to rotate key for secret {key}: {e}")
                    self._encryption_key = old_key  # Restore old key
                    return False
            
            # Write rotated secrets back to file
            with open(secrets_file, "w") as f:
                json.dump(rotated_secrets, f, indent=2)
            
            # Clear cache
            self._cache = {}
            self._cache_ttl = {}
            
            logger.info("Encryption key rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating encryption key: {e}")
            self._encryption_key = old_key  # Restore old key
            return False


@lru_cache()
def get_secrets_manager() -> SecretsManager:
    """
    Get a cached instance of the secrets manager.
    
    Returns:
        SecretsManager: The secrets manager instance
    """
    # Determine the appropriate backend based on environment
    if settings.ENVIRONMENT == "production":
        # In production, prefer a secure backend like Vault or AWS
        if os.environ.get("VAULT_ADDR"):
            backend = "vault"
        elif os.environ.get("AWS_SECRET_ACCESS_KEY"):
            backend = "aws"
        else:
            backend = "env"
    else:
        # In development, use environment variables or local file
        backend = "env"
    
    return SecretsManager(backend=backend)


# Create a global secrets manager instance
secrets_manager = get_secrets_manager()


def get_api_key(service: str) -> Optional[str]:
    """
    Get an API key for a specific service.
    
    This is a convenience function for retrieving API keys with appropriate
    fallbacks and validation.
    
    Args:
        service: The service name (e.g., 'openai', 'anthropic')
        
    Returns:
        Optional[str]: The API key or None if not found
    """
    # Map service names to environment variable names
    service_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "azure": "AZURE_API_KEY",
        "huggingface": "HUGGINGFACE_API_KEY",
    }
    
    if service not in service_map:
        logger.warning(f"Unknown service: {service}")
        return None
    
    env_var = service_map[service]
    
    # Try to get from secrets manager first
    api_key = secrets_manager.get_secret(env_var)
    
    # If not found and in development, try to get from settings
    if not api_key and settings.ENVIRONMENT == "development":
        api_key = getattr(settings, env_var, None)
        if api_key:
            logger.warning(f"Using {service} API key from settings (not secure for production)")
    
    # Validate the API key format if present
    if api_key:
        # Basic validation - most API keys are at least 20 chars
        if len(api_key) < 20:
            logger.warning(f"{service} API key seems too short, might be invalid")
        
        # Service-specific validation
        if service == "openai" and not api_key.startswith(("sk-", "org-")):
            logger.warning("OpenAI API key format seems invalid")
        elif service == "anthropic" and not api_key.startswith(("sk-ant-", "sk-")):
            logger.warning("Anthropic API key format seems invalid")
    
    return api_key


def mask_secret(secret: str) -> str:
    """
    Mask a secret for display or logging.
    
    Args:
        secret: The secret to mask
        
    Returns:
        str: The masked secret
    """
    if not secret:
        return ""
    
    if len(secret) <= 8:
        return "****"
    
    return f"{secret[:4]}****{secret[-4:]}"