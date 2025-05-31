'use client';

import React, { useState } from 'react';
import { useTaskContext, Task } from '../context/TaskContext';

export const TaskChecklist: React.FC = () => {
  const { tasks, loading, error, addTask, updateTask, deleteTask, toggleTaskCompletion } = useTaskContext();
  const [newTaskTitle, setNewTaskTitle] = useState('');

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newTaskTitle.trim()) {
      await addTask({
        title: newTaskTitle,
        description: '',
        completed: false,
      });
      setNewTaskTitle('');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Tasks</h2>
      
      <form onSubmit={handleAddTask} className="mb-6">
        <div className="flex">
          <input
            type="text"
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
            placeholder="Add a new task..."
            className="flex-1 px-4 py-2 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Add
          </button>
        </div>
      </form>
      
      {loading ? (
        <div className="flex justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="text-red-500 text-center py-4">
          Error: {error}
        </div>
      ) : (
        <div className="space-y-2">
          {tasks.length > 0 ? (
            tasks.map((task) => (
              <div key={task.id} className="flex items-center p-3 border rounded-lg">
                <input
                  type="checkbox"
                  checked={task.completed}
                  onChange={() => toggleTaskCompletion(task.id)}
                  className="h-5 w-5 text-blue-500"
                />
                <span
                  className={`ml-3 flex-1 ${task.completed ? 'line-through text-gray-400' : ''}`}
                >
                  {task.title}
                </span>
                <button
                  onClick={() => deleteTask(task.id)}
                  className="text-red-500 hover:text-red-700"
                >
                  Delete
                </button>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-4">No tasks yet. Add one above!</p>
          )}
        </div>
      )}
    </div>
  );
};