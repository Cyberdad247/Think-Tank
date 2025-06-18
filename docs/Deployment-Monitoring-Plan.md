## Deployment and Monitoring Strategy for Think-Tank Monorepo

This document outlines a minimal end-to-end deployment and monitoring strategy for the "Think-Tank" monorepo's vertical slice.

### 1. Containerize all services with Docker

The existing placeholder Dockerfiles provide a good starting point. For each service, we need to complete the Dockerfile by adding steps to copy application code, install dependencies, and define the entrypoint command.

**General Dockerfile Enhancements:**

*   **Copy Code:** Use `COPY . .` after setting the `WORKDIR` to copy the application code into the container. For monorepos, `COPY` commands might need to be more specific (e.g., `COPY apps/frontend /app`). Alternatively, a multi-stage build could be used to copy only the built artifacts for production images. For simplicity in a minimal setup, we can copy the entire relevant application directory.
*   **Install Dependencies:**
    *   **Frontend (Next.js):** Add `COPY package*.json ./` and `RUN npm install` or `RUN yarn install`.
    *   **Backend & AI Agents (Python/Poetry):** Add `COPY pyproject.toml poetry.lock ./` and `RUN pip install poetry && poetry install --no-root --no-dev`.
*   **Define Entrypoint/Command:** Replace placeholder `CMD` with actual commands to start the application.

**Specific Dockerfile Considerations and Build Commands:**

#### **Frontend (`think-tank-monorepo/infra/docker/Dockerfile.frontend`)**

*   **Dependencies:** `npm install` (or `yarn install`)
*   **Build Step:** `npm run build` (Next.js build)
*   **Production Server:** `npm start` (Next.js production server)
*   **Context:** The build context for this Dockerfile should be the root of the monorepo, and the `COPY` commands should be relative to that.

```dockerfile
# Use an official Node.js runtime as a parent image
FROM node:alpine AS development

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
COPY apps/frontend/package.json ./apps/frontend/
COPY packages/ui/package.json ./packages/ui/
# ... copy other package.json files for workspaces if needed

RUN npm install --prefix ./apps/frontend # Install frontend specific dependencies

# Copy the rest of the application code
COPY . .

WORKDIR /app/apps/frontend

# Build the Next.js application
RUN npm run build

FROM node:alpine AS production

WORKDIR /app

# Copy built artifacts from the development stage
COPY --from=development /app/apps/frontend/.next /app/.next
COPY --from=development /app/apps/frontend/public /app/public
COPY --from=development /app/apps/frontend/node_modules /app/node_modules # Copy only production dependencies if possible
COPY --from=development /app/apps/frontend/package.json /app/package.json

EXPOSE 3000

CMD ["npm", "start"]
```

**Build Command Example (from monorepo root):**
`docker build -f ./infra/docker/Dockerfile.frontend -t thinktank-frontend:latest .`

#### **Backend (`think-tank-monorepo/infra/docker/Dockerfile.backend`)**

*   **Dependencies:** `poetry install --no-root --no-dev`
*   **Entrypoint:** `uvicorn main:app --host 0.0.0.0 --port 8000` (assuming FastAPI `main.py`)
*   **Context:** The build context should be the monorepo root.

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

WORKDIR /app

# Install Poetry and dependencies
RUN pip install poetry
COPY poetry.lock pyproject.toml ./
COPY apps/backend/pyproject.toml ./apps/backend/
COPY packages/ai-agent-core/pyproject.toml ./packages/ai-agent-core/ # If ai-agent-core is a dependency
# ... copy other pyproject.toml/poetry.lock files for internal packages if needed

RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY . .

WORKDIR /app/apps/backend

EXPOSE 8000

# Command to run the FastAPI application
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build Command Example (from monorepo root):**
`docker build -f ./infra/docker/Dockerfile.backend -t thinktank-backend:latest .`

#### **AI Agent (`think-tank-monorepo/infra/docker/Dockerfile.ai-agent`)**

*   **Dependencies:** `poetry install --no-root --no-dev`
*   **Entrypoint:** This will likely be a Celery worker command, e.g., `celery -A tasks worker --loglevel=info`
*   **Context:** The build context should be the monorepo root.

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

