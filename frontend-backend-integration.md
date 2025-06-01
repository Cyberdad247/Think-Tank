# Frontend-Backend Integration in Think-Tank

This document explains how the frontend and backend components integrate in the Think-Tank project, providing a comprehensive reference for developers working on the system.

## 1. System Overview

Think-Tank uses a hybrid architecture with the following key components:

- **Frontend**: Next.js application using the App Router
- **Backend**: 
  - Next.js API routes for frontend-specific concerns
  - FastAPI backend for complex business logic
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth
- **Vector Search**: ChromaDB for vector embeddings and search

```mermaid
graph TD
    Client[Client Browser] --> NextJS[Next.js Frontend]
    NextJS --> NextAPI[Next.js API Routes]
    NextJS --> FastAPI[FastAPI Backend]
    NextAPI --> Supabase[(Supabase)]
    FastAPI --> Supabase
    
    subgraph "Frontend Layer"
        NextJS
    end
    
    subgraph "API Layer"
        NextAPI
        FastAPI
    end
    
    subgraph "Data Layer"
        Supabase
    end
```

## 2. API Proxying Configuration

The Next.js application is configured to proxy certain API requests to the FastAPI backend. This is done through the `next.config.js` file:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // The App Router is now the default in Next.js 14, so we don't need the experimental flag
  // Configure rewrites to proxy API requests to the FastAPI backend in development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.BACKEND_URL || 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```

This configuration:
- Intercepts requests to `/api/:path*`
- Forwards them to the FastAPI backend at `process.env.BACKEND_URL` or `http://localhost:8000/api/:path*` if the environment variable is not set
- Allows the frontend to communicate with the backend without dealing with CORS issues
- Provides a unified API namespace for the client

## 3. Frontend Implementation

### 3.1 Next.js App Structure

The frontend uses Next.js with the App Router architecture, which provides:
- File-based routing
- Server Components
- Client Components
- API Routes

Key frontend files and directories:
- `app/page.tsx`: Main application page
- `app/layout.tsx`: Root layout component
- `app/api/`: API routes
- `components/`: Reusable UI components
- `utils/`: Utility functions, including Supabase client

### 3.2 API Calls to Backend

The frontend makes API calls in several ways:

1. **Direct Supabase Client Calls**: For simple database operations and authentication
   ```typescript
   // Example from a client component
   import { supabase } from '@/utils/supabase';
   
   // Fetch tasks
   const { data, error } = await supabase
     .from('tasks')
     .select('*')
     .order('order_position', { ascending: true });
   ```

2. **Next.js API Routes**: For operations that require server-side logic
   ```typescript
   // Example client-side fetch to a Next.js API route
   const response = await fetch('/api/tasks', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ title: 'New Task' }),
   });
   ```

3. **FastAPI Backend Calls**: For complex business logic (via Next.js API proxy)
   ```typescript
   // This call will be proxied to the FastAPI backend
   const response = await fetch('/api/vector-search', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ query: 'search term' }),
   });
   ```

### 3.3 Authentication in the Frontend

Authentication is handled using Supabase Auth:

```typescript
// Sign in example
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123',
});

// Get current session
const { data: { session } } = await supabase.auth.getSession();
```

## 4. Backend API Structure

### 4.1 Next.js API Routes

Next.js API routes handle frontend-specific concerns like authentication and direct Supabase database access. These routes are located in the `app/api/` directory.

Example API route for tasks:

