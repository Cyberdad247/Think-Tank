import React, { useState, useRef, useEffect, memo } from 'react';
import { Task, useTaskContext } from '@/context/TaskContext';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { 
  CheckCircle, 
  Circle, 
  Edit2, 
  Trash2, 
  Clock, 
  AlertCircle, 
  Tag, 
  ChevronDown, 
  ChevronUp,
  BarChart2
} from 'react-feather';

/**
 * Enhanced TaskItem component with improved UX, animations, and analytics features.
 * 
 * Improvements:
 * - Optimized rendering with React.memo
 * - Smooth animations with framer-motion
 * - Enhanced accessibility
 * - Priority indicators
 * - Due date visualization
 * - Task analytics
 * - Expanded metadata support
 * - Keyboard shortcuts
 */

interface TaskItemProps {
  task: Task;
  index: number;
  isDragging?: boolean;
}

// Define task priority levels and their colors
const PRIORITY_COLORS = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-green-100 text-green-800',
  none: 'bg-gray-100 text-gray-800'
};

// Animation variants for task items
const taskVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, x: -100 }
};

export const TaskItem: React.FC<TaskItemProps> = memo(({ task, index, isDragging = false }) => {
  // Context and state
  const { updateTask, deleteTask, logTaskActivity } = useTaskContext();
  const [isEditing, setIsEditing] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [editedTitle, setEditedTitle] = useState(task.title);
  const [editedDescription, setEditedDescription] = useState(task.description || '');
  const [editedDueDate, setEditedDueDate] = useState(task.dueDate || '');
  const [editedPriority, setEditedPriority] = useState(task.priority || 'none');
  const [editedTags, setEditedTags] = useState(task.tags?.join(', ') || '');
  
  // Refs
  const titleInputRef = useRef<HTMLInputElement>(null);
  const taskItemRef = useRef<HTMLDivElement>(null);
  
  // Effects
  useEffect(() => {
    // Focus title input when editing starts
    if (isEditing && titleInputRef.current) {
      titleInputRef.current.focus();
    }
  }, [isEditing]);
  
  // Calculate if task is overdue
  const isOverdue = task.dueDate && new Date(task.dueDate) < new Date() && !task.completed;
  
  // Format due date for display
  const formattedDueDate = task.dueDate 
    ? format(new Date(task.dueDate), 'MMM d, yyyy')
    : null;
  
  // Calculate task age in days
  const taskAge = task.createdAt 
    ? Math.floor((Date.now() - new Date(task.createdAt).getTime()) / (1000 * 60 * 60 * 24))
    : 0;
  
  // Event handlers
  const handleToggleComplete = () => {
    updateTask(task.id, { completed: !task.completed });
    logTaskActivity(task.id, task.completed ? 'uncompleted' : 'completed');
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = () => {
    if (editedTitle.trim()) {
      const updatedTask = { 
        title: editedTitle,
        description: editedDescription || undefined,
        dueDate: editedDueDate || undefined,
        priority: editedPriority,
        tags: editedTags ? editedTags.split(',').map(tag => tag.trim()) : []
      };
      
      updateTask(task.id, updatedTask);
      logTaskActivity(task.id, 'updated');
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setEditedTitle(task.title);
    setEditedDescription(task.description || '');
    setEditedDueDate(task.dueDate || '');
    setEditedPriority(task.priority || 'none');
    setEditedTags(task.tags?.join(', ') || '');
    setIsEditing(false);
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      deleteTask(task.id);
      logTaskActivity(task.id, 'deleted');
    }
  };
  
  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded);
  };
  
  // Keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isEditing) {
      if (e.key === 'Enter' && e.ctrlKey) {
        handleSave();
      } else if (e.key === 'Escape') {
        handleCancel();
      }
    } else {
      if (e.key === 'e' && e.ctrlKey) {
        e.preventDefault();
        handleEdit();
      } else if (e.key === 'Delete' && e.ctrlKey) {
        e.preventDefault();
        handleDelete();
      } else if (e.key === ' ' && e.ctrlKey) {
        e.preventDefault();
        handleToggleComplete();
      }
    }
  };

  return (
    <motion.div
      ref={taskItemRef}
      className={`flex flex-col p-3 border rounded-lg mb-2 shadow-sm group transition-colors ${
        isDragging ? 'shadow-md bg-blue-50' : 'hover:bg-gray-50'
      } ${task.completed ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-200'}`}
      variants={taskVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={{ duration: 0.2 }}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      aria-label={`Task: ${task.title}, Status: ${task.completed ? 'completed' : 'active'}`}
      data-testid={`task-item-${task.id}`}
    >
      <div className="flex items-center">
        {/* Completion toggle */}
        <button
          type="button"
          onClick={handleToggleComplete}
          className="h-6 w-6 flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full"
          aria-label={task.completed ? "Mark as incomplete" : "Mark as complete"}
        >
          {task.completed ? (
            <CheckCircle className="text-green-500" size={24} />
          ) : (
            <Circle className="text-gray-400 hover:text-blue-500" size={24} />
          )}
        </button>
        
        {isEditing ? (
          <div className="flex-1 ml-3 flex flex-col">
            {/* Edit form */}
            <input
              ref={titleInputRef}
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
              placeholder="Task title"
              aria-label="Task title"
            />
            
            <textarea
              value={editedDescription}
              onChange={(e) => setEditedDescription(e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
              placeholder="Description (optional)"
              rows={2}
              aria-label="Task description"
            />
            
            <div className="grid grid-cols-2 gap-2 mb-2">
              <div>
                <label htmlFor={`due-date-${task.id}`} className="block text-sm text-gray-600 mb-1">
                  Due Date
                </label>
                <input
                  id={`due-date-${task.id}`}
                  type="date"
                  value={editedDueDate}
                  onChange={(e) => setEditedDueDate(e.target.value)}
                  className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label htmlFor={`priority-${task.id}`} className="block text-sm text-gray-600 mb-1">
                  Priority
                </label>
                <select
                  id={`priority-${task.id}`}
                  value={editedPriority}
                  onChange={(e) => setEditedPriority(e.target.value)}
                  className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="none">None</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            
            <div className="mb-2">
              <label htmlFor={`tags-${task.id}`} className="block text-sm text-gray-600 mb-1">
                Tags (comma separated)
              </label>
              <input
                id={`tags-${task.id}`}
                type="text"
                value={editedTags}
                onChange={(e) => setEditedTags(e.target.value)}
                className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="work, personal, urgent"
              />
            </div>
            
            <div className="flex mt-2">
              <button 
                onClick={handleSave}
                className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500"
                aria-label="Save task"
              >
                Save
              </button>
              <button 
                onClick={handleCancel}
                className="ml-2 px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                aria-label="Cancel editing"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 ml-3">
              {/* Task title and description */}
              <div className="flex items-center">
                <span 
                  className={`block font-medium ${task.completed ? 'line-through text-gray-500' : ''}`}
                >
                  {task.title}
                </span>
                
                {/* Priority indicator */}
                {task.priority && task.priority !== 'none' && (
                  <span 
                    className={`ml-2 px-2 py-0.5 text-xs rounded-full ${PRIORITY_COLORS[task.priority as keyof typeof PRIORITY_COLORS]}`}
                  >
                    {task.priority}
                  </span>
                )}
              </div>
              
              {/* Due date */}
              {formattedDueDate && (
                <div className={`flex items-center text-sm mt-1 ${
                  isOverdue ? 'text-red-600' : 'text-gray-500'
                }`}>
                  <Clock size={14} className="mr-1" />
                  <span>{formattedDueDate}</span>
                  {isOverdue && (
                    <span className="ml-2 text-red-600 flex items-center">
                      <AlertCircle size={14} className="mr-1" />
                      Overdue
                    </span>
                  )}
                </div>
              )}
              
              {/* Tags */}
              {task.tags && task.tags.length > 0 && (
                <div className="flex flex-wrap items-center mt-1">
                  <Tag size={14} className="text-gray-500 mr-1" />
                  {task.tags.map((tag, i) => (
                    <span 
                      key={i} 
                      className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded mr-1 mb-1"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              
              {/* Preview of description */}
              {task.description && !isExpanded && (
                <p className={`text-sm mt-1 line-clamp-1 ${task.completed ? 'line-through text-gray-400' : 'text-gray-600'}`}>
                  {task.description}
                </p>
              )}
            </div>
            
            {/* Action buttons */}
            <div className="flex items-center">
              <button 
                onClick={handleToggleExpand}
                className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                aria-label={isExpanded ? "Collapse task details" : "Expand task details"}
              >
                {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
              
              <button 
                onClick={handleEdit}
                className="p-1 text-gray-400 hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                aria-label="Edit task"
              >
                <Edit2 size={18} />
              </button>
              
              <button 
                onClick={handleDelete}
                className="p-1 text-gray-400 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                aria-label="Delete task"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </>
        )}
      </div>
      
      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && !isEditing && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="mt-3 pt-3 border-t border-gray-200"
          >
            {/* Full description */}
            {task.description && (
              <div className="mb-3">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Description</h4>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{task.description}</p>
              </div>
            )}
            
            {/* Task analytics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center">
                <BarChart2 size={16} className="text-gray-500 mr-2" />
                <div>
                  <h4 className="text-xs font-medium text-gray-700">Task Age</h4>
                  <p className="text-sm">{taskAge} days</p>
                </div>
              </div>
              
              {task.completedAt && (
                <div className="flex items-center">
                  <CheckCircle size={16} className="text-green-500 mr-2" />
                  <div>
                    <h4 className="text-xs font-medium text-gray-700">Completed</h4>
                    <p className="text-sm">{format(new Date(task.completedAt), 'MMM d, yyyy')}</p>
                  </div>
                </div>
              )}
              
              {task.createdAt && (
                <div className="flex items-center">
                  <Clock size={16} className="text-gray-500 mr-2" />
                  <div>
                    <h4 className="text-xs font-medium text-gray-700">Created</h4>
                    <p className="text-sm">{format(new Date(task.createdAt), 'MMM d, yyyy')}</p>
                  </div>
                </div>
              )}
              
              {task.updatedAt && task.updatedAt !== task.createdAt && (
                <div className="flex items-center">
                  <Edit2 size={16} className="text-gray-500 mr-2" />
                  <div>
                    <h4 className="text-xs font-medium text-gray-700">Last Updated</h4>
                    <p className="text-sm">{format(new Date(task.updatedAt), 'MMM d, yyyy')}</p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
});

TaskItem.displayName = 'TaskItem';