WORKDIR /app

# Install Poetry and dependencies
RUN pip install poetry
COPY poetry.lock pyproject.toml ./
COPY apps/backend/pyproject.toml ./apps/backend/
COPY apps/ai-agent/pyproject.toml ./apps/ai-agent/ # If ai-agent is a separate package
COPY packages/ai-agent-core/pyproject.toml ./packages/ai-agent-core/ # If ai-agent-core is a dependency
# ... copy other pyproject.toml/poetry.lock files for internal packages if needed

RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY . .

WORKDIR /app/apps/backend # Assuming tasks.py is in the backend app

EXPOSE 8001 # This port is likely for internal communication or metrics if any

# Command to run the Celery worker for AI agents
CMD ["poetry", "run", "celery", "-A", "tasks", "worker", "--loglevel=info"]
```

**Build Command Example (from monorepo root):**
`docker build -f ./infra/docker/Dockerfile.ai-agent -t thinktank-ai-agent:latest .`

### 2. Deploy frontend on Vercel

Vercel is well-suited for Next.js applications, even within a monorepo.

*   **Monorepo Configuration:** Vercel automatically detects monorepos and allows specifying the "Root Directory" for each project. For `think-tank-monorepo/apps/frontend`, the root directory would be `/apps/frontend`.
*   **Build Command:** Vercel usually detects this automatically for Next.js, but it can be explicitly set to `npm run build` or `yarn build`.
*   **Output Directory:** Similarly, Vercel detects `.next` for Next.js.
*   **Environment Variables:** Configure environment variables (e.g., `NEXT_PUBLIC_BACKEND_API_URL`) directly in the Vercel project settings.
*   **Git Integration:** Connect the monorepo GitHub repository to Vercel. Vercel will automatically deploy new commits to the specified "Root Directory".
*   **Custom Domains:** Easily configurable within Vercel.

**Vercel Project Setup Steps:**

1.  Import Git Repository: Select the `think-tank-monorepo` repository.
2.  Configure Root Directory: For the frontend project, set the "Root Directory" to `apps/frontend`.
3.  Environment Variables: Add any necessary environment variables.
4.  Deploy: Vercel will build and deploy the application.

### 3. Deploy backend and AI agents on Google Cloud Run

Google Cloud Run is an excellent choice for stateless containerized services like FastAPI and Celery workers, offering auto-scaling and pay-per-use billing.

#### **Backend (FastAPI)**

*   **Service Name:** e.g., `thinktank-backend`
*   **Container Image:** Use the Docker image built in step 1 (e.g., `gcr.io/your-project-id/thinktank-backend:latest`).
*   **Port:** Configure Cloud Run to expect traffic on port 8000 (matching `EXPOSE 8000` in Dockerfile).
*   **Environment Variables:**
    *   Database connection strings (`DATABASE_URL`)
    *   Redis connection string (`REDIS_URL`) for Celery broker
    *   Any API keys for external services
    *   These should be managed as Cloud Run environment variables or ideally using Secret Manager.
*   **Service Account:** Assign a dedicated service account with minimal necessary permissions (e.g., `roles/datastore.user` if using Datastore, `roles/secretmanager.secretAccessor`).
*   **Scaling:**
    *   **Min Instances:** Set to 0 for cost optimization, allowing it to scale down to zero when idle.
    *   **Max Instances:** Configure based on expected load.
    *   **Concurrency:** Number of concurrent requests per container instance. Default is 80, but fine-tune based on application performance characteristics.
*   **Ingress Control:** Allow all traffic (default) or restrict to internal load balancers/VPC for private APIs.
*   **Authentication:** For internal communication, use Cloud Run's built-in IAM authentication (e.g., for frontend to backend calls, the Vercel frontend would need to be configured to authenticate to Cloud Run, or the backend should be publicly accessible if not sensitive).

**Deployment Command Example:**

```bash
gcloud run deploy thinktank-backend \
  --image gcr.io/your-project-id/thinktank-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 512Mi \
  --set-env-vars DATABASE_URL="...",REDIS_URL="..." \
  --service-account your-backend-service-account@your-project-id.iam.gserviceaccount.com
