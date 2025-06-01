import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from './utils/api-client';

/**
 * TaskComponent - A React component that demonstrates frontend-backend integration
 * 
 * This component showcases:
 * 1. Making authenticated API calls to both Next.js API routes and FastAPI endpoints
 * 2. Handling loading states, errors, and successful responses
 * 3. Using React hooks for state management
 * 4. Proper TypeScript typing
 * 
 * The component implements a complete CRUD interface for tasks:
 * - Create: Add new tasks
 * - Read: Fetch and display tasks
 * - Update: Edit task details and toggle completion status
 * - Delete: Remove tasks
 */

// Define TypeScript interfaces for our data models
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

// Interface for creating a new task
export interface CreateTaskPayload {
  title: string;
  description?: string;
  priority?: 'none' | 'low' | 'medium' | 'high';
  due_date?: string;
  tags?: string[];
}

// Interface for updating a task
export interface UpdateTaskPayload {
  title?: string;
  description?: string;
  completed?: boolean;
  priority?: 'none' | 'low' | 'medium' | 'high';
  due_date?: string;
  tags?: string[];
}

const TaskComponent: React.FC = () => {
  // State management using React hooks
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState<string>('');
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  
  // Form state for editing
  const [editForm, setEditForm] = useState<{
    title: string;
    description: string;
    priority: 'none' | 'low' | 'medium' | 'high';
    due_date: string;
    tags: string;
  }>({
    title: '',
    description: '',
    priority: 'none',
    due_date: '',
    tags: ''
  });

  /**
   * Fetch tasks from the API
   * This demonstrates making an authenticated API call and handling the response
   */
  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Using our API client to make the request
      const data = await apiClient.getTasks();
      setTasks(data);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load tasks when component mounts
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  /**
   * Create a new task
   * Demonstrates sending data to the API and handling the response
   */
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newTaskTitle.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Create task payload
      const newTask: CreateTaskPayload = {
        title: newTaskTitle.trim()
      };
      
      // Send to API
      await apiClient.createTask(newTask);
      
      // Reset form and refresh tasks
      setNewTaskTitle('');
      await fetchTasks();
    } catch (err) {
      console.error('Error creating task:', err);
      setError(err instanceof Error ? err.message : 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Toggle task completion status
   * Demonstrates updating a resource via the API
   */
  const handleToggleComplete = async (task: Task) => {
    setLoading(true);
    setError(null);
    
    try {
      // Update task with toggled completion status
      await apiClient.updateTask(task.id, {
        completed: !task.completed
      });
      
      // Refresh tasks
      await fetchTasks();
    } catch (err) {
      console.error('Error updating task:', err);
      setError(err instanceof Error ? err.message : 'Failed to update task');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Delete a task
   * Demonstrates deleting a resource via the API
   */
  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Delete the task
      await apiClient.deleteTask(taskId);
      
      // Refresh tasks
      await fetchTasks();
    } catch (err) {
      console.error('Error deleting task:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete task');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Start editing a task
   * Sets up the edit form with the current task values
   */
  const startEditing = (task: Task) => {
    setEditingTask(task);
    setEditForm({
      title: task.title,
      description: task.description || '',
      priority: (task.priority || 'none') as ('none' | 'low' | 'medium' | 'high'),
      due_date: task.due_date || '',
      tags: task.tags ? task.tags.join(', ') : ''
    });
  };

  /**
   * Cancel editing
   * Resets the editing state
   */
  const cancelEditing = () => {
    setEditingTask(null);
  };

  /**
   * Save edited task
   * Demonstrates updating a resource with multiple fields
   */
  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!editingTask || !editForm.title.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Prepare update payload
      const updatePayload: UpdateTaskPayload = {
        title: editForm.title.trim(),
        description: editForm.description.trim() || undefined,
        priority: editForm.priority,
        due_date: editForm.due_date || undefined,
        tags: editForm.tags ? editForm.tags.split(',').map(tag => tag.trim()) : undefined
      };
      
      // Send update to API
      await apiClient.updateTask(editingTask.id, updatePayload);
      
      // Reset editing state and refresh tasks
      setEditingTask(null);
      await fetchTasks();
    } catch (err) {
      console.error('Error updating task:', err);
      setError(err instanceof Error ? err.message : 'Failed to update task');
    } finally {
      setLoading(false);
    }
  };

  // Render loading state
  if (loading && tasks.length === 0) {
    return <div className="loading">Loading tasks...</div>;
  }

  // Render error state
  if (error && tasks.length === 0) {
    return (
      <div className="error">
        <p>Error: {error}</p>
        <button onClick={fetchTasks}>Try Again</button>
      </div>
    );
  }

  return (
    <div className="task-component">
      <h1>Tasks</h1>
      
      {/* Create Task Form */}
      <form onSubmit={handleCreateTask} className="create-task-form">
        <input
          type="text"
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          placeholder="Enter a new task"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !newTaskTitle.trim()}>
          Add Task
        </button>
      </form>
      
      {/* Error message */}
      {error && <div className="error-message">{error}</div>}
      
      {/* Task List */}
      <ul className="task-list">
        {tasks.map(task => (
          <li key={task.id} className={`task-item ${task.completed ? 'completed' : ''}`}>
            {editingTask?.id === task.id ? (
              /* Edit Form */
              <form onSubmit={handleSaveEdit} className="edit-task-form">
                <div className="form-group">
                  <label htmlFor="title">Title:</label>
                  <input
                    id="title"
                    type="text"
                    value={editForm.title}
                    onChange={(e) => setEditForm({...editForm, title: e.target.value})}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="description">Description:</label>
                  <textarea
                    id="description"
                    value={editForm.description}
                    onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                    rows={3}
                  />
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="priority">Priority:</label>
                    <select
                      id="priority"
                      value={editForm.priority}
                      onChange={(e) => setEditForm({
                        ...editForm,
                        priority: e.target.value as ('none' | 'low' | 'medium' | 'high')
                      })}
                    >
                      <option value="none">None</option>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="due_date">Due Date:</label>
                    <input
                      id="due_date"
                      type="date"
                      value={editForm.due_date}
                      onChange={(e) => setEditForm({...editForm, due_date: e.target.value})}
                    />
                  </div>
                </div>
                
                <div className="form-group">
                  <label htmlFor="tags">Tags (comma separated):</label>
                  <input
                    id="tags"
                    type="text"
                    value={editForm.tags}
                    onChange={(e) => setEditForm({...editForm, tags: e.target.value})}
                    placeholder="work, personal, urgent"
                  />
                </div>
                
                <div className="form-actions">
                  <button type="submit" disabled={loading || !editForm.title.trim()}>
                    Save
                  </button>
                  <button type="button" onClick={cancelEditing} disabled={loading}>
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              /* Task Display */
              <>
                <div className="task-content">
                  <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={() => handleToggleComplete(task)}
                    disabled={loading}
                  />
                  
                  <div className="task-details">
                    <h3 className="task-title">{task.title}</h3>
                    
                    {task.description && (
                      <p className="task-description">{task.description}</p>
                    )}
                    
                    <div className="task-meta">
                      {task.priority && task.priority !== 'none' && (
                        <span className={`priority priority-${task.priority}`}>
                          {task.priority}
                        </span>
                      )}
                      
                      {task.due_date && (
                        <span className="due-date">
                          Due: {new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                      
                      {task.tags && task.tags.length > 0 && (
                        <div className="tags">
                          {task.tags.map((tag, index) => (
                            <span key={index} className="tag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="task-actions">
                  <button
                    onClick={() => startEditing(task)}
                    disabled={loading}
                    className="edit-button"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteTask(task.id)}
                    disabled={loading}
                    className="delete-button"
                  >
                    Delete
                  </button>
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
      
      {/* Empty state */}
      {tasks.length === 0 && !loading && (
        <p className="empty-state">No tasks found. Create your first task above!</p>
      )}
      
      {/* Loading indicator for actions */}
      {loading && tasks.length > 0 && (
        <div className="loading-indicator">Processing...</div>
      )}
    </div>
  );
};

export default TaskComponent;