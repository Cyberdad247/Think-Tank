import React, { useState, useEffect, useMemo } from 'react';
import { useTaskContext, Task } from '@/context/TaskContext';
import { 
  BarChart2, 
  PieChart, 
  Calendar, 
  Clock, 
  Tag, 
  CheckCircle, 
  Circle, 
  AlertTriangle,
  Filter,
  Download
} from 'react-feather';
import { format, isAfter, isBefore, addDays, startOfWeek, endOfWeek, isWithinInterval } from 'date-fns';

/**
 * TaskDashboard component with analytics features.
 * 
 * This component provides:
 * - Task completion statistics
 * - Due date analytics
 * - Priority distribution
 * - Tag analysis
 * - Task age metrics
 * - Export functionality
 */

interface TaskStats {
  total: number;
  completed: number;
  active: number;
  overdue: number;
  completionRate: number;
  averageCompletionTime: number;
  priorityDistribution: Record<string, number>;
  tagDistribution: Record<string, number>;
  dueDateDistribution: {
    today: number;
    thisWeek: number;
    nextWeek: number;
    later: number;
    noDueDate: number;
  };
}

interface ChartData {
  labels: string[];
  values: number[];
  colors: string[];
}

export const TaskDashboard: React.FC = () => {
  const { tasks } = useTaskContext();
  const [timeFrame, setTimeFrame] = useState<'all' | 'week' | 'month'>('all');
  const [filterTag, setFilterTag] = useState<string | null>(null);
  const [filterPriority, setFilterPriority] = useState<string | null>(null);
  
  // Calculate filtered tasks based on selected filters
  const filteredTasks = useMemo(() => {
    let result = [...tasks];
    
    // Apply time frame filter
    if (timeFrame === 'week') {
      const oneWeekAgo = addDays(new Date(), -7);
      result = result.filter(task => {
        const taskDate = task.updatedAt || task.createdAt;
        return taskDate && isAfter(new Date(taskDate), oneWeekAgo);
      });
    } else if (timeFrame === 'month') {
      const oneMonthAgo = addDays(new Date(), -30);
      result = result.filter(task => {
        const taskDate = task.updatedAt || task.createdAt;
        return taskDate && isAfter(new Date(taskDate), oneMonthAgo);
      });
    }
    
    // Apply tag filter
    if (filterTag) {
      result = result.filter(task => 
        task.tags && task.tags.some(tag => tag.toLowerCase() === filterTag.toLowerCase())
      );
    }
    
    // Apply priority filter
    if (filterPriority) {
      result = result.filter(task => task.priority === filterPriority);
    }
    
    return result;
  }, [tasks, timeFrame, filterTag, filterPriority]);
  
  // Calculate task statistics
  const taskStats: TaskStats = useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const thisWeekStart = startOfWeek(today);
    const thisWeekEnd = endOfWeek(today);
    const nextWeekStart = addDays(thisWeekEnd, 1);
    const nextWeekEnd = endOfWeek(nextWeekStart);
    
    const stats: TaskStats = {
      total: filteredTasks.length,
      completed: filteredTasks.filter(t => t.completed).length,
      active: filteredTasks.filter(t => !t.completed).length,
      overdue: filteredTasks.filter(t => 
        t.dueDate && 
        isBefore(new Date(t.dueDate), today) && 
        !t.completed
      ).length,
      completionRate: 0,
      averageCompletionTime: 0,
      priorityDistribution: {
        high: 0,
        medium: 0,
        low: 0,
        none: 0
      },
      tagDistribution: {},
      dueDateDistribution: {
        today: 0,
        thisWeek: 0,
        nextWeek: 0,
        later: 0,
        noDueDate: 0
      }
    };
    
    // Calculate completion rate
    stats.completionRate = stats.total > 0 
      ? Math.round((stats.completed / stats.total) * 100) 
      : 0;
    
    // Calculate average completion time
    const completedWithDates = filteredTasks.filter(
      t => t.completed && t.completedAt && t.createdAt
    );
    
    if (completedWithDates.length > 0) {
      const totalDays = completedWithDates.reduce((sum, task) => {
        const created = new Date(task.createdAt!);
        const completed = new Date(task.completedAt!);
        const days = Math.round((completed.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
        return sum + days;
      }, 0);
      
      stats.averageCompletionTime = Math.round(totalDays / completedWithDates.length);
    }
    
    // Calculate priority distribution
    filteredTasks.forEach(task => {
      const priority = task.priority || 'none';
      stats.priorityDistribution[priority] = (stats.priorityDistribution[priority] || 0) + 1;
    });
    
    // Calculate tag distribution
    filteredTasks.forEach(task => {
      if (task.tags && task.tags.length > 0) {
        task.tags.forEach(tag => {
          stats.tagDistribution[tag] = (stats.tagDistribution[tag] || 0) + 1;
        });
      }
    });
    
    // Calculate due date distribution
    filteredTasks.forEach(task => {
      if (!task.dueDate) {
        stats.dueDateDistribution.noDueDate++;
      } else {
        const dueDate = new Date(task.dueDate);
        
        if (dueDate.toDateString() === today.toDateString()) {
          stats.dueDateDistribution.today++;
        } else if (isWithinInterval(dueDate, { start: thisWeekStart, end: thisWeekEnd })) {
          stats.dueDateDistribution.thisWeek++;
        } else if (isWithinInterval(dueDate, { start: nextWeekStart, end: nextWeekEnd })) {
          stats.dueDateDistribution.nextWeek++;
        } else {
          stats.dueDateDistribution.later++;
        }
      }
    });
    
    return stats;
  }, [filteredTasks]);
  
  // Prepare chart data for priority distribution
  const priorityChartData: ChartData = useMemo(() => {
    return {
      labels: Object.keys(taskStats.priorityDistribution),
      values: Object.values(taskStats.priorityDistribution),
      colors: ['#EF4444', '#F59E0B', '#10B981', '#9CA3AF']
    };
  }, [taskStats.priorityDistribution]);
  
  // Prepare chart data for due date distribution
  const dueDateChartData: ChartData = useMemo(() => {
    return {
      labels: ['Today', 'This Week', 'Next Week', 'Later', 'No Due Date'],
      values: [
        taskStats.dueDateDistribution.today,
        taskStats.dueDateDistribution.thisWeek,
        taskStats.dueDateDistribution.nextWeek,
        taskStats.dueDateDistribution.later,
        taskStats.dueDateDistribution.noDueDate
      ],
      colors: ['#EF4444', '#F59E0B', '#10B981', '#6366F1', '#9CA3AF']
    };
  }, [taskStats.dueDateDistribution]);
  
  // Get top tags
  const topTags = useMemo(() => {
    return Object.entries(taskStats.tagDistribution)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  }, [taskStats.tagDistribution]);
  
  // Handle export to CSV
  const handleExportCSV = () => {
    // Create CSV content
    const headers = ['Title', 'Description', 'Status', 'Priority', 'Due Date', 'Tags', 'Created At', 'Updated At', 'Completed At'];
    const rows = filteredTasks.map(task => [
      `"${task.title.replace(/"/g, '""')}"`,
      `"${(task.description || '').replace(/"/g, '""')}"`,
      task.completed ? 'Completed' : 'Active',
      task.priority || 'None',
      task.dueDate || '',
      `"${(task.tags || []).join(', ')}"`,
      task.createdAt || '',
      task.updatedAt || '',
      task.completedAt || ''
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `tasks-export-${format(new Date(), 'yyyy-MM-dd')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // Simple bar chart component
  const BarChart: React.FC<{ data: ChartData, height?: number }> = ({ data, height = 150 }) => {
    const maxValue = Math.max(...data.values, 1);
    
    return (
      <div className="flex items-end h-full space-x-2">
        {data.values.map((value, index) => (
          <div key={index} className="flex flex-col items-center">
            <div 
              className="w-8 rounded-t" 
              style={{ 
                height: `${(value / maxValue) * height}px`,
                backgroundColor: data.colors[index] 
              }}
            />
            <span className="text-xs mt-1">{data.labels[index]}</span>
            <span className="text-xs font-medium">{value}</span>
          </div>
        ))}
      </div>
    );
  };
  
  // Simple donut chart component
  const DonutChart: React.FC<{ data: ChartData }> = ({ data }) => {
    const total = data.values.reduce((sum, val) => sum + val, 0);
    let startAngle = 0;
    
    return (
      <div className="relative w-32 h-32">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          {data.values.map((value, index) => {
            if (value === 0) return null;
            
            const angle = (value / total) * 360;
            const endAngle = startAngle + angle;
            
            // Calculate SVG arc path
            const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
            const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
            const x2 = 50 + 40 * Math.cos((endAngle * Math.PI) / 180);
            const y2 = 50 + 40 * Math.sin((endAngle * Math.PI) / 180);
            
            const largeArcFlag = angle > 180 ? 1 : 0;
            const path = `M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
            
            const result = (
              <path
                key={index}
                d={path}
                fill={data.colors[index]}
                stroke="#fff"
                strokeWidth="1"
              />
            );
            
            startAngle = endAngle;
            return result;
          })}
          <circle cx="50" cy="50" r="25" fill="white" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold">{taskStats.completionRate}%</span>
        </div>
      </div>
    );
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800">Task Analytics Dashboard</h2>
        
        <div className="flex space-x-2">
          {/* Time frame filter */}
          <select
            value={timeFrame}
            onChange={(e) => setTimeFrame(e.target.value as any)}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Select time frame"
          >
            <option value="all">All Time</option>
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
          </select>
          
          {/* Export button */}
          <button
            onClick={handleExportCSV}
            className="flex items-center px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Export to CSV"
          >
            <Download size={16} className="mr-1" />
            Export
          </button>
        </div>
      </div>
      
      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
          <div className="flex items-center">
            <BarChart2 className="text-blue-500 mr-3" size={24} />
            <div>
              <h3 className="text-sm font-medium text-gray-500">Total Tasks</h3>
              <p className="text-2xl font-bold text-gray-800">{taskStats.total}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg border border-green-100">
          <div className="flex items-center">
            <CheckCircle className="text-green-500 mr-3" size={24} />
            <div>
              <h3 className="text-sm font-medium text-gray-500">Completed</h3>
              <p className="text-2xl font-bold text-gray-800">{taskStats.completed}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100">
          <div className="flex items-center">
            <Circle className="text-yellow-500 mr-3" size={24} />
            <div>
              <h3 className="text-sm font-medium text-gray-500">Active</h3>
              <p className="text-2xl font-bold text-gray-800">{taskStats.active}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg border border-red-100">
          <div className="flex items-center">
            <AlertTriangle className="text-red-500 mr-3" size={24} />
            <div>
              <h3 className="text-sm font-medium text-gray-500">Overdue</h3>
              <p className="text-2xl font-bold text-gray-800">{taskStats.overdue}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Charts section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Completion rate chart */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-700 mb-4">Completion Rate</h3>
          <div className="flex items-center">
            <DonutChart data={priorityChartData} />
            <div className="ml-4">
              <div className="mb-2">
                <span className="text-2xl font-bold">{taskStats.completionRate}%</span>
                <span className="text-sm text-gray-500 ml-2">tasks completed</span>
              </div>
              <div className="text-sm text-gray-600">
                <p>Average completion time: {taskStats.averageCompletionTime} days</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Priority distribution chart */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-700 mb-4">Priority Distribution</h3>
          <div className="h-40">
            <BarChart data={priorityChartData} />
          </div>
        </div>
        
        {/* Due date distribution chart */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-700 mb-4">Due Date Distribution</h3>
          <div className="h-40">
            <BarChart data={dueDateChartData} />
          </div>
        </div>
        
        {/* Top tags */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-700 mb-4">Top Tags</h3>
          {topTags.length > 0 ? (
            <div className="space-y-2">
              {topTags.map(([tag, count]) => (
                <div key={tag} className="flex items-center">
                  <div 
                    className="w-full bg-gray-200 rounded-full h-2.5"
                    onClick={() => setFilterTag(filterTag === tag ? null : tag)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full" 
                      style={{ width: `${(count / filteredTasks.length) * 100}%` }}
                    />
                  </div>
                  <span className="ml-2 text-sm">{tag} ({count})</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No tags found</p>
          )}
        </div>
      </div>
      
      {/* Filters section */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 mb-6">
        <div className="flex items-center mb-3">
          <Filter size={18} className="text-gray-500 mr-2" />
          <h3 className="text-lg font-medium text-gray-700">Filters</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Tag filter */}
          <div>
            <label htmlFor="tag-filter" className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Tag
            </label>
            <select
              id="tag-filter"
              value={filterTag || ''}
              onChange={(e) => setFilterTag(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Tags</option>
              {Object.keys(taskStats.tagDistribution).map(tag => (
                <option key={tag} value={tag}>{tag} ({taskStats.tagDistribution[tag]})</option>
              ))}
            </select>
          </div>
          
          {/* Priority filter */}
          <div>
            <label htmlFor="priority-filter" className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Priority
            </label>
            <select
              id="priority-filter"
              value={filterPriority || ''}
              onChange={(e) => setFilterPriority(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Priorities</option>
              <option value="high">High ({taskStats.priorityDistribution.high || 0})</option>
              <option value="medium">Medium ({taskStats.priorityDistribution.medium || 0})</option>
              <option value="low">Low ({taskStats.priorityDistribution.low || 0})</option>
              <option value="none">None ({taskStats.priorityDistribution.none || 0})</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Task activity timeline - simplified version */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h3 className="text-lg font-medium text-gray-700 mb-4">Recent Activity</h3>
        
        {filteredTasks.length > 0 ? (
          <div className="space-y-3 max-h-60 overflow-y-auto">
            {filteredTasks
              .sort((a, b) => {
                const dateA = new Date(a.updatedAt || a.createdAt || 0);
                const dateB = new Date(b.updatedAt || b.createdAt || 0);
                return dateB.getTime() - dateA.getTime();
              })
              .slice(0, 5)
              .map(task => (
                <div key={task.id} className="flex items-start">
                  <div className={`mt-1 rounded-full p-1 ${task.completed ? 'bg-green-100' : 'bg-yellow-100'}`}>
                    {task.completed ? (
                      <CheckCircle size={16} className="text-green-500" />
                    ) : (
                      <Circle size={16} className="text-yellow-500" />
                    )}
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium">{task.title}</p>
                    <p className="text-xs text-gray-500">
                      {task.updatedAt 
                        ? `Updated ${format(new Date(task.updatedAt), 'MMM d, yyyy')}`
                        : `Created ${format(new Date(task.createdAt || new Date()), 'MMM d, yyyy')}`
                      }
                    </p>
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No tasks found</p>
        )}
      </div>
    </div>
  );
};