```

#### **AI Agents (Celery Workers)**

*   **Service Name:** e.g., `thinktank-ai-agent-worker`
*   **Container Image:** Use the Docker image built in step 1 (e.g., `gcr.io/your-project-id/thinktank-ai-agent:latest`).
*   **Port:** While the Dockerfile exposes a port, Celery workers typically don't serve HTTP traffic. Cloud Run requires an exposed port, but it won't be used for external access. The port can be `8080` (Cloud Run's default expected port) or any other, as long as it's exposed in the Dockerfile.
*   **Environment Variables:**
    *   `REDIS_URL` (for Celery broker and result backend)
    *   `CELERY_BROKER_URL`
    *   `CELERY_RESULT_BACKEND`
    *   Any API keys for AI models (e.g., OpenAI API key)
    *   Managed via Cloud Run environment variables or Secret Manager.
*   **Service Account:** Dedicated service account with permissions for AI APIs, data storage (if agents interact directly with databases), and Secret Manager.
*   **Scaling:**
    *   **Min Instances:** Set to 0 to save costs when no tasks are queued.
    *   **Max Instances:** Based on expected task concurrency and processing requirements.
    *   **Concurrency:** This refers to HTTP requests per instance. For Celery workers, it's less relevant, but still set it. Cloud Run is designed for HTTP requests, so triggering Celery workers might involve HTTP endpoints (e.g., a backend endpoint that enqueues tasks and signals Cloud Run to scale up the worker service if min instances is 0). A better pattern for event-driven workers on Cloud Run is often to use Pub/Sub subscriptions or Cloud Tasks to trigger the worker.
        *   **Recommendation:** For a minimal setup, rely on the backend to enqueue tasks to Redis. Cloud Run's auto-scaling will bring up instances when tasks are processed, assuming the worker picks them up. For more robust event-driven scaling, consider Cloud Tasks.
*   **Background Processing with Cloud Run:** Cloud Run is designed for stateless, request-driven services. Long-running background tasks (like some AI agent processes) can be challenging.
    *   **Timeout:** Increase the request timeout for tasks that might run for several minutes (up to 60 minutes).
    *   **CPU Allocation:** Set CPU to "Always allocated" if tasks are truly long-running and require consistent CPU, otherwise "CPU is only allocated during request processing" might lead to throttling.
    *   **Task Queues:** The use of Celery and Redis is appropriate for task queuing. The Cloud Run worker instances will pull tasks from Redis.

**Deployment Command Example:**

```bash
gcloud run deploy thinktank-ai-agent-worker \
  --image gcr.io/your-project-id/thinktank-ai-agent:latest \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --port 8080 \
  --min-instances 0 \
  --max-instances 5 \
  --cpu 1 \
  --memory 1Gi \
  --set-env-vars REDIS_URL="...",OPENAI_API_KEY="..." \
  --service-account your-ai-agent-service-account@your-project-id.iam.gserviceaccount.com \
  --timeout 300 # 5 minutes for long-running tasks
```

**Mermaid Diagram: Deployment Overview**

```mermaid
graph TD
    User --> Vercel (Frontend)
    Vercel --> GoogleCloudRunBackend(Google Cloud Run: FastAPI Backend)
    GoogleCloudRunBackend --> Redis(Redis Instance - Celery Broker)
    GoogleCloudRunBackend --> ExternalAPIs(External APIs e.g., AI Models)
    Redis --> GoogleCloudRunAIAgent(Google Cloud Run: AI Agent Worker)
    GoogleCloudRunAIAgent --> ExternalAPIs
    GoogleCloudRunBackend --> Supabase(Supabase/Vector DB)
    GoogleCloudRunAIAgent --> Supabase
