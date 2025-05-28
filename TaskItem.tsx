import React, { useState } from 'react';
import { Task, useTaskContext } from '@/context/TaskContext';

interface TaskItemProps {
  task: Task;
}

export const TaskItem: React.FC<TaskItemProps> = ({ task }) => {
  const { updateTask, deleteTask } = useTaskContext();
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(task.title);
  const [editedDescription, setEditedDescription] = useState(task.description || '');

  const handleToggleComplete = () => {
    updateTask(task.id, { completed: !task.completed });
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = () => {
    if (editedTitle.trim()) {
      updateTask(task.id, { 
        title: editedTitle,
        description: editedDescription || undefined
      });
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setEditedTitle(task.title);
    setEditedDescription(task.description || '');
    setIsEditing(false);
  };

  const handleDelete = () => {
    deleteTask(task.id);
  };

  return (
    <div className="flex flex-col p-3 border-b border-gray-200 group hover:bg-gray-50 transition-colors">
      <div className="flex items-center">
        <input
          type="checkbox"
          checked={task.completed}
          onChange={handleToggleComplete}
          className="h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
        />
        
        {isEditing ? (
          <div className="flex-1 ml-3 flex flex-col">
            <input
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
              placeholder="Task title"
              autoFocus
            />
            <textarea
              value={editedDescription}
              onChange={(e) => setEditedDescription(e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Description (optional)"
              rows={2}
            />
            <div className="flex mt-2">
              <button 
                onClick={handleSave}
                className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
              >
                Save
              </button>
              <button 
                onClick={handleCancel}
                className="ml-2 px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 ml-3">
              <span className={`block font-medium ${task.completed ? 'line-through text-gray-500' : ''}`}>
                {task.title}
              </span>
              {task.description && (
                <p className={`text-sm mt-1 ${task.completed ? 'line-through text-gray-400' : 'text-gray-600'}`}>
                  {task.description}
                </p>
              )}
            </div>
            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
              <button 
                onClick={handleEdit}
                className="px-2 py-1 text-gray-600 hover:text-blue-600"
              >
                Edit
              </button>
              <button 
                onClick={handleDelete}
                className="px-2 py-1 text-gray-600 hover:text-red-600"
              >
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
