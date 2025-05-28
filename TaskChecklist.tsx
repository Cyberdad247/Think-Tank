import React, { useState } from 'react';
import { useTaskContext } from '@/context/TaskContext';
import { TaskItem } from './TaskItem';
import { TaskForm } from './TaskForm';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';

type FilterType = 'all' | 'active' | 'completed';

export const TaskChecklist: React.FC = () => {
  const { tasks, loading, error, reorderTasks } = useTaskContext();
  const [filter, setFilter] = useState<FilterType>('all');

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true;
    if (filter === 'active') return !task.completed;
    if (filter === 'completed') return task.completed;
    return true;
  });

  const handleDragEnd = (result: DropResult) => {
    const { destination, source } = result;

    // If dropped outside the list or no movement
    if (!destination || 
        (destination.droppableId === source.droppableId && 
         destination.index === source.index)) {
      return;
    }

    // Create a new array of task IDs in the new order
    const taskIds = Array.from(tasks.map(t => t.id));
    const [removed] = taskIds.splice(source.index, 1);
    taskIds.splice(destination.index, 0, removed);

    // Update the order in the backend
    reorderTasks(taskIds);
  };

  if (error) {
    return <div className="p-4 text-red-600 bg-red-100 rounded">Error: {error}</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-6">Task Checklist</h2>
      
      <TaskForm />
      
      <div className="mb-4 flex space-x-2">
        <button 
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          All
        </button>
        <button 
          onClick={() => setFilter('active')}
          className={`px-3 py-1 rounded ${filter === 'active' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Active
        </button>
        <button 
          onClick={() => setFilter('completed')}
          className={`px-3 py-1 rounded ${filter === 'completed' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Completed
        </button>
      </div>
      
      {loading ? (
        <div className="flex justify-center p-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="p-4 text-center text-gray-500">
          {filter === 'all' 
            ? 'No tasks yet. Add one above!' 
            : filter === 'active' 
              ? 'No active tasks.' 
              : 'No completed tasks.'}
        </div>
      ) : (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="tasks">
            {(provided) => (
              <div
                {...provided.droppableProps}
                ref={provided.innerRef}
                className="border border-gray-200 rounded"
              >
                {filteredTasks.map((task, index) => (
                  <Draggable key={task.id} draggableId={task.id.toString()} index={index}>
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                      >
                        <TaskItem task={task} />
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      )}
      
      <div className="mt-4 text-sm text-gray-600">
        {tasks.length > 0 && (
          <>
            <span>{tasks.filter(t => !t.completed).length} remaining</span>
            {' / '}
            <span>{tasks.length} total</span>
          </>
        )}
      </div>
    </div>
  );
}