```typescript
// app/api/tasks/route.ts
export async function GET(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Query tasks
    const { data: tasks, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('user_id', session.user.id)
      .order('order_position', { ascending: true });
    
    if (error) {
      console.error('Error fetching tasks:', error);
      return NextResponse.json({ error: 'Failed to fetch tasks' }, { status: 500 });
    }
    
    return NextResponse.json(tasks);
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

### 4.2 FastAPI Backend

The FastAPI backend handles more complex business logic. It's structured as follows:

- `main.py`: Application entry point
- `api.py`: API router configuration
- `models/`: Database models
- `schemas/`: Pydantic schemas for validation
- `services/`: Business logic services

Example FastAPI endpoint:

```python
# From FastAPI backend
@router.get("/tasks/", response_model=List[schemas.Task])
def read_tasks(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all tasks for the current user"""
    tasks = task_service.get_tasks(db, skip=skip, limit=limit, user_id=current_user.id)
    return tasks
```

## 5. Authentication Flow

Authentication is handled by Supabase Auth and integrated across both frontend and backend:

1. **User Authentication**:
   - User signs in via the frontend using Supabase Auth
   - Supabase returns a JWT token
   - Token is stored in cookies

2. **Frontend Authentication**:
   - Next.js API routes use `createRouteHandlerClient` to access the authenticated Supabase client
   - Session is verified on each request

   ```typescript
   // In Next.js API route
   const supabase = createRouteHandlerClient({ cookies });
   const { data: { session } } = await supabase.auth.getSession();
   if (!session) {
     return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
   }
   ```

3. **Backend Authentication**:
   - FastAPI backend validates the JWT token
   - User information is extracted from the token
   - Authorization is enforced based on user roles and permissions

## 6. Data Flow

The data flow between frontend and backend follows these patterns:

1. **Simple Data Operations**:
   - Frontend components directly use the Supabase client
   - Data is fetched, created, updated, or deleted directly in the database
   - Real-time subscriptions can be set up for live updates

2. **Complex Operations**:
   - Frontend makes requests to Next.js API routes
   - API routes either:
     - Handle the request directly using Supabase
     - Proxy the request to the FastAPI backend
   - Response is returned to the frontend

3. **State Management**:
   - Local component state for UI-specific state
   - React Context for shared application state
   - Supabase for persistent data storage

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant Next as Next.js Frontend
    participant NextAPI as Next.js API Routes
    participant FastAPI as FastAPI Backend
    participant Supabase as Supabase Database
    
    Client->>Next: User Interaction
    
    alt Simple Data Operation
        Next->>Supabase: Direct Supabase Client Call
        Supabase-->>Next: Data Response
    else Next.js API Operation
        Next->>NextAPI: API Request
        NextAPI->>Supabase: Database Operation
        Supabase-->>NextAPI: Data Response
        NextAPI-->>Next: API Response
    else Complex Operation
        Next->>NextAPI: API Request
        NextAPI->>FastAPI: Proxy Request
        FastAPI->>Supabase: Database Operation
        Supabase-->>FastAPI: Data Response
        FastAPI-->>NextAPI: API Response
        NextAPI-->>Next: API Response
    end
    
    Next-->>Client: UI Update
```

## 7. Supabase Integration

Supabase is the primary database for the entire application and provides authentication services.

### 7.1 Supabase Client Setup

The Supabase client is initialized in `utils/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js';

// Initialize the Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Create a single supabase client for the browser
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Helper function to get authenticated supabase client on the server
export const getServerSupabaseClient = async () => {
  const { createServerClient } = await import('@supabase/auth-helpers-nextjs');
  const { cookies } = await import('next/headers');
  
  const cookieStore = cookies();
  
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
    {
      cookies: {
        get: (name) => cookieStore.get(name)?.value,
        set: (name, value, options) => {
          cookieStore.set({ name, value, ...options });
        },
        remove: (name, options) => {
          cookieStore.set({ name, value: '', ...options });
        },
      },
    }
  );
};
```

### 7.2 Database Schema

The Supabase database includes tables for:
- Users
- Tasks
- Knowledge items
- TAL blocks
- Debates

These are defined with TypeScript types in `utils/supabase.ts`:

```typescript
// Types for Supabase tables
export type Tables = {
  users: {
    Row: {
      id: string;
      email: string;
      created_at: string;
      is_active: boolean;
    };
    // ...
  };
  tasks: {
    Row: {
      id: string;
      title: string;
      description: string;
      completed: boolean;
      order_position: number;
      user_id: string;
      created_at: string;
      updated_at: string;
      completed_at?: string;
      due_date?: string;
      priority?: 'none' | 'low' | 'medium' | 'high';
      tags?: string[];
    };
    // ...
  };
  // Other tables...
};
```

### 7.3 FastAPI Connection to Supabase

The FastAPI backend connects to the same Supabase PostgreSQL instance when needed for complex operations. This is configured in the database session setup:

```python
# session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()
```

## 8. Environment Configuration

The application uses environment variables for configuration, with separate files for different environments.

### 8.1 Frontend Environment Variables

Frontend environment variables are defined in `.env.local`:

```
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# OpenAI API Key (for embeddings and AI features)
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_MODEL=gpt-4

# Application Settings
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 8.2 Backend Environment Variables

Backend environment variables are defined in `.env`:

```
# Environment settings
NODE_ENV=development
DEBUG=false

# API settings
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/thinktank
REDIS_URL=redis://localhost:6379

# Vector DB
VECTOR_DB_URL=http://localhost:8000
VECTOR_DB_PERSIST_DIRECTORY=./vector_db

# Security
SECRET_KEY=replace_with_strong_secret_key_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=11520
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# AI Services
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-opus-20240229

# Caching
CACHE_TTL=3600
CACHE_ENABLED=true
CACHE_STRATEGY=multi_level

# Resource Limits
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT_SECONDS=30
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD_SECONDS=60

# Monitoring
ENABLE_TELEMETRY=false
LOG_LEVEL=info

# Feature Flags
ENABLE_ADVANCED_ANALYTICS=false
ENABLE_USER_FEEDBACK=true
```

## 9. Development Workflow

When developing features for Think-Tank, follow these guidelines:

1. **Frontend-Only Features**:
   - Implement directly in the Next.js frontend
   - Use the Supabase client for data access
   - Create components in the `components/` directory

2. **Simple API Features**:
   - Implement in Next.js API routes
   - Use the Supabase client for database operations
   - Handle authentication and validation

3. **Complex Business Logic**:
   - Implement in the FastAPI backend
   - Create appropriate models, schemas, and services
   - Expose endpoints through the API router
   - Access from the frontend via the API proxy

4. **Database Changes**:
   - Update the Supabase schema
   - Update TypeScript types in `utils/supabase.ts`
   - Update any affected models in the FastAPI backend

## 10. Error Handling and Logging

Error handling and logging are critical aspects of the Think-Tank architecture, ensuring that issues can be identified, debugged, and resolved efficiently.

### 10.1 Frontend Error Handling

In the frontend, errors are handled at multiple levels:

1. **Component-Level Error Boundaries**:
   React error boundaries catch JavaScript errors in the component tree:

   ```tsx
   // components/ErrorBoundary.tsx
   import React, { Component, ErrorInfo, ReactNode } from 'react';
   
   interface Props {
     children: ReactNode;
     fallback?: ReactNode;
   }
   
   interface State {
     hasError: boolean;
     error?: Error;
   }
   
   export class ErrorBoundary extends Component<Props, State> {
     constructor(props: Props) {
       super(props);
       this.state = { hasError: false };
     }
   
     static getDerivedStateFromError(error: Error): State {
       return { hasError: true, error };
     }
   
     componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
       console.error("Uncaught error:", error, errorInfo);
       // Log to monitoring service
     }
   
     render(): ReactNode {
       if (this.state.hasError) {
         return this.props.fallback || (
           <div className="error-container">
             <h2>Something went wrong</h2>
             <p>{this.state.error?.message}</p>
           </div>
         );
       }
   
       return this.props.children;
     }
   }
   ```

2. **API Request Error Handling**:
   Errors from API requests are caught and handled appropriately:

   ```tsx
   // Example of API error handling in a component
   const fetchTasks = async () => {
     setLoading(true);
     setError(null);
     
     try {
       const response = await fetch('/api/tasks');
       
       if (!response.ok) {
         const errorData = await response.json();
         throw new Error(errorData.error || 'Failed to fetch tasks');
       }
       
       const data = await response.json();
       setTasks(data);
     } catch (err) {
       setError(err instanceof Error ? err.message : 'An unknown error occurred');
       // Log error to monitoring service
     } finally {
       setLoading(false);
     }
   };
   ```

3. **Supabase Error Handling**:
   Errors from Supabase operations are handled explicitly:

   ```tsx
   const createTask = async (title: string) => {
     const { data, error } = await supabase
       .from('tasks')
       .insert({ title, user_id: userId })
       .select()
       .single();
     
     if (error) {
       console.error('Error creating task:', error);
       toast.error(`Failed to create task: ${error.message}`);
       return null;
     }
     
     return data;
   };
   ```

### 10.2 Next.js API Route Error Handling

Next.js API routes use structured error handling:

```typescript
// app/api/tasks/route.ts
export async function GET(request: NextRequest) {
  try {
    // API logic here
  } catch (error) {
    console.error('Unexpected error:', error);
    
    // Determine error type and return appropriate response
    if (error instanceof AuthError) {
      return NextResponse.json(
        { error: 'Authentication failed', details: error.message },
        { status: 401 }
      );
    } else if (error instanceof ValidationError) {
      return NextResponse.json(
        { error: 'Validation failed', details: error.message },
        { status: 400 }
      );
    }
    
    // Generic error
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### 10.3 FastAPI Backend Error Handling

The FastAPI backend uses exception handlers and Pydantic validation:

```python
# Exception handlers in FastAPI
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

class DatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message

@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=500,
        content={"error": "Database error", "detail": exc.message},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the error
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
```

### 10.4 Logging Strategy

The application uses a multi-level logging strategy:

1. **Frontend Logging**:
   - Console logging during development
   - Error tracking service in production (e.g., Sentry)
   - Performance monitoring

2. **Next.js API Route Logging**:
   - Structured logging with request details
   - Error logging with stack traces
   - Request/response logging for debugging

3. **FastAPI Backend Logging**:
   - Configured through the settings module
   - Different log levels based on environment
   - Structured JSON logging in production

   ```python
   # Logging configuration in FastAPI
   import logging
   from app.core.config import settings
   
   # Configure logging
   log_level = getattr(logging, settings.LOG_LEVEL.upper())
   logging.basicConfig(
       level=log_level,
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
   )
   
   logger = logging.getLogger("app")
   ```

### 10.5 Error Propagation

Errors are propagated through the system as follows:

1. **Database Errors**:
   - Captured at the data access layer
   - Transformed into application-specific exceptions
   - Propagated to the API layer

2. **API Errors**:
   - Transformed into appropriate HTTP responses
   - Include error codes and messages
   - Sanitized to avoid exposing sensitive information

3. **Frontend Errors**:
   - Displayed to users in a friendly format
   - Logged for debugging
   - May trigger retry mechanisms when appropriate

## 11. Frontend Component Examples

This section provides more detailed examples of how frontend components interact with the API.

### 11.1 Task List Component with Loading, Error States, and Pagination

```tsx
// components/TaskList.tsx
import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabase';
import { Task } from '@/types';

export default function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const limit = 10;
  
  const fetchTasks = async (pageNum: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const skip = (pageNum - 1) * limit;
      
      // Option 1: Direct Supabase query
      const { data, error } = await supabase
        .from('tasks')
        .select('*')
        .order('order_position', { ascending: true })
        .range(skip, skip + limit - 1);
      
      if (error) throw new Error(error.message);
      
      // Option 2: Using Next.js API route
      // const response = await fetch(`/api/tasks?skip=${skip}&limit=${limit}`);
      // if (!response.ok) {
      //   const errorData = await response.json();
      //   throw new Error(errorData.error || 'Failed to fetch tasks');
      // }
      // const data = await response.json();
      
      setTasks(pageNum === 1 ? data : [...tasks, ...data]);
      setHasMore(data.length === limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchTasks(page);
  }, [page]);
  
  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(page + 1);
    }
  };
  
  if (error) {
    return (
      <div className="error-container">
        <p>Error: {error}</p>
        <button onClick={() => fetchTasks(page)}>Retry</button>
      </div>
    );
  }
  
  return (
    <div className="task-list">
      <h2>Your Tasks</h2>
      
      {tasks.length === 0 && !loading ? (
        <p>No tasks found. Create your first task!</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id} className={task.completed ? 'completed' : ''}>
              <h3>{task.title}</h3>
              <p>{task.description}</p>
              <div className="task-meta">
                <span>Priority: {task.priority || 'none'}</span>
                {task.due_date && <span>Due: {new Date(task.due_date).toLocaleDateString()}</span>}
              </div>
            </li>
          ))}
        </ul>
      )}
      
      {loading && <div className="loading-spinner">Loading...</div>}
      
      {hasMore && !loading && (
        <button onClick={loadMore} className="load-more-button">
          Load More
        </button>
      )}
    </div>
  );
}
```

### 11.2 Task Form with Validation and Submission

```tsx
// components/TaskForm.tsx
import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface FormData {
  title: string;
  description: string;
  priority: 'none' | 'low' | 'medium' | 'high';
  due_date: string;
}

export default function TaskForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    priority: 'none',
    due_date: '',
  });
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  const validateForm = (): boolean => {
    const newErrors: Partial<FormData> = {};
    
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    
    if (formData.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setSubmitting(true);
    setSubmitError(null);
    
    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create task');
      }
      
      // Success - redirect or update UI
      router.push('/tasks');
      router.refresh(); // Refresh the current route
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setSubmitting(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="task-form">
      <h2>Create New Task</h2>
      
      {submitError && (
        <div className="error-message">{submitError}</div>
      )}
      
      <div className="form-group">
        <label htmlFor="title">Title *</label>
        <input
          type="text"
          id="title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          disabled={submitting}
        />
        {errors.title && <span className="error">{errors.title}</span>}
      </div>
      
      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          disabled={submitting}
          rows={4}
        />
        {errors.description && <span className="error">{errors.description}</span>}
      </div>
      
      <div className="form-group">
        <label htmlFor="priority">Priority</label>
        <select
          id="priority"
          name="priority"
          value={formData.priority}
          onChange={handleChange}
          disabled={submitting}
        >
          <option value="none">None</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="due_date">Due Date</label>
        <input
          type="date"
          id="due_date"
          name="due_date"
          value={formData.due_date}
          onChange={handleChange}
          disabled={submitting}
        />
      </div>
      
      <button type="submit" disabled={submitting} className="submit-button">
        {submitting ? 'Creating...' : 'Create Task'}
      </button>
    </form>
  );
}
```

### 11.3 Real-time Updates with Supabase

```tsx
// components/RealtimeTaskList.tsx
import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabase';
import { Task } from '@/types';

export default function RealtimeTaskList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Initial fetch
    const fetchTasks = async () => {
      setLoading(true);
      
      try {
        const { data, error } = await supabase
          .from('tasks')
          .select('*')
          .order('order_position', { ascending: true });
        
        if (error) throw new Error(error.message);
        
        setTasks(data || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTasks();
    
    // Set up real-time subscription
    const subscription = supabase
      .channel('tasks-channel')
      .on('postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'tasks'
        },
        (payload) => {
          console.log('Change received!', payload);
          
          // Handle different change types
          if (payload.eventType === 'INSERT') {
            setTasks(prev => [...prev, payload.new as Task]);
          } else if (payload.eventType === 'UPDATE') {
            setTasks(prev =>
              prev.map(task => task.id === payload.new.id ? payload.new as Task : task)
            );
          } else if (payload.eventType === 'DELETE') {
            setTasks(prev =>
              prev.filter(task => task.id !== payload.old.id)
            );
          }
        }
      )
      .subscribe();
    
    // Cleanup subscription
    return () => {
      subscription.unsubscribe();
    };
  }, []);
  
  if (loading) return <div>Loading tasks...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div className="task-list">
      <h2>Tasks (Real-time)</h2>
      {tasks.length === 0 ? (
        <p>No tasks found</p>
      ) : (
        <ul>
          {tasks.map(task => (
            <li key={task.id}>
              <span>{task.title}</span>
              <span>{task.completed ? '✓' : '○'}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### 11.4 Authentication Component

```tsx
// components/AuthForm.tsx
import { useState } from 'react';
import { supabase } from '@/utils/supabase';

type AuthMode = 'signin' | 'signup';

export default function AuthForm() {
  const [mode, setMode] = useState<AuthMode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    
    try {
      if (mode === 'signin') {
        // Option 1: Direct Supabase auth
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        
        if (error) throw new Error(error.message);
        
        // Option 2: Using Next.js API route
        // const response = await fetch('/api/auth/signin', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({ email, password }),
        // });
        //
        // if (!response.ok) {
        //   const errorData = await response.json();
        //   throw new Error(errorData.error || 'Sign in failed');
        // }
        
        setMessage('Signed in successfully!');
        window.location.href = '/dashboard'; // Redirect
      } else {
        // Sign up
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
        });
        
        if (error) throw new Error(error.message);
        
        setMessage('Check your email to confirm your account');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="auth-form-container">
      <h2>{mode === 'signin' ? 'Sign In' : 'Sign Up'}</h2>
      
      {error && <div className="error-message">{error}</div>}
      {message && <div className="success-message">{message}</div>}
      
      <form onSubmit={handleAuth} className="auth-form">
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            minLength={6}
          />
        </div>
        
        <button type="submit" disabled={loading} className="auth-button">
          {loading ? 'Processing...' : mode === 'signin' ? 'Sign In' : 'Sign Up'}
        </button>
      </form>
      
      <div className="auth-switch">
        {mode === 'signin' ? (
          <p>
            Don't have an account?{' '}
            <button onClick={() => setMode('signup')} className="text-button">
              Sign Up
            </button>
          </p>
        ) : (
          <p>
            Already have an account?{' '}
            <button onClick={() => setMode('signin')} className="text-button">
              Sign In
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
```

## 12. Conclusion

The Think-Tank project uses a hybrid architecture that combines the strengths of Next.js and FastAPI. The Next.js API routes handle frontend-specific concerns like authentication and direct Supabase database access, while more complex business logic is handled by the FastAPI backend. The Next.js config proxies certain paths to FastAPI when needed.

This architecture provides:
- Excellent developer experience with Next.js
- Strong typing with TypeScript and Pydantic
- Robust backend capabilities with FastAPI
- Simplified database and authentication with Supabase
- Flexible deployment options

By understanding how these components integrate, developers can effectively contribute to the project and extend its capabilities. The error handling and logging strategies ensure that issues can be quickly identified and resolved, while the frontend component examples provide practical patterns for implementing new features.