/**
 * examples/api/tasks.ts
 * 
 * A Next.js API route that demonstrates:
 * - Proxying requests to the FastAPI backend
 * - Authentication validation
 * - Error handling and response formatting
 * - Proper TypeScript typing for request/response
 * 
 * This file shows how Next.js API routes can serve as a middleware layer
 * between the frontend and the backend, handling authentication and
 * providing a unified API interface.
 */

import { NextApiRequest, NextApiResponse } from 'next';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

// Define response types for better type safety
interface ErrorResponse {
  error: string;
  details?: any;
}

interface SuccessResponse<T> {
  data: T;
}

// Define task types
export interface Task {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  order_position: number;
  user_id: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  due_date?: string;
  priority?: 'none' | 'low' | 'medium' | 'high';
  tags?: string[];
}

// Custom error classes for better error handling
class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
  }
}

/**
 * Helper function to validate authentication
 * Throws AuthError if user is not authenticated
 */
async function validateAuth() {
  const supabase = createRouteHandlerClient({ cookies });
  
  // Check if user is authenticated
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    throw new AuthError('Unauthorized: User not authenticated');
  }
  
  return { supabase, userId: session.user.id };
}

/**
 * Helper function to proxy requests to the FastAPI backend
 * This demonstrates how to forward requests while adding authentication
 */
