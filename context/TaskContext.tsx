'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { v4 as uuidv4 } from 'uuid';

export interface Task {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  due_date?: string;
  priority?: 'none' | 'low' | 'medium' | 'high';
  tags?: string[];
  order_position: number;
  user_id: string;
}

interface TaskContextType {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  addTask: (task: Omit<Task, 'id' | 'created_at' | 'updated_at' | 'order_position' | 'user_id'>) => Promise<void>;
  updateTask: (id: string, task: Partial<Task>) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
  toggleTaskCompletion: (id: string) => Promise<void>;
  reorderTasks: (taskIds: string[]) => Promise<void>;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

export const useTaskContext = () => {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error('useTaskContext must be used within a TaskProvider');
  }
  return context;
};

interface TaskProviderProps {
  children: ReactNode;
}

export const TaskProvider: React.FC<TaskProviderProps> = ({ children }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClientComponentClient();

  // Fetch tasks on component mount
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Check if user is authenticated
        const { data: { session } } = await supabase.auth.getSession();
        
        if (!session) {
          // If not authenticated, use mock data for demo purposes
          const mockTasks: Task[] = [
            {
              id: '1',
              title: 'Create project structure',
              description: 'Set up the initial project structure with Next.js and FastAPI',
              completed: true,
              created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
              updated_at: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
              completed_at: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
              priority: 'high',
              tags: ['setup', 'infrastructure'],
              order_position: 1,
              user_id: 'demo-user'
            },
            {
              id: '2',
              title: 'Implement task management UI',
              description: 'Create React components for task management',
              completed: false,
              created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
              updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
              due_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
              priority: 'medium',
              tags: ['frontend', 'ui'],
              order_position: 2,
              user_id: 'demo-user'
            },
            {
              id: '3',
              title: 'Set up RAG engine',
              description: 'Implement the Retrieval-Augmented Generation engine',
              completed: false,
              created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
              updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
              due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
              priority: 'high',
              tags: ['backend', 'ai'],
              order_position: 3,
              user_id: 'demo-user'
            }
          ];
          
          setTasks(mockTasks);
          setLoading(false);
          return;
        }
        
        // Fetch tasks from Supabase
        const { data, error } = await supabase
          .from('tasks')
          .select('*')
          .order('order_position', { ascending: true });
        
        if (error) {
          throw error;
        }
        
        setTasks(data || []);
      } catch (err) {
        console.error('Error fetching tasks:', err);
        setError('Failed to fetch tasks');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTasks();
    
    // Set up real-time subscription
    const tasksSubscription = supabase
      .channel('tasks-channel')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'tasks' }, (payload) => {
        // Handle different events
        if (payload.eventType === 'INSERT') {
          setTasks(prev => [...prev, payload.new as Task]);
        } else if (payload.eventType === 'UPDATE') {
          setTasks(prev => prev.map(task => task.id === payload.new.id ? payload.new as Task : task));
        } else if (payload.eventType === 'DELETE') {
          setTasks(prev => prev.filter(task => task.id !== payload.old.id));
        }
      })
      .subscribe();
    
    // Clean up subscription
    return () => {
      supabase.removeChannel(tasksSubscription);
    };
  }, [supabase]);

  const addTask = async (task: Omit<Task, 'id' | 'created_at' | 'updated_at' | 'order_position' | 'user_id'>) => {
    try {
      setError(null);
      
      // Check if user is authenticated
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        // If not authenticated, use client-side state for demo
        const now = new Date().toISOString();
        const newTask: Task = {
          ...task,
          id: uuidv4(),
          created_at: now,
          updated_at: now,
          order_position: tasks.length + 1,
          user_id: 'demo-user'
        };
        setTasks([...tasks, newTask]);
        return;
      }
      
      // Get highest order position
      const highestPosition = tasks.length > 0
        ? Math.max(...tasks.map(t => t.order_position))
        : 0;
      
      // Create task in Supabase
      const { error } = await supabase
        .from('tasks')
        .insert({
          title: task.title,
          description: task.description || '',
          completed: task.completed || false,
          order_position: highestPosition + 1,
          priority: task.priority || 'none',
          tags: task.tags || [],
          due_date: task.due_date || null
        });
      
      if (error) {
        throw error;
      }
      
      // Note: We don't need to update the state here as the real-time subscription will handle it
    } catch (err) {
      console.error('Error adding task:', err);
      setError('Failed to add task');
    }
  };

  const updateTask = async (id: string, updatedFields: Partial<Task>) => {
    try {
      setError(null);
      
      // Check if user is authenticated
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        // If not authenticated, use client-side state for demo
        setTasks(tasks.map(task =>
          task.id === id
            ? { ...task, ...updatedFields, updated_at: new Date().toISOString() }
            : task
        ));
        return;
      }
      
      // Remove fields that shouldn't be updated directly
      const { id: _, user_id, created_at, updated_at, ...fieldsToUpdate } = updatedFields;
      
      // Update task in Supabase
      const { error } = await supabase
        .from('tasks')
        .update(fieldsToUpdate)
        .eq('id', id);
      
      if (error) {
        throw error;
      }
      
      // Note: We don't need to update the state here as the real-time subscription will handle it
    } catch (err) {
      console.error('Error updating task:', err);
      setError('Failed to update task');
    }
  };

  const deleteTask = async (id: string) => {
    try {
      setError(null);
      
      // Check if user is authenticated
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        // If not authenticated, use client-side state for demo
        setTasks(tasks.filter(task => task.id !== id));
        return;
      }
      
      // Delete task from Supabase
      const { error } = await supabase
        .from('tasks')
        .delete()
        .eq('id', id);
      
      if (error) {
        throw error;
      }
      
      // Note: We don't need to update the state here as the real-time subscription will handle it
    } catch (err) {
      console.error('Error deleting task:', err);
      setError('Failed to delete task');
    }
  };

  const toggleTaskCompletion = async (id: string) => {
    try {
      setError(null);
      
      // Find the task
      const task = tasks.find(t => t.id === id);
      if (!task) {
        throw new Error('Task not found');
      }
      
      // Toggle completion
      const completed = !task.completed;
      const completedAt = completed ? new Date().toISOString() : null;
      
      // Check if user is authenticated
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        // If not authenticated, use client-side state for demo
        setTasks(tasks.map(task => {
          if (task.id === id) {
            return {
              ...task,
              completed,
              completed_at: completedAt,
              updated_at: new Date().toISOString()
            };
          }
          return task;
        }));
        return;
      }
      
      // Update task in Supabase
      const { error } = await supabase
        .from('tasks')
        .update({
          completed,
          completed_at: completedAt
        })
        .eq('id', id);
      
      if (error) {
        throw error;
      }
      
      // Note: We don't need to update the state here as the real-time subscription will handle it
    } catch (err) {
      console.error('Error toggling task completion:', err);
      setError('Failed to update task');
    }
  };

  const reorderTasks = async (taskIds: string[]) => {
    try {
      setError(null);
      
      // Check if user is authenticated
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        // If not authenticated, use client-side state for demo
        const reorderedTasks = [...tasks];
        
        // Create a map of task ID to task
        const taskMap = new Map(reorderedTasks.map(task => [task.id, task]));
        
        // Update order_position for each task
        taskIds.forEach((id, index) => {
          const task = taskMap.get(id);
          if (task) {
            task.order_position = index + 1;
          }
        });
        
        // Sort tasks by order_position
        reorderedTasks.sort((a, b) => a.order_position - b.order_position);
        
        setTasks(reorderedTasks);
        return;
      }
      
      // Call the reorder API endpoint
      const response = await fetch('/api/tasks/reorder', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ task_ids: taskIds }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to reorder tasks');
      }
      
      // Note: We don't need to update the state here as the real-time subscription will handle it
    } catch (err) {
      console.error('Error reordering tasks:', err);
      setError('Failed to reorder tasks');
    }
  };

  return (
    <TaskContext.Provider value={{
      tasks,
      loading,
      error,
      addTask,
      updateTask,
      deleteTask,
      toggleTaskCompletion,
      reorderTasks
    }}>
      {children}
    </TaskContext.Provider>
  );
};