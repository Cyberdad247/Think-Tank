import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TaskProvider } from '@/context/TaskContext';
import { TaskChecklist } from '@/components/TaskChecklist/TaskChecklist';

// Mock the fetch API
global.fetch = jest.fn();

describe('TaskChecklist Component', () => {
  beforeEach(() => {
    // Mock successful fetch for tasks
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, title: 'Task 1', completed: false, order_position: 1 },
        { id: 2, title: 'Task 2', completed: true, order_position: 2 }
      ]
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders task list and form', async () => {
    render(
      <TaskProvider>
        <TaskChecklist />
      </TaskProvider>
    );

    // Check if loading indicator is shown initially
    expect(screen.getByRole('status')).toBeInTheDocument();

    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });

    // Check if form is rendered
    expect(screen.getByPlaceholderText('Add a new task...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add task/i })).toBeInTheDocument();
  });

  test('adds a new task', async () => {
    // Mock successful task creation
    global.fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          { id: 1, title: 'Task 1', completed: false, order_position: 1 },
          { id: 2, title: 'Task 2', completed: true, order_position: 2 }
        ])
      })
    ).mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ 
          id: 3, 
          title: 'New Task', 
          completed: false, 
          order_position: 3 
        })
      })
    );

    render(
      <TaskProvider>
        <TaskChecklist />
      </TaskProvider>
    );

    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    // Add a new task
    const input = screen.getByPlaceholderText('Add a new task...');
    const addButton = screen.getByRole('button', { name: /add task/i });

    fireEvent.change(input, { target: { value: 'New Task' } });
    fireEvent.click(addButton);

    // Verify fetch was called with correct parameters
    expect(global.fetch).toHaveBeenCalledWith('/api/tasks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title: 'New Task', completed: false }),
    });
  });

  test('toggles task completion', async () => {
    // Mock successful task update
    global.fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          { id: 1, title: 'Task 1', completed: false, order_position: 1 },
          { id: 2, title: 'Task 2', completed: true, order_position: 2 }
        ])
      })
    ).mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ 
          id: 1, 
          title: 'Task 1', 
          completed: true, 
          order_position: 1 
        })
      })
    );

    render(
      <TaskProvider>
        <TaskChecklist />
      </TaskProvider>
    );

    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    // Find the checkbox for Task 1 and toggle it
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);

    // Verify fetch was called with correct parameters
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/tasks/1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ completed: true }),
      });
    });
  });
});
