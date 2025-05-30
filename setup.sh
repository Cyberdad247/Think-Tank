#!/bin/bash
# Enhanced setup.sh - Automated setup script for Think-Tank-IO
# 
# Features:
# - Improved error handling and validation
# - Dependency checking
# - Environment validation
# - Colorized output
# - Progress indicators
# - Rollback on failure
# - Logging

# Exit on error, but with proper cleanup
set -o errexit
set -o pipefail
set -o nounset

# Script variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/setup.log"
ENV_FILE="${SCRIPT_DIR}/.env"
ENV_EXAMPLE_FILE="${SCRIPT_DIR}/.env.example"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${SCRIPT_DIR}/backups/${TIMESTAMP}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to log messages
log() {
  local level=$1
  local message=$2
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  echo -e "${timestamp} [${level}] ${message}" >> "${LOG_FILE}"
  
  case ${level} in
    INFO)
      echo -e "${BLUE}[INFO]${NC} ${message}"
      ;;
    SUCCESS)
      echo -e "${GREEN}[SUCCESS]${NC} ${message}"
      ;;
    WARNING)
      echo -e "${YELLOW}[WARNING]${NC} ${message}"
      ;;
    ERROR)
      echo -e "${RED}[ERROR]${NC} ${message}"
      ;;
    *)
      echo -e "[${level}] ${message}"
      ;;
  esac
}

