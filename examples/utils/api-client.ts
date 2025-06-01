/**
 * api-client.ts
 * 
 * A utility file that demonstrates:
 * - Creating a reusable API client for frontend components
 * - Handling authentication headers
 * - Managing request/response types
 * - Error handling and retry logic
 * 
 * This client provides a clean interface for components to interact with
 * both Next.js API routes and FastAPI backend endpoints.
 */

import { CreateTaskPayload, Task, UpdateTaskPayload } from '../TaskComponent';

// Configuration options for the API client
interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

// Default configuration
const DEFAULT_CONFIG: ApiClientConfig = {
  baseUrl: '/api',
  timeout: 10000, // 10 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
};

/**
 * Custom error class for API errors
 * Provides additional context about the failed request
 */
export class ApiError extends Error {
  status: number;
  data: any;
  
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * API Client class that handles all API requests
 * Provides methods for common CRUD operations on tasks
 */
class ApiClient {
  private config: ApiClientConfig;
  
  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }
  
  /**
   * Get the authentication token from local storage
   * In a real application, this might use a more secure method
   */
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }
  
  /**
   * Create headers for API requests, including authentication
   */
  private createHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }
  
  /**
   * Generic request method with retry logic and error handling
   * This is the core method that all other methods use
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const headers = this.createHeaders();
    
    // Create request with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: { ...headers, ...options.headers },
        signal: controller.signal,
      });
      
      // Clear timeout
      clearTimeout(timeoutId);
      
      // Handle successful response
      if (response.ok) {
        // Check if response is empty
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        }
        return {} as T;
      }
      
      // Handle error response
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { message: 'Unknown error' };
      }
      
      // Throw API error
      throw new ApiError(
        errorData.error || errorData.message || `Request failed with status ${response.status}`,
        response.status,
        errorData
      );
    } catch (error) {
      // Clear timeout
      clearTimeout(timeoutId);
      
      // Handle fetch errors (network issues, timeouts)
      if (error instanceof ApiError) {
        // If it's already an ApiError, just rethrow it
        throw error;
      }
      
      // Handle abort error (timeout)
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError('Request timeout', 408);
      }
      
      // Implement retry logic for network errors
      if (retryCount < this.config.retryAttempts) {
        console.log(`Retrying request (${retryCount + 1}/${this.config.retryAttempts})...`);
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
        
        // Retry the request
        return this.request<T>(endpoint, options, retryCount + 1);
      }
      
      // If we've exhausted retries, throw a generic error
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error',
        0
      );
    }
  }
  
  /**
   * Get all tasks
   * Uses the Next.js API route which proxies to Supabase
   */
  async getTasks(): Promise<Task[]> {
    return this.request<Task[]>('/tasks');
  }
  
  /**
   * Get a single task by ID
   */
  async getTask(id: string): Promise<Task> {
    return this.request<Task>(`/tasks/${id}`);
  }
  
  /**
   * Create a new task
   */
  async createTask(task: CreateTaskPayload): Promise<Task> {
    return this.request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }
  
  /**
   * Update an existing task
   */
  async updateTask(id: string, updates: UpdateTaskPayload): Promise<Task> {
    return this.request<Task>(`/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }
  
  /**
   * Delete a task
   */
  async deleteTask(id: string): Promise<void> {
    return this.request<void>(`/tasks/${id}`, {
      method: 'DELETE',
    });
  }
  
  /**
   * Reorder tasks
   * This demonstrates a more complex API call
   */
  async reorderTasks(taskIds: string[]): Promise<Task[]> {
    return this.request<Task[]>('/tasks/reorder', {
      method: 'PUT',
      body: JSON.stringify({ task_ids: taskIds }),
    });
  }
  
  /**
   * Search tasks using the FastAPI vector search endpoint
   * This demonstrates calling a FastAPI endpoint through the Next.js API proxy
   */
  async searchTasks(query: string): Promise<Task[]> {
    return this.request<Task[]>('/vector-search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }
  
  /**
   * Get task analytics
   * This demonstrates calling a FastAPI endpoint that performs complex calculations
   */
  async getTaskAnalytics(): Promise<any> {
    return this.request<any>('/tasks/analytics');
  }
}

// Export a singleton instance of the API client
export const apiClient = new ApiClient();

// Also export the class for testing or custom configuration
export default ApiClient;