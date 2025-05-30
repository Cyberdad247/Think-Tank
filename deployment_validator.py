#!/usr/bin/env python3
"""
Deployment Validator for Think-Tank

This script verifies that all prerequisites for deployment are met,
including system requirements, dependencies, configuration, and permissions.

Usage:
    python deployment_validator.py [--verbose] [--fix] [--config CONFIG_FILE]

Options:
    --verbose       Show detailed output for each check
    --fix           Attempt to fix issues automatically
    --config        Path to custom config file (default: .env)
"""

import os
import sys
import json
import shutil
import socket
import platform
import subprocess
import argparse
import logging
import re
from typing import Dict, List, Tuple, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass
import urllib.request
import ssl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deployment_validator")

# Constants
MIN_PYTHON_VERSION = (3, 8, 0)
MIN_NODE_VERSION = (14, 0, 0)
MIN_NPM_VERSION = (6, 0, 0)
MIN_DOCKER_VERSION = (20, 0, 0)
MIN_DOCKER_COMPOSE_VERSION = (2, 0, 0)
REQUIRED_PORTS = [3000, 5432, 6379, 8000, 8080, 9090]
REQUIRED_DIRECTORIES = ["data", "logs", "backups"]
REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "REDIS_URL",
    "SECRET_KEY",
    "VECTOR_DB_URL",
]
RECOMMENDED_ENV_VARS = [
    "OPENAI_API_KEY",
    "LOG_LEVEL",
    "DEBUG",
]


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    passed: bool
    message: str
    details: Optional[Any] = None
    fix_available: bool = False
    fix_command: Optional[str] = None
    severity: str = "error"  # "error", "warning", "info"


class DeploymentValidator:
    """
    Validates deployment prerequisites for Think-Tank.
    
    This class checks system requirements, dependencies, configuration,
    and permissions to ensure that the application can be deployed successfully.
    """
    
    def __init__(self, verbose: bool = False, fix: bool = False, config_file: str = ".env"):
        """
        Initialize the deployment validator.
        
def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            bool: True if all checks passed, False otherwise
        """
        logger.info("Starting deployment validation...")
        
        # System checks
        self._check_system_requirements()
        
        # Dependency checks
        self._check_python_version()
        self._check_node_version()
        self._check_npm_version()
        self._check_docker()
        self._check_docker_compose()
        self._check_required_packages()
        
        # Configuration checks
        self._check_env_file()
        self._check_env_variables()
        self._check_config_files()
        
        # Network checks
        self._check_port_availability()
        self._check_internet_connectivity()
        
        # File system checks
        self._check_directory_structure()
        self._check_file_permissions()
        self._check_disk_space()
        
        # Database checks
        self._check_database_connection()
        
        # Security checks
        self._check_secret_key()
        self._check_api_keys()
        
        # Print summary
        self._print_summary()
        
        # Return overall result
        return all(result.passed for result in self.results if result.severity == "error")
    
    def _check_system_requirements(self) -> None:
        """Check system requirements."""
        # Check CPU cores
        cpu_count = os.cpu_count() or 0
        cpu_check_passed = cpu_count >= 2
        
        self.results.append(ValidationResult(
            name="CPU Cores",
            passed=cpu_check_passed,
            message=f"System has {cpu_count} CPU cores" if cpu_check_passed else f"System has only {cpu_count} CPU cores, recommended minimum is 2",
            details={"cpu_count": cpu_count, "recommended": 2},
            severity="warning" if cpu_check_passed else "error"
        ))
        
        # Check memory
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    mem_info = f.read()
                mem_total = int(re.search(r"MemTotal:\s+(\d+)", mem_info).group(1)) // 1024  # MB
            elif platform.system() == "Darwin":  # macOS
                mem_str = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
                mem_total = int(mem_str) // (1024 * 1024)  # MB
            elif platform.system() == "Windows":
                mem_str = subprocess.check_output(["wmic", "computersystem", "get", "totalphysicalmemory"]).decode()
                mem_total = int(mem_str.split("\n")[1].strip()) // (1024 * 1024)  # MB
            else:
                mem_total = 0
                
            mem_check_passed = mem_total >= 4096  # 4 GB
            
            self.results.append(ValidationResult(
                name="Memory",
                passed=mem_check_passed,
                message=f"System has {mem_total} MB memory" if mem_check_passed else f"System has only {mem_total} MB memory, recommended minimum is 4096 MB (4 GB)",
                details={"memory_mb": mem_total, "recommended": 4096},
                severity="warning" if mem_check_passed else "error"
            ))
        except Exception as e:
            logger.error(f"Failed to check memory: {e}")
            self.results.append(ValidationResult(
                name="Memory",
                passed=False,
                message=f"Failed to check memory: {e}",
                severity="warning"
            ))
        
        # Check disk space
        try:
            disk_usage = shutil.disk_usage(self.project_root)
            disk_free_gb = disk_usage.free / (1024 * 1024 * 1024)
            disk_check_passed = disk_free_gb >= 10  # 10 GB
            
            self.results.append(ValidationResult(
                name="Disk Space",
                passed=disk_check_passed,
                message=f"System has {disk_free_gb:.2f} GB free disk space" if disk_check_passed else f"System has only {disk_free_gb:.2f} GB free disk space, recommended minimum is 10 GB",
                details={"free_space_gb": disk_free_gb, "recommended": 10},
                severity="warning" if disk_check_passed else "error"
            ))
        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")
            self.results.append(ValidationResult(
                name="Disk Space",
                passed=False,
                message=f"Failed to check disk space: {e}",
                severity="warning"
            ))
    
    def _check_python_version(self) -> None:
        """Check Python version."""
        current_version = sys.version_info[:3]
        version_str = ".".join(map(str, current_version))
        min_version_str = ".".join(map(str, MIN_PYTHON_VERSION))
        
        passed = current_version >= MIN_PYTHON_VERSION
        
        self.results.append(ValidationResult(
            name="Python Version",
            passed=passed,
            message=f"Python version {version_str} is installed" if passed else f"Python version {version_str} is installed, but {min_version_str} or higher is required",
            details={"current_version": version_str, "required_version": min_version_str},
            severity="error"
        ))
    
    def _check_node_version(self) -> None:
        """Check Node.js version."""
        try:
            node_version_str = subprocess.check_output(["node", "--version"]).decode().strip().lstrip("v")
            node_version = tuple(map(int, node_version_str.split(".")))
            min_version_str = ".".join(map(str, MIN_NODE_VERSION))
            