# Function to display a spinner during long operations
spinner() {
  local pid=$1
  local message=$2
  local spin='-\|/'
  local i=0
  
  echo -ne "${CYAN}${message}${NC} "
  
  while kill -0 $pid 2>/dev/null; do
    i=$(( (i+1) % 4 ))
    echo -ne "\r${CYAN}${message}${NC} ${spin:$i:1}"
    sleep .1
  done
  
  echo -ne "\r${CYAN}${message}${NC} Done!   \n"
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check required dependencies
check_dependencies() {
  log "INFO" "Checking dependencies..."
  
  local missing_deps=()
  
  # Check for required commands
  for cmd in docker docker-compose python3 pip3 node npm; do
    if ! command_exists "$cmd"; then
      missing_deps+=("$cmd")
    fi
  done
  
  # Check Docker is running
  if command_exists docker && ! docker info >/dev/null 2>&1; then
    log "ERROR" "Docker is installed but not running. Please start Docker and try again."
    exit 1
  fi
  
  # Report missing dependencies
  if [ ${#missing_deps[@]} -ne 0 ]; then
    log "ERROR" "Missing required dependencies: ${missing_deps[*]}"
    log "ERROR" "Please install these dependencies and try again."
    exit 1
  fi
  
  log "SUCCESS" "All dependencies are installed."
}

# Function to create backup directory
create_backup() {
  log "INFO" "Creating backup directory..."
  mkdir -p "${BACKUP_DIR}"
  
  # Backup existing .env file if it exists
  if [ -f "${ENV_FILE}" ]; then
    log "INFO" "Backing up existing .env file..."
    cp "${ENV_FILE}" "${BACKUP_DIR}/.env.backup"
  fi
  
  # Backup database if it exists
  if [ -f "${SCRIPT_DIR}/thinktank.db" ]; then
    log "INFO" "Backing up existing database..."
    cp "${SCRIPT_DIR}/thinktank.db" "${BACKUP_DIR}/thinktank.db.backup"
  fi
  
  log "SUCCESS" "Backup created at ${BACKUP_DIR}"
}

# Function to restore from backup in case of failure
restore_from_backup() {
  log "WARNING" "Setup failed. Restoring from backup..."
  
  if [ -f "${BACKUP_DIR}/.env.backup" ]; then
    log "INFO" "Restoring .env file..."
    cp "${BACKUP_DIR}/.env.backup" "${ENV_FILE}"
  fi
  
  if [ -f "${BACKUP_DIR}/thinktank.db.backup" ]; then
    log "INFO" "Restoring database..."
    cp "${BACKUP_DIR}/thinktank.db.backup" "${SCRIPT_DIR}/thinktank.db"
  fi
  
  log "INFO" "Restoration complete. Please check the log file for errors: ${LOG_FILE}"
}

# Function to create .env file
create_env_file() {
  log "INFO" "Creating .env file..."
  
  # Check if .env.example exists
  if [ ! -f "${ENV_EXAMPLE_FILE}" ]; then
    log "ERROR" ".env.example file not found. Cannot create .env file."
    exit 1
  fi
  
  # Check if .env already exists and prompt for overwrite
  if [ -f "${ENV_FILE}" ]; then
    read -p "$(echo -e "${YELLOW}[WARNING]${NC} .env file already exists. Overwrite? (y/n): ")" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log "INFO" "Keeping existing .env file."
      return
    fi
  fi
  
  # Copy .env.example to .env
  cp "${ENV_EXAMPLE_FILE}" "${ENV_FILE}"
  
  # Generate a secure random key for SECRET_KEY
  local secret_key=$(openssl rand -hex 32)
  sed -i.bak "s/replace_with_strong_secret_key_in_production/${secret_key}/g" "${ENV_FILE}"
  rm -f "${ENV_FILE}.bak"
  
  # Prompt for OpenAI API key
  read -p "$(echo -e "${BLUE}[INPUT]${NC} Enter your OpenAI API key (leave blank to skip): ")" openai_key
  if [ -n "$openai_key" ]; then
    sed -i.bak "s/your_openai_api_key/${openai_key}/g" "${ENV_FILE}"
    rm -f "${ENV_FILE}.bak"
  else
    log "WARNING" "No OpenAI API key provided. Some features may not work."
  fi
  
  log "SUCCESS" ".env file created successfully."
}

# Function to install frontend dependencies
install_frontend_dependencies() {
  log "INFO" "Installing frontend dependencies..."
  
  # Check if frontend directory exists
  if [ ! -d "${SCRIPT_DIR}/frontend" ]; then
    log "ERROR" "Frontend directory not found."
    return 1
  fi
  
  # Navigate to frontend directory
  cd "${SCRIPT_DIR}/frontend"
  
  # Install dependencies with progress indicator
  npm install --no-fund --no-audit > "${LOG_FILE}.npm" 2>&1 &
  spinner $! "Installing frontend dependencies..."
  
  # Check if installation was successful
  if [ $? -ne 0 ]; then
    log "ERROR" "Failed to install frontend dependencies. Check ${LOG_FILE}.npm for details."
    return 1
  fi
  
  log "SUCCESS" "Frontend dependencies installed successfully."
  return 0
}

# Function to install backend dependencies
install_backend_dependencies() {
  log "INFO" "Installing backend dependencies..."
  
  # Check if backend directory exists
  if [ ! -d "${SCRIPT_DIR}/backend" ]; then
    log "ERROR" "Backend directory not found."
    return 1
  fi
  
  # Navigate to backend directory
  cd "${SCRIPT_DIR}/backend"
  
  # Check if virtual environment exists, create if not
  if [ ! -d "venv" ]; then
    log "INFO" "Creating virtual environment..."
    python3 -m venv venv
  fi
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Install dependencies with progress indicator
  pip install -r requirements.txt > "${LOG_FILE}.pip" 2>&1 &
  spinner $! "Installing backend dependencies..."
  
  # Check if installation was successful
  if [ $? -ne 0 ]; then
    log "ERROR" "Failed to install backend dependencies. Check ${LOG_FILE}.pip for details."
    deactivate
    return 1
  fi
  
  # Deactivate virtual environment
  deactivate
  
  log "SUCCESS" "Backend dependencies installed successfully."
  return 0
}

# Function to start infrastructure services
start_infrastructure() {
  log "INFO" "Starting infrastructure services..."
  
  # Check if docker-compose.yml exists
  if [ ! -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
    log "ERROR" "docker-compose.yml not found."
    return 1
  fi
  
  # Navigate to project root
  cd "${SCRIPT_DIR}"
  
  # Start services with progress indicator
  docker-compose up -d postgres redis chroma > "${LOG_FILE}.docker" 2>&1 &
  spinner $! "Starting infrastructure services..."
  
  # Check if services are running
  if ! docker-compose ps | grep -q "Up"; then
    log "ERROR" "Failed to start infrastructure services. Check ${LOG_FILE}.docker for details."
    return 1
  fi
  
  # Wait for services to be ready
  log "INFO" "Waiting for services to be ready..."
  sleep 5
  
  log "SUCCESS" "Infrastructure services started successfully."
  return 0
}

# Function to initialize database
initialize_database() {
  log "INFO" "Initializing database..."
  
  # Check if backend directory exists
  if [ ! -d "${SCRIPT_DIR}/backend" ]; then
    log "ERROR" "Backend directory not found."
    return 1
  fi
  
  # Navigate to backend directory
  cd "${SCRIPT_DIR}/backend"
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Run database initialization
  log "INFO" "Creating database tables..."
  python -c "from app.db.session import engine, Base; from app.models.models import *; Base.metadata.create_all(bind=engine)" > "${LOG_FILE}.db" 2>&1
  
  # Check if initialization was successful
  if [ $? -ne 0 ]; then
    log "ERROR" "Failed to initialize database. Check ${LOG_FILE}.db for details."
    deactivate
    return 1
  fi
  
  # Deactivate virtual environment
  deactivate
  
  log "SUCCESS" "Database initialized successfully."
  return 0
}

# Function to validate setup
validate_setup() {
  log "INFO" "Validating setup..."
  
  local validation_errors=0
  
  # Check if .env file exists
  if [ ! -f "${ENV_FILE}" ]; then
    log "ERROR" ".env file not found."
    validation_errors=$((validation_errors + 1))
  fi
  
  # Check if frontend dependencies are installed
  if [ ! -d "${SCRIPT_DIR}/frontend/node_modules" ]; then
    log "ERROR" "Frontend dependencies not installed."
    validation_errors=$((validation_errors + 1))
  fi
  
  # Check if backend virtual environment exists
  if [ ! -d "${SCRIPT_DIR}/backend/venv" ]; then
    log "ERROR" "Backend virtual environment not found."
    validation_errors=$((validation_errors + 1))
  fi
  
  # Check if infrastructure services are running
  if ! docker-compose ps | grep -q "Up"; then
    log "ERROR" "Infrastructure services are not running."
    validation_errors=$((validation_errors + 1))
  fi
  
  if [ $validation_errors -eq 0 ]; then
    log "SUCCESS" "Setup validation passed."
    return 0
  else
    log "ERROR" "Setup validation failed with ${validation_errors} errors."
    return 1
  fi
}

# Main setup function
main() {
  # Clear log file
  > "${LOG_FILE}"
  
  log "INFO" "Starting Think-Tank-IO setup..."
  log "INFO" "Log file: ${LOG_FILE}"
  
  # Create backup
  create_backup
  
  # Check dependencies
  check_dependencies
  
  # Create .env file
  create_env_file
  
  # Install frontend dependencies
  if ! install_frontend_dependencies; then
    log "ERROR" "Failed to install frontend dependencies."
    restore_from_backup
    exit 1
  fi
  
  # Install backend dependencies
  if ! install_backend_dependencies; then
    log "ERROR" "Failed to install backend dependencies."
    restore_from_backup
    exit 1
  fi
  
  # Start infrastructure services
  if ! start_infrastructure; then
    log "ERROR" "Failed to start infrastructure services."
    restore_from_backup
    exit 1
  fi
  
  # Initialize database
  if ! initialize_database; then
    log "ERROR" "Failed to initialize database."
    restore_from_backup
    exit 1
  fi
  
  # Validate setup
  if ! validate_setup; then
    log "WARNING" "Setup completed with validation errors. Check the log file for details: ${LOG_FILE}"
  else
    log "SUCCESS" "Setup completed successfully!"
  fi
  
  # Print next steps
  echo
  echo -e "${GREEN}=== Next Steps ===${NC}"
  echo -e "${CYAN}To start the frontend:${NC}"
  echo -e "  cd frontend && npm run dev"
  echo
  echo -e "${CYAN}To start the backend:${NC}"
  echo -e "  cd backend && source venv/bin/activate && uvicorn main:app --reload"
  echo
  echo -e "${CYAN}To stop infrastructure services:${NC}"
  echo -e "  docker-compose down"
  echo
  echo -e "${YELLOW}For more information, check the documentation.${NC}"
}

# Trap for cleanup on exit
trap 'log "ERROR" "Setup interrupted. Cleaning up..."; restore_from_backup; exit 1' INT TERM

# Run main function
main
