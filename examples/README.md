# Frontend-Backend Integration Examples

This directory contains example code files that demonstrate the integration between a Next.js frontend and a FastAPI backend, as described in the project documentation.

## Overview

These examples showcase practical implementations of the integration concepts, including:

- Making authenticated API calls from React components
- Proxying requests from Next.js API routes to FastAPI
- Handling authentication across the stack
- Error handling and response formatting
- Data validation with TypeScript and Pydantic
- Database operations with Supabase

## Files in this Directory

### 1. TaskComponent.tsx

A React component that demonstrates:
- Making authenticated API calls to both Next.js API routes and FastAPI endpoints
- Handling loading states, errors, and successful responses
- Using React hooks for state management
- Proper TypeScript typing

This component implements a complete CRUD interface for tasks, showing how to:
- Create new tasks
- Read and display tasks with proper loading and error states
- Update task details and toggle completion status
- Delete tasks

### 2. api/tasks.ts

A Next.js API route that demonstrates:
- Proxying requests to the FastAPI backend
- Authentication validation
- Error handling and response formatting
- Proper TypeScript typing for request/response

This file shows how Next.js API routes can serve as a middleware layer between the frontend and backend, handling authentication and providing a unified API interface.

### 3. backend/task_endpoint.py

A FastAPI endpoint that demonstrates:
- Request validation with Pydantic models
- Authentication handling
- Database operations with Supabase
- Error handling and response formatting

This file shows how to implement complex business logic in the backend that would be inefficient to handle in the frontend.

### 4. utils/api-client.ts

A utility file that demonstrates:
- Creating a reusable API client for frontend components
- Handling authentication headers
- Managing request/response types
- Error handling and retry logic

This client provides a clean interface for components to interact with both Next.js API routes and FastAPI backend endpoints.

## How to Use These Examples

### Prerequisites

1. A running Next.js frontend application
2. A running FastAPI backend application
3. A Supabase project with the appropriate tables set up
4. Environment variables configured as described in the documentation

### Integration Steps

1. **Set up the API client**:
   - Copy `utils/api-client.ts` to your project's utils directory
   - Adjust the configuration as needed for your environment

2. **Create the Next.js API route**:
   - Copy `api/tasks.ts` to your project's `app/api/tasks/route.ts` file
   - Update imports and paths as needed for your project structure

3. **Implement the FastAPI endpoint**:
   - Copy `backend/task_endpoint.py` to your FastAPI project
   - Update imports and database configuration as needed

4. **Create the React component**:
   - Copy `TaskComponent.tsx` to your project's components directory
   - Import and use it in your pages or other components

### Testing the Integration

1. Start your Next.js frontend application
2. Start your FastAPI backend application
3. Navigate to the page containing the TaskComponent
4. Test the CRUD operations:
   - Create a new task
   - View the list of tasks
   - Edit a task
   - Delete a task

## Key Integration Concepts Demonstrated

1. **Authentication Flow**:
   - The frontend stores authentication tokens
   - The API client includes tokens in requests
   - Next.js API routes validate tokens before processing requests
   - FastAPI endpoints receive and validate user information

2. **Error Handling**:
   - Client-side error handling with loading states and error messages
   - Server-side error handling with appropriate HTTP status codes
   - Consistent error response format across the stack

3. **Data Validation**:
   - TypeScript interfaces for frontend type safety
   - Pydantic models for backend request validation
   - Consistent data models across the stack

4. **Proxying Strategy**:
   - Simple operations handled directly by Next.js API routes
   - Complex operations proxied to FastAPI
   - Unified API interface for the frontend

5. **Database Access**:
   - Direct Supabase client usage for simple operations
   - FastAPI backend for complex database operations
   - Consistent data access patterns

## Extending the Examples

These examples can be extended to include:

1. **Real-time updates** using Supabase subscriptions
2. **File uploads** with proper handling across the stack
3. **Advanced authentication** with role-based access control
4. **Pagination and filtering** for large datasets
5. **Caching strategies** for improved performance

Refer to the main documentation for more details on these advanced topics.