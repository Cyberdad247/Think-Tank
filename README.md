# Think-Tank Monorepo

A project demonstrating a multi-agent debate system. This monorepo contains the frontend, backend, AI agent services, and supporting packages for the Think-Tank application.

## Monorepo Structure

The repository is organized as follows:

- **`apps/`**: Contains the main applications.
    - **`ai-agent/`**: Python-based application for AI agent logic and processing.
    - **`backend/`**: Python-based backend server (likely FastAPI or Flask) handling API requests and business logic.
    - **`frontend/`**: Next.js/React frontend application for the user interface.
- **`packages/`**: Contains shared libraries and utilities used across different applications.
    - **`ai-agent-core/`**: Core logic for the AI agents.
    - **`cache-queue/`**: Clients and utilities for message queuing and caching (e.g., Redis).
    - **`data-storage/`**: Modules for interacting with data storage solutions (e.g., Supabase, vector databases).
    - **`ui/`**: Shared UI components for the frontend.
- **`infra/`**: Contains infrastructure-related configurations.
    - **`ci-cd/`**: Continuous integration and deployment configurations (e.g., GitHub Actions).
    - **`docker/`**: Dockerfiles for containerizing applications.
- **`docs/`**: Contains project documentation, plans, and diagrams.

## Setup Instructions

### 1. Install Dependencies

**For Frontend (Next.js/React):**

Navigate to the frontend application directory and install dependencies using npm or yarn:
```bash
cd apps/frontend
npm install
# or
# yarn install
```

**For Backend & AI Agent (Python):**

It's recommended to use a virtual environment for Python projects.

For each Python application (`apps/backend`, `apps/ai-agent`) and Python package (`packages/*` if they have their own dependencies):
```bash
cd path/to/python_app_or_package
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt # If a requirements.txt file exists
# or if using Poetry (as indicated by pyproject.toml)
# pip install poetry
# poetry install
```
*Looking at the file structure, `pyproject.toml` exists, suggesting Poetry is used for Python dependency management.* For projects with `pyproject.toml` (likely `apps/ai-agent`, `apps/backend`, and Python-based `packages`), use Poetry:
```bash
cd path/to/python_project
pip install poetry # If you don't have poetry installed
poetry install
```
To install dependencies for all projects at once using `nx` (if configured):
```bash
npm install # Installs root dependencies and bootstraps Nx
# Further commands might be needed depending on Nx setup for Python projects
```

### 2. Set Up Environment Variables

Create a `.env` file in the root of the project or in specific application directories as needed, by copying the example file:
```bash
cp .env.example .env
```
Then, update the `.env` file with your actual credentials and configuration values. Each application or package might have its own `.env.example` or require specific variables to be set.

**Example `.env` variables (refer to `.env.example` for a complete list):**
```env
# Backend Configuration
DATABASE_URL=your_database_connection_string
API_KEY=your_api_key

# AI Agent Configuration
OPENAI_API_KEY=your_openai_api_key

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Running the Applications

### 1. Backend Server

```bash
cd apps/backend
# If using a virtual environment, activate it:
# source venv/bin/activate  # Or poetry shell
uvicorn main:app --reload --port 8000
```
*(The port is assumed to be 8000, adjust if necessary)*

### 2. Frontend Application

```bash
cd apps/frontend
npm run dev
```
The frontend will typically be available at `http://localhost:3000`.

### 3. AI Agent Service

(Assuming the AI agent runs as a separate service, specific instructions would depend on its implementation. It might be a script to run, a Celery worker, or another FastAPI app.)

Example (if it's a Python script or app started with Poetry):
```bash
cd apps/ai-agent
# If using a virtual environment, activate it:
# source venv/bin/activate # Or poetry shell
# poetry run python main.py # Or however the agent is started
```

## Running Tests

(Placeholder: Specific instructions for running tests will be added here once the testing strategy and frameworks are defined.)

Example:
```bash
# For frontend tests
cd apps/frontend
npm test

# For backend tests
cd apps/backend
# poetry run pytest # or python -m pytest
```

## Application and Package Descriptions

### Applications

-   **`apps/ai-agent`**: Manages the AI agents, their personas, and their interaction logic within the debate system. It likely handles tasks such as generating responses, processing arguments, and interacting with AI models.
-   **`apps/backend`**: Provides the core API for the Think-Tank application. It handles user authentication, data persistence, manages debate sessions, and orchestrates interactions between the frontend and the AI agents.
-   **`apps/frontend`**: The user-facing web application built with Next.js. It allows users to view debates, interact with the system, and manage their settings.

### Packages

-   **`packages/ai-agent-core`**: Contains fundamental Python modules for AI agent functionalities, such as persona definitions (`persona_system.py`) and lightweight agent implementations (`light_agent.py`).
-   **`packages/cache-queue`**: Includes Python utilities for connecting to and interacting with Redis (`redis_client.py`), used for caching and message queuing to improve performance and enable asynchronous tasks.
-   **`packages/data-storage`**: Provides Python clients for data storage solutions. This includes `supabase_client.py` for interacting with a Supabase backend and `vector_db.py` for managing and querying vector embeddings, likely for semantic search or similarity tasks.
-   **`packages/ui`**: A collection of shared React UI components used across the frontend application to ensure a consistent look and feel. It has its own `package.json` for managing dependencies.

---

This README provides a starting point. It should be updated as the project evolves.
