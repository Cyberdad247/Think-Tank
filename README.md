# Think-Tank

A hybrid system that combines task management functionality with advanced AI research capabilities, leveraging RAG (Retrieval-Augmented Generation) and agentic planning.

## Project Overview

Think-Tank serves as both:
1. A structured task management platform with features for creating, organizing, and tracking tasks
2. An advanced AI research assistant leveraging RAG and agentic capabilities

This dual nature allows Think-Tank to provide intelligent assistance while maintaining a structured approach to organizing information and workflows.

## Architecture

The Think-Tank architecture follows a layered approach:

- **Frontend Layer**: React and Next.js with component-based architecture
- **Backend Layer**: Python with FastAPI
- **AI Core Services**: RAG Engine, Agentic Parser, Workflow Manager, Vector Search
- **Data Layer**: PostgreSQL, Redis, Chroma Vector DB
- **Infrastructure**: Docker, Kong API Gateway

## Technology Stack

### Frontend Technologies
- Next.js
- React
- TypeScript
- react-beautiful-dnd

### Backend Technologies
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

### AI and ML Technologies
- LangChain
- OpenAI API
- ChromaDB

### Database Technologies
- PostgreSQL
- Redis
- Chroma Vector DB

### Infrastructure Technologies
- Docker
- Kong API Gateway
- Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js and npm
- Python 3.9+

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/think-tank.git
   cd think-tank
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Start the development server:
   ```bash
   # For backend
   cd backend
   uvicorn main:app --reload
   
   # For frontend
   cd frontend
   npm run dev
   ```

## Project Structure

```
think-tank/
├── api.py                      # API endpoints
├── agentic_parser.py           # Agentic parsing logic
├── caching.py                  # Caching implementation
├── config.py                   # Configuration settings
├── database_optimizations.py   # Database optimization utilities
├── deployment_validator.py     # Deployment validation tools
├── docker-compose.yml          # Docker Compose configuration
├── docker-compose.enhanced.yml # Enhanced Docker Compose configuration
├── feedback_collector.tsx      # Feedback collection component
├── integrated_solution.md      # Integration documentation
├── kong.yml                    # Kong API Gateway configuration
├── main.py                     # Main application entry point
├── models.py                   # Database models
├── page.tsx                    # Main page component
├── rag_engine.py               # RAG Engine implementation
├── requirements.txt            # Python dependencies
├── schemas.py                  # Pydantic schemas
├── secrets_manager.py          # Secrets management utilities
├── security.py                 # Security utilities
├── session.py                  # Session management
├── setup.sh                    # Setup script
├── task_service.py             # Task service implementation
├── task.py                     # Task model
├── TaskChecklist.tsx           # Task checklist component
├── TaskContext.tsx             # Task context provider
├── TaskDashboard.tsx           # Task dashboard component
├── TaskForm.tsx                # Task form component
├── TaskItem.tsx                # Task item component
├── tasks.py                    # Task utilities
├── test_tasks.py               # Task tests
├── vector_search.py            # Vector search implementation
├── vector_search_enhanced.py   # Enhanced vector search
└── workflow_manager.py         # Workflow management
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the terms of the license included in the repository.
