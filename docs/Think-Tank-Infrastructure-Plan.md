# Think-Tank Monorepo Infrastructure and Tooling Plan

This plan outlines the steps to establish the foundational framework for the "Think-Tank" monorepo's vertical slice, focusing on essential configurations and structures rather than full implementations. Turborepo will be used as the monorepo tool.

## Overall Plan

```mermaid
graph TD
    A[Start Task] --> B{Confirm Turborepo Setup};
    B --> C[Configure JS Workspaces (npm/yarn)];
    C --> D[Configure Python Workspaces (Poetry)];
    D --> E[Create Placeholder Dockerfiles];
    E --> F[Outline Redis/Supabase Configuration];
    F --> G[Outline Vector DB Adapter Setup (Chroma)];
    G --> H[Propose Basic CI/CD Pipeline];
    H --> I[Review Plan with User];
    I --> J{Write Plan to Markdown File?};
    J -- Yes --> K[Write Plan.md];
    K --> L[Switch to Code Mode for Implementation];
    J -- No --> L;
    L --> Z[End Task];
```

## Detailed Steps

1.  **Confirm Existing Turborepo Setup**
    *   **Goal**: Verify the presence and basic configuration of `turbo.json` and `package.json` within `think-tank-monorepo` to ensure Turborepo is ready for use.
    *   **Action**: Read the contents of `think-tank-monorepo/turbo.json` and `think-tank-monorepo/package.json` to understand the existing monorepo structure and available scripts. This will inform how we integrate new services.

2.  **Setup Poetry (Python) and npm/yarn (JS) Workspaces**
    *   **Goal**: Configure the monorepo to properly manage dependencies for both Python (backend, AI agents) and JavaScript (frontend) services.
    *   **JavaScript (npm/yarn) Workspaces**:
        *   **Action**: Ensure the `package.json` in `think-tank-monorepo` is configured with a `workspaces` array that includes patterns for future frontend applications (e.g., `["apps/*", "packages/*"]`).
        *   **Action**: Create an example `apps/frontend/package.json` and `packages/ui/package.json` (placeholder for shared UI components if needed later) to demonstrate the workspace structure.
    *   **Python (Poetry) Workspaces**:
        *   **Action**: In `think-tank-monorepo/pyproject.toml`, add `tool.poetry.packages` to define Python package directories within the monorepo.
        *   **Action**: Create placeholder `pyproject.toml` files within anticipated Python service directories, such as `apps/backend/pyproject.toml` and `apps/ai-agent/pyproject.toml`. These will define the Poetry projects for each service.

3.  **Configure Dockerfiles for frontend, backend, and AI agent core services**
    *   **Goal**: Create basic placeholder Dockerfiles for each core service.
    *   **Action**: Create the directory `think-tank-monorepo/infra/docker`.
    *   **Action**: Create `think-tank-monorepo/infra/docker/Dockerfile.frontend` with a basic structure (e.g., `FROM node:alpine`, `WORKDIR /app`).
    *   **Action**: Create `think-tank-monorepo/infra/docker/Dockerfile.backend` with a basic structure (e.g., `FROM python:3.9-slim-buster`, `WORKDIR /app`).
    *   **Action**: Create `think-tank-monorepo/infra/docker/Dockerfile.ai-agent` with a basic structure (e.g., `FROM python:3.9-slim-buster`, `WORKDIR /app`).

4.  **Setup Redis and Supabase local or cloud instances for cache and persistence**
    *   **Goal**: Outline the configuration steps for connecting to Redis and Supabase.
    *   **Redis Configuration**:
        *   **Action**: Document the use of environment variables (e.g., `REDIS_HOST`, `REDIS_PORT`) for connection parameters in a conceptual `.env.example` file within `think-tank-monorepo`.
        *   **Action**: Mention local setup via Docker Compose (though not creating the full `docker-compose.yml` yet).
        *   **Action**: Outline cloud deployment considerations (e.g., managed Redis services).
    *   **Supabase Configuration**:
        *   **Action**: Document the use of environment variables (e.g., `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) in the conceptual `.env.example`.
        *   **Action**: Mention local setup using Supabase CLI and Docker (though not creating the full `docker-compose.yml` yet).
        *   **Action**: Outline cloud deployment considerations (Supabase platform).

5.  **Setup Vector DB adapter with a lightweight local vector store (Chroma)**
    *   **Goal**: Decide on a lightweight local vector store and outline its integration.
    *   **Decision**: Chroma will be used for its simplicity in local development setup.
    *   **Action**: Outline the Python code structure for a basic vector DB adapter class (e.g., `vector_db_adapter.py`) that uses Chroma, including initialization and methods for embedding and retrieval.
    *   **Action**: Mention the requirement for a `chromadb` dependency in the relevant `pyproject.toml` (e.g., `apps/ai-agent/pyproject.toml`).

6.  **Configure basic CI/CD pipeline for linting, testing, and deployment**
    *   **Goal**: Propose a basic CI/CD pipeline structure.
    *   **Action**: Create the directory `think-tank-monorepo/infra/ci-cd`.
    *   **Action**: Create a placeholder file, e.g., `think-tank-monorepo/infra/ci-cd/github-actions.yml`, with comments outlining stages for:
        *   Linting (JavaScript & Python)
        *   Testing (JavaScript & Python)
        *   Building Docker images for frontend, backend, and AI agent
        *   Deployment (conceptual steps)
    *   **Action**: Emphasize using Turborepo's `run` command for running linting/testing scripts across workspaces within the CI/CD pipeline.