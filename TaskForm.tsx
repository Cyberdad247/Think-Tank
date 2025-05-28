import React, { useState } from 'react';
import { useTaskContext } from '@/context/TaskContext';

export const TaskForm: React.FC = () => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [showDescription, setShowDescription] = useState(false);
  const { addTask, loading } = useTaskContext();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (title.trim()) {
      await addTask(title.trim(), description.trim() || undefined);
      setTitle('');
      setDescription('');
      setShowDescription(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-6 bg-white p-4 rounded-lg shadow-sm">
      <div className="mb-3">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add a new task..."
          className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
      </div>
      
      {showDescription ? (
        <div className="mb-3">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add description (optional)"
            className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            disabled={loading}
          />
        </div>
      ) : (
        <div className="mb-3">
          <button
            type="button"
            onClick={() => setShowDescription(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            + Add description
          </button>
        </div>
      )}
      
      <div className="flex justify-end">
        {showDescription && (
          <button
            type="button"
            onClick={() => {
              setShowDescription(false);
              setDescription('');
            }}
            className="px-4 py-2 mr-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:opacity-50"
            disabled={loading}
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          disabled={!title.trim() || loading}
        >
          {loading ? 'Adding...' : 'Add Task'}
        </button>
      </div>
    </form>
  );
}
