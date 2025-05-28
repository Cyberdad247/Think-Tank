#!/bin/bash
# setup.sh - Automated setup script for Think-Tank-IO

# Exit on error
set -e

# Create .env file
cat > .env << EOF
# Environment settings
NODE_ENV=development
DEBUG=true

# API settings
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://thinktank:thinktank123@localhost:5432/thinktank
REDIS_URL=redis://localhost:6379

# Vector DB
VECTOR_DB_URL=http://localhost:8000

# Security
SECRET_KEY=development_secret_key_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# AI Services
OPENAI_API_KEY=your_openai_api_key
EOF

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
source venv/bin/activate
pip install -r requirements.txt

# Start infrastructure services
cd ..
docker-compose up -d postgres redis chroma

# Initialize database
cd backend
source venv/bin/activate
python -c "from app.db.session import engine, Base; from app.models.models import *; Base.metadata.create_all(bind=engine)"

echo "Setup complete! You can now start development."
echo "To start the frontend: cd frontend && npm run dev"
echo "To start the backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