def _check_npm_version(self) -> None:
        """Check npm version."""
        try:
            npm_version_str = subprocess.check_output(["npm", "--version"]).decode().strip()
            npm_version = tuple(map(int, npm_version_str.split(".")))
            min_version_str = ".".join(map(str, MIN_NPM_VERSION))
            
            passed = npm_version >= MIN_NPM_VERSION
            
            self.results.append(ValidationResult(
                name="npm Version",
                passed=passed,
                message=f"npm version {npm_version_str} is installed" if passed else f"npm version {npm_version_str} is installed, but {min_version_str} or higher is required",
                details={"current_version": npm_version_str, "required_version": min_version_str},
                severity="error",
                fix_available=not passed,
                fix_command="npm install -g npm@latest"
            ))
        except (subprocess.SubprocessError, FileNotFoundError):
            self.results.append(ValidationResult(
                name="npm Version",
                passed=False,
                message=f"npm is not installed, but is required",
                fix_available=True,
                fix_command="npm install -g npm@latest",
                severity="error"
            ))
    
    def _check_docker(self) -> None:
        """Check Docker installation."""
        try:
            docker_version_str = subprocess.check_output(["docker", "--version"]).decode().strip()
            # Extract version from string like "Docker version 20.10.7, build f0df350"
            version_match = re.search(r"Docker version (\d+\.\d+\.\d+)", docker_version_str)
            if version_match:
                docker_version_str = version_match.group(1)
                docker_version = tuple(map(int, docker_version_str.split(".")))
                min_version_str = ".".join(map(str, MIN_DOCKER_VERSION))
                
                passed = docker_version >= MIN_DOCKER_VERSION
                
                self.results.append(ValidationResult(
                    name="Docker Version",
                    passed=passed,
                    message=f"Docker version {docker_version_str} is installed" if passed else f"Docker version {docker_version_str} is installed, but {min_version_str} or higher is required",
                    details={"current_version": docker_version_str, "required_version": min_version_str},
                    severity="error"
                ))
            else:
                self.results.append(ValidationResult(
                    name="Docker Version",
                    passed=False,
                    message=f"Failed to parse Docker version from: {docker_version_str}",
                    severity="error"
                ))
                
            # Check if Docker daemon is running
            subprocess.check_output(["docker", "info"])
            self.results.append(ValidationResult(
                name="Docker Daemon",
                passed=True,
                message="Docker daemon is running",
                severity="error"
            ))
        except (subprocess.SubprocessError, FileNotFoundError):
            self.results.append(ValidationResult(
                name="Docker",
                passed=False,
                message="Docker is not installed or not running",
                fix_available=True,
                fix_command="curl -fsSL https://get.docker.com | sh",
                severity="error"
            ))
    
    def _check_docker_compose(self) -> None:
        """Check Docker Compose installation."""
        try:
            # Try docker-compose v2 (part of docker CLI)
            compose_version_str = subprocess.check_output(["docker", "compose", "version"]).decode().strip()
            # Extract version from string like "Docker Compose version v2.0.0"
            version_match = re.search(r"Docker Compose version v(\d+\.\d+\.\d+)", compose_version_str)
            if version_match:
                compose_version_str = version_match.group(1)
                compose_version = tuple(map(int, compose_version_str.split(".")))
                min_version_str = ".".join(map(str, MIN_DOCKER_COMPOSE_VERSION))
                
                passed = compose_version >= MIN_DOCKER_COMPOSE_VERSION
                
                self.results.append(ValidationResult(
                    name="Docker Compose Version",
                    passed=passed,
                    message=f"Docker Compose version {compose_version_str} is installed" if passed else f"Docker Compose version {compose_version_str} is installed, but {min_version_str} or higher is required",
                    details={"current_version": compose_version_str, "required_version": min_version_str},
                    severity="error"
                ))
            else:
                self.results.append(ValidationResult(
                    name="Docker Compose Version",
                    passed=False,
                    message=f"Failed to parse Docker Compose version from: {compose_version_str}",
                    severity="error"
                ))
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                # Try standalone docker-compose
                compose_version_str = subprocess.check_output(["docker-compose", "--version"]).decode().strip()
                # Extract version from string like "docker-compose version 1.29.2, build 5becea4c"
                version_match = re.search(r"docker-compose version (\d+\.\d+\.\d+)", compose_version_str)
                if version_match:
                    compose_version_str = version_match.group(1)
                    compose_version = tuple(map(int, compose_version_str.split(".")))
                    
                    # For standalone docker-compose, we need to convert the version
                    # v1.x.y is equivalent to v1.x.y in the new versioning scheme
                    if compose_version[0] == 1:
                        passed = True
                    else:
                        passed = compose_version >= MIN_DOCKER_COMPOSE_VERSION
                    
                    min_version_str = ".".join(map(str, MIN_DOCKER_COMPOSE_VERSION))
                    
                    self.results.append(ValidationResult(
                        name="Docker Compose Version",
                        passed=passed,
                        message=f"Docker Compose version {compose_version_str} is installed" if passed else f"Docker Compose version {compose_version_str} is installed, but {min_version_str} or higher is required",
                        details={"current_version": compose_version_str, "required_version": min_version_str},
                        severity="error"
                    ))
                else:
                    self.results.append(ValidationResult(
                        name="Docker Compose Version",
                        passed=False,
                        message=f"Failed to parse Docker Compose version from: {compose_version_str}",
                        severity="error"
                    ))
            except (subprocess.SubprocessError, FileNotFoundError):
                self.results.append(ValidationResult(
                    name="Docker Compose",
                    passed=False,
                    message="Docker Compose is not installed",
def _check_required_packages(self) -> None:
        """Check required Python packages."""
        required_packages = {
            "fastapi": "0.68.0",
            "sqlalchemy": "1.4.0",
            "pydantic": "1.8.0",
            "uvicorn": "0.15.0",
            "redis": "4.0.0",
            "requests": "2.26.0",
        }
        
        for package, min_version in required_packages.items():
            try:
                # Try to import the package
                module = __import__(package)
                
                # Get the version
                if hasattr(module, "__version__"):
                    version = module.__version__
                elif hasattr(module, "VERSION"):
                    version = module.VERSION
                else:
                    version = "unknown"
                
                # Compare versions if known
                if version != "unknown":
                    current_version = tuple(map(int, version.split(".")))
                    required_version = tuple(map(int, min_version.split(".")))
                    passed = current_version >= required_version
                else:
                    passed = True  # Assume it's OK if we can't determine version
                
                self.results.append(ValidationResult(
                    name=f"Python Package: {package}",
                    passed=passed,
                    message=f"Package {package} version {version} is installed" if passed else f"Package {package} version {version} is installed, but {min_version} or higher is required",
                    details={"package": package, "current_version": version, "required_version": min_version},
                    severity="warning",
                    fix_available=not passed,
                    fix_command=f"pip install {package}>={min_version}"
                ))
            except ImportError:
                self.results.append(ValidationResult(
                    name=f"Python Package: {package}",
                    passed=False,
                    message=f"Package {package} is not installed, but is required",
                    fix_available=True,
                    fix_command=f"pip install {package}>={min_version}",
                    severity="warning"
                ))
    
    def _check_env_file(self) -> None:
        """Check if .env file exists and is valid."""
        env_file = Path(self.config_file)
        
        if not env_file.exists():
            self.results.append(ValidationResult(
                name="Environment File",
                passed=False,
                message=f"Environment file {self.config_file} does not exist",
                fix_available=True,
                fix_command=f"cp .env.example {self.config_file}",
                severity="error"
            ))
            return
        
        # Check if file is readable
        try:
            with open(env_file, "r") as f:
                env_content = f.read()
            
            self.results.append(ValidationResult(
                name="Environment File",
                passed=True,
                message=f"Environment file {self.config_file} exists and is readable",
                severity="info"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                name="Environment File",
                passed=False,
                message=f"Environment file {self.config_file} exists but is not readable: {e}",
                severity="error"
            ))
    
    def _check_env_variables(self) -> None:
        """Check if required environment variables are set."""
        env_file = Path(self.config_file)
        
        if not env_file.exists():
            return
        
        try:
            # Parse .env file
            env_vars = {}
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
            
            # Check required variables
            for var in REQUIRED_ENV_VARS:
                if var not in env_vars or not env_vars[var]:
                    self.results.append(ValidationResult(
                        name=f"Environment Variable: {var}",
                        passed=False,
                        message=f"Required environment variable {var} is not set",
                        severity="error"
                    ))
                else:
                    self.results.append(ValidationResult(
                        name=f"Environment Variable: {var}",
                        passed=True,
                        message=f"Environment variable {var} is set",
                        severity="info"
                    ))
            
            # Check recommended variables
            for var in RECOMMENDED_ENV_VARS:
                if var not in env_vars or not env_vars[var]:
                    self.results.append(ValidationResult(
                        name=f"Environment Variable: {var}",
                        passed=False,
                        message=f"Recommended environment variable {var} is not set",
                        severity="warning"
                    ))
                else:
                    self.results.append(ValidationResult(
                        name=f"Environment Variable: {var}",
                        passed=True,
                        message=f"Environment variable {var} is set",
                        severity="info"
                    ))
        except Exception as e:
            logger.error(f"Failed to parse environment file: {e}")
def _check_port_availability(self) -> None:
        """Check if required ports are available."""
        for port in REQUIRED_PORTS:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        # Port is in use
                        self.results.append(ValidationResult(
                            name=f"Port Availability: {port}",
                            passed=False,
                            message=f"Port {port} is already in use",
                            severity="warning"
                        ))
                    else:
                        # Port is available
                        self.results.append(ValidationResult(
                            name=f"Port Availability: {port}",
                            passed=True,
                            message=f"Port {port} is available",
                            severity="info"
                        ))
            except Exception as e:
                logger.error(f"Failed to check port {port}: {e}")
                self.results.append(ValidationResult(
                    name=f"Port Availability: {port}",
                    passed=False,
                    message=f"Failed to check port {port}: {e}",
                    severity="warning"
                ))
    
    def _check_internet_connectivity(self) -> None:
        """Check internet connectivity."""
        try:
            # Disable SSL certificate verification for this test
            context = ssl._create_unverified_context()
            urllib.request.urlopen("https://www.google.com", timeout=5, context=context)
            self.results.append(ValidationResult(
                name="Internet Connectivity",
                passed=True,
                message="Internet connection is available",
                severity="info"
            ))
        except Exception as e:
            logger.error(f"Failed to connect to the internet: {e}")
            self.results.append(ValidationResult(
                name="Internet Connectivity",
                passed=False,
                message=f"Failed to connect to the internet: {e}",
                severity="warning"
            ))
    
    def _check_directory_structure(self) -> None:
        """Check if required directories exist."""
        for directory in REQUIRED_DIRECTORIES:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                self.results.append(ValidationResult(
                    name=f"Directory: {directory}",
                    passed=False,
                    message=f"Required directory {directory} does not exist",
                    fix_available=True,
                    fix_command=f"mkdir -p {directory}",
                    severity="warning"
                ))
            else:
                self.results.append(ValidationResult(
                    name=f"Directory: {directory}",
                    passed=True,
                    message=f"Directory {directory} exists",
                    severity="info"
                ))
    
    def _check_file_permissions(self) -> None:
        """Check file permissions."""
        # Check if setup.sh is executable
        setup_script = self.project_root / "setup.sh"
        if setup_script.exists():
            if os.access(setup_script, os.X_OK):
                self.results.append(ValidationResult(
                    name="File Permissions: setup.sh",
                    passed=True,
                    message="setup.sh is executable",
                    severity="info"
                ))
            else:
                self.results.append(ValidationResult(
                    name="File Permissions: setup.sh",
                    passed=False,
                    message="setup.sh is not executable",
                    fix_available=True,
                    fix_command="chmod +x setup.sh",
                    severity="warning"
                ))
    
    def _check_disk_space(self) -> None:
        """Check available disk space."""
        # Already checked in _check_system_requirements
        pass
    
    def _check_database_connection(self) -> None:
        """Check database connection."""
        # This is a simplified check that just verifies if PostgreSQL is running
        try:
            # Try to connect to PostgreSQL
            subprocess.check_output(["docker", "exec", "thinktank-postgres", "pg_isready"])
            self.results.append(ValidationResult(
                name="Database Connection",
                passed=True,
                message="PostgreSQL database is running and accessible",
                severity="info"
            ))
        except (subprocess.SubprocessError, FileNotFoundError):
            self.results.append(ValidationResult(
                name="Database Connection",
                passed=False,
                message="PostgreSQL database is not running or not accessible",
                severity="warning"
            ))
    
    def _check_secret_key(self) -> None:
        """Check if SECRET_KEY is secure."""
        env_file = Path(self.config_file)
        
        if not env_file.exists():
            return
        
        try:
            # Parse .env file
            with open(env_file, "r") as f:
                env_content = f.read()
            
            # Check if SECRET_KEY is set and secure
            secret_key_match = re.search(r"SECRET_KEY\s*=\s*(.+)", env_content)
            if secret_key_match:
                secret_key = secret_key_match.group(1).strip()
                
                # Check if it's the default value
                if secret_key == "development_secret_key_change_in_production":
                    self.results.append(ValidationResult(
                        name="Secret Key",
                        passed=False,
                        message="SECRET_KEY is set to the default value, which is not secure",
                        fix_available=True,
                        fix_command="openssl rand -hex 32",
                        severity="error"
                    ))
                # Check if it's too short
                elif len(secret_key) < 32:
                    self.results.append(ValidationResult(
                        name="Secret Key",
                        passed=False,
                        message=f"SECRET_KEY is too short ({len(secret_key)} characters), should be at least 32 characters",
                        fix_available=True,
                        fix_command="openssl rand -hex 32",
                        severity="warning"
                    ))
                else:
                    self.results.append(ValidationResult(
                        name="Secret Key",
                        passed=True,
                        message="SECRET_KEY is set and secure",
                        severity="info"
                    ))
            else:
                self.results.append(ValidationResult(
                    name="Secret Key",
                    passed=False,
                    message="SECRET_KEY is not set",
                    severity="error"
                ))
        except Exception as e:
            logger.error(f"Failed to check SECRET_KEY: {e}")
            self.results.append(ValidationResult(
                name="Secret Key",
                passed=False,
                message=f"Failed to check SECRET_KEY: {e}",
                severity="error"
            ))
    
    def _check_api_keys(self) -> None:
        """Check if API keys are set."""
        env_file = Path(self.config_file)
        
        if not env_file.exists():
            return
        
        try:
            # Parse .env file
            with open(env_file, "r") as f:
                env_content = f.read()
            
            # Check if OPENAI_API_KEY is set
            openai_key_match = re.search(r"OPENAI_API_KEY\s*=\s*(.+)", env_content)
            if openai_key_match:
                openai_key = openai_key_match.group(1).strip()
                
                if openai_key == "your_openai_api_key" or not openai_key:
                    self.results.append(ValidationResult(
                        name="OpenAI API Key",
                        passed=False,
                        message="OPENAI_API_KEY is not set properly",
                        severity="warning"
                    ))
                else:
                    self.results.append(ValidationResult(
                        name="OpenAI API Key",
                        passed=True,
                        message="OPENAI_API_KEY is set",
                        severity="info"
                    ))
            else:
                self.results.append(ValidationResult(
                    name="OpenAI API Key",
                    passed=False,
                    message="OPENAI_API_KEY is not set",
                    severity="warning"
                ))
        except Exception as e:
            logger.error(f"Failed to check API keys: {e}")
            self.results.append(ValidationResult(
                name="API Keys",
                passed=False,
                message=f"Failed to check API keys: {e}",
                severity="warning"
            ))
    
    def _print_summary(self) -> None:
        """Print summary of validation results."""
        errors = [r for r in self.results if not r.passed and r.severity == "error"]
        warnings = [r for r in self.results if not r.passed and r.severity == "warning"]
        passed = [r for r in self.results if r.passed]
        
        print("\n" + "=" * 80)
        print(f"DEPLOYMENT VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal checks: {len(self.results)}")
        print(f"Passed: {len(passed)}")
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        
        if errors:
            print("\n" + "=" * 80)
            print("ERRORS (Must be fixed before deployment)")
            print("=" * 80)
            for i, result in enumerate(errors, 1):
                print(f"\n{i}. {result.name}: {result.message}")
                if result.fix_available and result.fix_command:
                    print(f"   Fix: {result.fix_command}")
        
        if warnings:
            print("\n" + "=" * 80)
            print("WARNINGS (Recommended to fix)")
            print("=" * 80)
            for i, result in enumerate(warnings, 1):
                print(f"\n{i}. {result.name}: {result.message}")
                if result.fix_available and result.fix_command:
                    print(f"   Fix: {result.fix_command}")
        
        print("\n" + "=" * 80)
        if not errors:
            print("✅ All critical checks passed! The system is ready for deployment.")
        else:
            print("❌ Some critical checks failed. Please fix the errors before deployment.")
        print("=" * 80 + "\n")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate deployment prerequisites for Think-Tank")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues automatically")
    parser.add_argument("--config", default=".env", help="Path to config file")
    
    args = parser.parse_args()
    
    validator = DeploymentValidator(
        verbose=args.verbose,
        fix=args.fix,
        config_file=args.config
    )
    
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
            self.results.append(ValidationResult(
                name="Environment Variables",
                passed=False,
                message=f"Failed to parse environment file: {e}",
                severity="error"
            ))
    
    def _check_config_files(self) -> None:
        """Check if required configuration files exist."""
        required_files = [
            "docker-compose.yml",
            "infrastructure/kong/kong.yml",
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.results.append(ValidationResult(
                    name=f"Config File: {file_path}",
                    passed=False,
                    message=f"Required configuration file {file_path} does not exist",
                    severity="error"
                ))
            else:
                self.results.append(ValidationResult(
                    name=f"Config File: {file_path}",
                    passed=True,
                    message=f"Configuration file {file_path} exists",
                    severity="info"
                ))
                    fix_available=True,
                    fix_command="pip install docker-compose",
                    severity="error"
                ))
            passed = node_version >= MIN_NODE_VERSION
            
            self.results.append(ValidationResult(
                name="Node.js Version",
                passed=passed,
                message=f"Node.js version {node_version_str} is installed" if passed else f"Node.js version {node_version_str} is installed, but {min_version_str} or higher is required",
                details={"current_version": node_version_str, "required_version": min_version_str},
                severity="error",
                fix_available=not passed,
                fix_command="curl -fsSL https://nodejs.org/dist/latest-v16.x/node-v16.x.x-linux-x64.tar.gz | tar -xz -C /usr/local --strip-components=1"
            ))
        except (subprocess.SubprocessError, FileNotFoundError):
            self.results.append(ValidationResult(
                name="Node.js Version",
                passed=False,
                message=f"Node.js is not installed, but is required",
                fix_available=True,
                fix_command="curl -fsSL https://nodejs.org/dist/latest-v16.x/node-v16.x.x-linux-x64.tar.gz | tar -xz -C /usr/local --strip-components=1",
                severity="error"
            ))
        Args:
            verbose: Whether to show detailed output for each check
            fix: Whether to attempt to fix issues automatically
            config_file: Path to the configuration file
        """
        self.verbose = verbose
        self.fix = fix
        self.config_file = config_file
        self.results: List[ValidationResult] = []
        self.project_root = Path(__file__).parent.absolute()
        
        # Set up logging
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug(f"Project root: {self.project_root}")
        logger.debug(f"Config file: {config_file}")