import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Define the Task type
export interface Task {
  id: number;
  title: string;
  description?: string;
  completed: boolean;
  order_position: number;
  created_at: string;
  updated_at: string;
}

// Define the context type
interface TaskContextType {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  fetchTasks: () => Promise<void>;
  addTask: (title: string, description?: string) => Promise<void>;
  updateTask: (id: number, updates: Partial<Task>) => Promise<void>;
  deleteTask: (id: number) => Promise<void>;
  reorderTasks: (taskIds: number[]) => Promise<void>;
}

// Create the context with default values
const TaskContext = createContext<TaskContextType>({
  tasks: [],
  loading: false,
  error: null,
  fetchTasks: async () => {},
  addTask: async () => {},
  updateTask: async () => {},
  deleteTask: async () => {},
  reorderTasks: async () => {},
});

// Hook to use the task context
export const useTaskContext = () => useContext(TaskContext);

// Provider component
interface TaskProviderProps {
  children: ReactNode;
}

export const TaskProvider = ({ children }: TaskProviderProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const API_URL = '/api/tasks';

  // Fetch all tasks
  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error('Failed to fetch tasks');
      }
      const data = await response.json();
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Add a new task
  const addTask = async (title: string, description?: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title, description, completed: false }),
      });
      if (!response.ok) {
        throw new Error('Failed to add task');
      }
      const newTask = await response.json();
      setTasks([...tasks, newTask]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Update a task
  const updateTask = async (id: number, updates: Partial<Task>) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      if (!response.ok) {
        throw new Error('Failed to update task');
      }
      const updatedTask = await response.json();
      setTasks(tasks.map(task => task.id === id ? updatedTask : task));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Delete a task
  const deleteTask = async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete task');
      }
      setTasks(tasks.filter(task => task.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Reorder tasks
  const reorderTasks = async (taskIds: number[]) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/reorder`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskIds),
      });
      if (!response.ok) {
        throw new Error('Failed to reorder tasks');
      }
      const reorderedTasks = await response.json();
      setTasks(reorderedTasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Load tasks on initial render
  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <TaskContext.Provider
      value={{
        tasks,
        loading,
        error,
        fetchTasks,
        addTask,
        updateTask,
        deleteTask,
        reorderTasks,
      }}
    >
      {children}
    </TaskContext.Provider>
  );
};
