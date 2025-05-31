'use client';

import React from 'react';
import { TaskProvider } from '../context/TaskContext';
import { TaskChecklist } from '../components/TaskChecklist';

export default function TasksPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-8 text-center">Task Management</h1>
      <TaskProvider>
        <TaskChecklist />
      </TaskProvider>
    </div>
  );
}