async function proxyToFastAPI(
  endpoint: string,
  method: string,
  body?: any,
  userId?: string
) {
  // Get the FastAPI backend URL from environment variables
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  const url = `${backendUrl}/api${endpoint}`;
  
  // Prepare headers with authentication
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  // Add user ID for authentication if available
  if (userId) {
    headers['X-User-ID'] = userId;
  }
  
  // Make the request to the FastAPI backend
  try {
    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    
    // Handle non-OK responses
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Backend request failed with status ${response.status}`);
    }
    
    // Parse and return the response
    return await response.json();
  } catch (error) {
    console.error('Error proxying to FastAPI:', error);
    throw error;
  }
}

/**
 * Handler for GET /api/tasks
 * Gets all tasks for the authenticated user
 *
 * This demonstrates:
 * - Direct Supabase database access for simple queries
 */
async function handleGetTasks(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string
) {
  // Get query parameters for pagination
  const { skip = '0', limit = '100' } = req.query;
  const skipNum = parseInt(skip as string, 10);
  const limitNum = parseInt(limit as string, 10);
  
  // Query tasks from Supabase
  const { data: tasks, error } = await supabase
    .from('tasks')
    .select('*')
    .eq('user_id', userId)
    .order('order_position', { ascending: true })
    .range(skipNum, skipNum + limitNum - 1);
  
  if (error) {
    console.error('Error fetching tasks:', error);
    throw new Error('Failed to fetch tasks');
  }
  
  // Return the tasks
  res.status(200).json({ data: tasks });
}

/**
 * Handler for GET /api/tasks/[id]
 * Gets a single task by ID
 *
 * This demonstrates:
 * - Checking ownership of resources
 * - Handling not found errors
 */
async function handleGetTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string,
  taskId: string
) {
  // Query the task from Supabase
  const { data: task, error } = await supabase
    .from('tasks')
    .select('*')
    .eq('id', taskId)
    .single();
  
  if (error) {
    console.error('Error fetching task:', error);
    throw new NotFoundError('Task not found');
  }
  
  // Check if the task belongs to the authenticated user
  if (task.user_id !== userId) {
    throw new AuthError('Unauthorized: Task belongs to another user');
  }
  
  // Return the task
  res.status(200).json({ data: task });
}

/**
 * Handler for POST /api/tasks
 * Creates a new task
 *
 * This demonstrates:
 * - Input validation
 * - Creating resources in the database
 */
async function handleCreateTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string
) {
  // Parse and validate the request body
  const { title, description, priority, due_date, tags } = req.body;
  
  if (!title || typeof title !== 'string') {
    throw new ValidationError('Title is required and must be a string');
  }
  
  // Get the highest order_position
  const { data: highestPositionTask } = await supabase
    .from('tasks')
    .select('order_position')
    .eq('user_id', userId)
    .order('order_position', { ascending: false })
    .limit(1);
  
  const newPosition = highestPositionTask && highestPositionTask.length > 0
    ? highestPositionTask[0].order_position + 1
    : 1;
  
  // Create the new task
  const { data: newTask, error } = await supabase
    .from('tasks')
    .insert({
      title,
      description: description || '',
      completed: false,
      order_position: newPosition,
      user_id: userId,
      priority: priority || 'none',
      tags: tags || [],
      due_date: due_date || null
    })
    .select()
    .single();
  
  if (error) {
    console.error('Error creating task:', error);
    throw new Error('Failed to create task');
  }
  
  // Return the new task
  res.status(201).json({ data: newTask });
}

/**
 * Handler for PATCH /api/tasks/[id]
 * Updates an existing task
 *
 * This demonstrates:
 * - Partial updates
 * - Proxying complex operations to FastAPI
 */
async function handleUpdateTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string,
  taskId: string
) {
  // First, check if the task exists and belongs to the user
  const { data: existingTask, error: fetchError } = await supabase
    .from('tasks')
    .select('*')
    .eq('id', taskId)
    .single();
  
  if (fetchError) {
    throw new NotFoundError('Task not found');
  }
  
  if (existingTask.user_id !== userId) {
    throw new AuthError('Unauthorized: Task belongs to another user');
  }
  
  // Check if this is a complex update that requires FastAPI
  const { completed, title, description, priority, due_date, tags } = req.body;
  
  // If this is a complex update (e.g., involves AI processing), proxy to FastAPI
  if (req.body.ai_process) {
    // Example of proxying to FastAPI for complex processing
    const processedTask = await proxyToFastAPI(
      `/tasks/${taskId}`,
      'PATCH',
      req.body,
      userId
    );
    
    res.status(200).json({ data: processedTask });
    return;
  }
  
  // For simple updates, use Supabase directly
  const updates: any = {};
  
  // Only include fields that are provided in the request
  if (title !== undefined) updates.title = title;
  if (description !== undefined) updates.description = description;
  if (completed !== undefined) {
    updates.completed = completed;
    if (completed) {
      updates.completed_at = new Date().toISOString();
    } else {
      updates.completed_at = null;
    }
  }
  if (priority !== undefined) updates.priority = priority;
  if (due_date !== undefined) updates.due_date = due_date;
  if (tags !== undefined) updates.tags = tags;
  
  // Always update the updated_at timestamp
  updates.updated_at = new Date().toISOString();
  
  // Update the task
  const { data: updatedTask, error: updateError } = await supabase
    .from('tasks')
    .update(updates)
    .eq('id', taskId)
    .select()
    .single();
  
  if (updateError) {
    console.error('Error updating task:', updateError);
    throw new Error('Failed to update task');
  }
  
  // Return the updated task
  res.status(200).json({ data: updatedTask });
}

/**
 * Handler for DELETE /api/tasks/[id]
 * Deletes a task
 *
 * This demonstrates:
 * - Resource deletion
 * - Security checks
 */
async function handleDeleteTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string,
  taskId: string
) {
  // First, check if the task exists and belongs to the user
  const { data: existingTask, error: fetchError } = await supabase
    .from('tasks')
    .select('*')
    .eq('id', taskId)
    .single();
  
  if (fetchError) {
    throw new NotFoundError('Task not found');
  }
  
  if (existingTask.user_id !== userId) {
    throw new AuthError('Unauthorized: Task belongs to another user');
  }
  
  // Delete the task
  const { error: deleteError } = await supabase
    .from('tasks')
    .delete()
    .eq('id', taskId);
  
  if (deleteError) {
    console.error('Error deleting task:', deleteError);
    throw new Error('Failed to delete task');
  }
  
  // Return success
  res.status(200).json({ data: { success: true, id: taskId } });
}

/**
 * Main API handler function
 * Handles different HTTP methods and routes requests appropriately
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<SuccessResponse<any> | ErrorResponse>
) {
  try {
    // Extract method and query parameters
    const { method, query } = req;
    
    // Validate authentication for all requests
    const { supabase, userId } = await validateAuth();
    
    // Handle different HTTP methods
    switch (method) {
      case 'GET': {
        // Handle GET requests
        if (query.id) {
          // Get a single task
          await handleGetTask(req, res, supabase, userId, query.id as string);
        } else {
          // Get all tasks
          await handleGetTasks(req, res, supabase, userId);
        }
        break;
      }
      
      case 'POST': {
        // Create a new task
        await handleCreateTask(req, res, supabase, userId);
        break;
      }
      
      case 'PATCH': {
        // Update an existing task
        if (!query.id) {
          throw new ValidationError('Task ID is required for updates');
        }
        await handleUpdateTask(req, res, supabase, userId, query.id as string);
        break;
      }
      
      case 'DELETE': {
        // Delete a task
        if (!query.id) {
          throw new ValidationError('Task ID is required for deletion');
        }
        await handleDeleteTask(req, res, supabase, userId, query.id as string);
        break;
      }
      
      default:
        // Handle unsupported methods
        res.setHeader('Allow', ['GET', 'POST', 'PATCH', 'DELETE']);
        res.status(405).json({ error: `Method ${method} Not Allowed` });
    }
  } catch (error) {
    // Handle different types of errors
    console.error('API error:', error);
    
    if (error instanceof AuthError) {
      res.status(401).json({ error: error.message });
    } else if (error instanceof ValidationError) {
      res.status(400).json({ error: error.message });
    } else if (error instanceof NotFoundError) {
      res.status(404).json({ error: error.message });
    } else {
      // Generic error handling
      res.status(500).json({
        error: 'Internal server error',
        details: process.env.NODE_ENV === 'development' ? (error as Error).message : undefined
      });
    }
  }
}

/**
 * Handler for GET /api/tasks
 * Gets all tasks for the authenticated user
 * 
 * This demonstrates:
 * - Direct Supabase database access for simple queries
 */
async function handleGetTasks(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string
) {
  // Get query parameters for pagination
  const { skip = '0', limit = '100' } = req.query;
  const skipNum = parseInt(skip as string, 10);
  const limitNum = parseInt(limit as string, 10);
  
  // Query tasks from Supabase
  const { data: tasks, error } = await supabase
    .from('tasks')
    .select('*')
    .eq('user_id', userId)
    .order('order_position', { ascending: true })
    .range(skipNum, skipNum + limitNum - 1);
  
  if (error) {
    console.error('Error fetching tasks:', error);
    throw new Error('Failed to fetch tasks');
  }
  
  // Return the tasks
  res.status(200).json({ data: tasks });
}

/**
 * Handler for GET /api/tasks/[id]
 * Gets a single task by ID
 * 
 * This demonstrates:
 * - Checking ownership of resources
 * - Handling not found errors
 */
async function handleGetTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string,
  taskId: string
) {
  // Query the task from Supabase
  const { data: task, error } = await supabase
    .from('tasks')
    .select('*')
    .eq('id', taskId)
    .single();
  
  if (error) {
    console.error('Error fetching task:', error);
    throw new NotFoundError('Task not found');
  }
  
  // Check if the task belongs to the authenticated user
  if (task.user_id !== userId) {
    throw new AuthError('Unauthorized: Task belongs to another user');
  }
  
  // Return the task
  res.status(200).json({ data: task });
}

/**
 * Handler for POST /api/tasks
 * Creates a new task
 * 
 * This demonstrates:
 * - Input validation
 * - Creating resources in the database
 */
async function handleCreateTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string
) {
  // Parse and validate the request body
  const { title, description, priority, due_date, tags } = req.body;
  
  if (!title || typeof title !== 'string') {
    throw new ValidationError('Title is required and must be a string');
  }
  
  // Get the highest order_position
  const { data: highestPositionTask } = await supabase
    .from('tasks')
    .select('order_position')
    .eq('user_id', userId)
    .order('order_position', { ascending: false })
    .limit(1);
  
  const newPosition = highestPositionTask && highestPositionTask.length > 0 
    ? highestPositionTask[0].order_position + 1 
    : 1;
  
  // Create the new task
  const { data: newTask, error } = await supabase
    .from('tasks')
    .insert({
      title,
      description: description || '',
      completed: false,
      order_position: newPosition,
      user_id: userId,
      priority: priority || 'none',
      tags: tags || [],
      due_date: due_date || null
    })
    .select()
    .single();
  
  if (error) {
    console.error('Error creating task:', error);
    throw new Error('Failed to create task');
  }
  
  // Return the new task
  res.status(201).json({ data: newTask });
}

/**
 * Handler for PATCH /api/tasks/[id]
 * Updates an existing task
 * 
 * This demonstrates:
 * - Partial updates
 * - Proxying complex operations to FastAPI
 */
async function handleUpdateTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string,
  taskId: string
) {
  // First, check if the task exists and belongs to the user
  const { data: existingTask, error: fetchError } = await supabase
    .from('tasks')
    .select('*')
    .eq('id', taskId)
    .single();
  
  if (fetchError) {
    throw new NotFoundError('Task not found');
  }
  
  if (existingTask.user_id !== userId) {
    throw new AuthError('Unauthorized: Task belongs to another user');
  }
  
  // Check if this is a complex update that requires FastAPI
  const { completed, title, description, priority, due_date, tags } = req.body;
  
  // If this is a complex update (e.g., involves AI processing), proxy to FastAPI
  if (req.body.ai_process) {
    // Example of proxying to FastAPI for complex processing
    const processedTask = await proxyToFastAPI(
      `/tasks/${taskId}`,
      'PATCH',
      req.body,
      userId
    );
    
    res.status(200).json({ data: processedTask });
    return;
  }
  
  // For simple updates, use Supabase directly
  const updates: any = {};
  
  // Only include fields that are provided in the request
  if (title !== undefined) updates.title = title;
  if (description !== undefined) updates.description = description;
  if (completed !== undefined) {
    updates.completed = completed;
    if (completed) {
      updates.completed_at = new Date().toISOString();
    } else {
      updates.completed_at = null;
    }
  }
  if (priority !== undefined) updates.priority = priority;
  if (due_date !== undefined) updates.due_date = due_date;
  if (tags !== undefined) updates.tags = tags;
  
  // Always update the updated_at timestamp
  updates.updated_at = new Date().toISOString();
  
  // Update the task
  const { data: updatedTask, error: updateError } = await supabase
    .from('tasks')
    .update(updates)
    .eq('id', taskId)
    .select()
    .single();
  
  if (updateError) {
    console.error('Error updating task:', updateError);
    throw new Error('Failed to update task');
  }
  
  // Return the updated task
  res.status(200).json({ data: updatedTask });
}

/**
 * Handler for DELETE /api/tasks/[id]
 * Deletes a task
 * 
 * This demonstrates:
 * - Resource deletion
 * - Security checks
 */
async function handleDeleteTask(
  req: NextApiRequest,
  res: NextApiResponse,
  supabase: any,
  userId: string,
  taskId: string
) {
  // First, check if the task exists and belongs to the user
  const { data: existingTask, error: fetchError } = await supabase
    .from('tasks')
    .select('*')
    .eq('id', taskId)
    .single();
  
  if (fetchError) {
    throw new NotFoundError('Task not found');
  }
  
  if (existingTask.user_id !== userId) {
    throw new AuthError('Unauthorized: Task belongs to another user');
  }
  
  // Delete the task
  const { error: deleteError } = await supabase
    .from('tasks')
    .delete()
    .eq('id', taskId);
  
  if (deleteError) {
    console.error('Error deleting task:', deleteError);
    throw new Error('Failed to delete task');
  }
  
  // Return success
  res.status(200).json({ data: { success: true, id: taskId } });
}