```

### 4. Setup logging and metrics collection for streaming and agent workflows

We'll leverage Google Cloud's native logging and monitoring services for a basic setup.

*   **Google Cloud Logging (formerly Stackdriver Logging):**
    *   **Automatic Ingestion:** Cloud Run automatically streams container logs (stdout/stderr) to Cloud Logging. No specific configuration needed within the application, just ensure applications log to stdout/stderr.
    *   **Structured Logging:** Encourage structured logging (e.g., JSON format) within FastAPI and Celery applications for easier parsing and querying in Cloud Logging. Python's `logging` module can be configured to output JSON.
    *   **Log Explorer:** Use the Google Cloud Console's Log Explorer to view, filter, and analyze logs.
*   **Basic Application Metrics (Cloud Monitoring):**
    *   **Built-in Metrics:** Cloud Run provides out-of-the-box metrics like request count, latency, CPU utilization, memory utilization, and instance count. These are visible in Cloud Monitoring.
    *   **Custom Metrics (Optional for minimal):** For more granular application-specific metrics (e.g., agent processing time, number of tasks processed), consider instrumenting the application with a client library that pushes metrics to Cloud Monitoring (e.g., OpenCensus/OpenTelemetry for Python, or a simple HTTP endpoint that Cloud Monitoring can scrape). For this *minimal* outline, we'll rely on built-in metrics and structured logs.
    *   **Celery Metrics:** Celery can emit events that can be captured and converted into metrics. For a minimal setup, relying on log parsing for success/failure rates might suffice.

**Logging and Metrics Strategy:**

1.  **Application Logging:** All services (Frontend, Backend, AI Agents) should log critical information, errors, and warnings to their standard output (stdout/stderr).
2.  **Cloud Run Integration:** Cloud Run will automatically collect these logs and send them to Google Cloud Logging.
3.  **Vercel Analytics/Logs:** Vercel also provides built-in logging and analytics for the frontend.
4.  **Monitoring Dashboards:** Utilize default dashboards in Cloud Monitoring for Cloud Run services. Create custom log queries in Cloud Logging for specific insights (e.g., "errors related to AI agent").

### 5. Setup alerting for errors and failures

Leverage Google Cloud Monitoring for basic alerting.

*   **Alerting Policies (Cloud Monitoring):**
    *   **Error Rate:** Create an alert if the HTTP error rate (e.g., 5xx errors) for the backend service exceeds a certain threshold over a period (e.g., >5% for 5 minutes).
    *   **Latency:** Alert if P99 latency for backend requests exceeds a threshold (e.g., >1 second for 10 minutes).
    *   **Resource Utilization:** Alert if CPU or memory utilization of Cloud Run instances (backend or AI agent) consistently stays high (e.g., >80% for 15 minutes), indicating potential scaling issues or performance bottlenecks.
    *   **No Healthy Instances:** Alert if the number of healthy instances for a service drops to zero (or below a configured minimum).
*   **Log-Based Metrics and Alerts:**
    *   Create log-based metrics in Cloud Logging to count specific error messages (e.g., "AI_AGENT_FAILURE", "DATABASE_CONNECTION_ERROR").
    *   Create alerts based on these log-based metrics exceeding a threshold. This is crucial for agent workflows where errors might not manifest as HTTP 5xx.
*   **Notification Channels:** Configure notification channels in Cloud Monitoring (e.g., Email, Slack, PagerDuty, Pub/Sub).

**Alerting Strategy:**

1.  **Critical Service Alerts:**
    *   Backend: High HTTP error rate, high latency, zero healthy instances.
    *   AI Agent: High CPU/memory utilization, zero healthy instances.
2.  **Application-Specific Alerts (Log-based):**
    *   Backend: Specific database connection errors, unhandled exceptions.
    *   AI Agent: Failure to process tasks, external API call failures (e.g., to OpenAI).
3.  **Notification:** Send alerts to a designated team email or chat channel.

**Mermaid Diagram: Monitoring and Alerting Flow**

```mermaid
graph TD
    Service(Application Services) --> StdoutStderr(Stdout/Stderr Logs)
    StdoutStderr --> GoogleCloudLogging(Google Cloud Logging)
    GoogleCloudLogging --> LogBasedMetrics(Log-Based Metrics)
    GoogleCloudLogging --> LogExplorer(Log Explorer & Analysis)

    Service --> CloudRunMetrics(Cloud Run Built-in Metrics)
    CloudRunMetrics --> GoogleCloudMonitoring(Google Cloud Monitoring)

    LogBasedMetrics --> GoogleCloudMonitoring
    GoogleCloudMonitoring --> AlertingPolicy(Alerting Policies)
    AlertingPolicy --> NotificationChannels(Email, Slack, PagerDuty)