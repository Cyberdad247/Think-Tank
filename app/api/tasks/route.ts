import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { v4 as uuidv4 } from 'uuid';

export const runtime = 'edge';

// GET /api/tasks - Get all tasks for the authenticated user
export async function GET(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get query parameters
    const { searchParams } = new URL(request.url);
    const skip = parseInt(searchParams.get('skip') || '0');
    const limit = parseInt(searchParams.get('limit') || '100');
    
    // Query tasks
    const { data: tasks, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('user_id', session.user.id)
      .order('order_position', { ascending: true })
      .range(skip, skip + limit - 1);
    
    if (error) {
      console.error('Error fetching tasks:', error);
      return NextResponse.json({ error: 'Failed to fetch tasks' }, { status: 500 });
    }
    
    return NextResponse.json(tasks);
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// POST /api/tasks - Create a new task
export async function POST(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get request body
    const body = await request.json();
    
    // Validate required fields
    if (!body.title) {
      return NextResponse.json({ error: 'Title is required' }, { status: 400 });
    }
    
    // Get the highest order_position
    const { data: highestPositionTask } = await supabase
      .from('tasks')
      .select('order_position')
      .eq('user_id', session.user.id)
      .order('order_position', { ascending: false })
      .limit(1);
    
    const newPosition = highestPositionTask && highestPositionTask.length > 0 
      ? highestPositionTask[0].order_position + 1 
      : 1;
    
    // Create new task
    const { data: newTask, error } = await supabase
      .from('tasks')
      .insert({
        id: uuidv4(),
        title: body.title,
        description: body.description || '',
        completed: body.completed || false,
        order_position: newPosition,
        user_id: session.user.id,
        priority: body.priority || 'none',
        tags: body.tags || [],
        due_date: body.due_date || null
      })
      .select()
      .single();
    
    if (error) {
      console.error('Error creating task:', error);
      return NextResponse.json({ error: 'Failed to create task' }, { status: 500 });
    }
    
    return NextResponse.json(newTask, { status: 201 });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// PUT /api/tasks/reorder - Reorder tasks
export async function PUT(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get request body
    const body = await request.json();
    
    // Validate task_ids
    if (!body.task_ids || !Array.isArray(body.task_ids) || body.task_ids.length === 0) {
      return NextResponse.json({ error: 'task_ids array is required' }, { status: 400 });
    }
    
    // Update order_position for each task
    const updates = body.task_ids.map((taskId: string, index: number) => {
      return supabase
        .from('tasks')
        .update({ order_position: index + 1 })
        .eq('id', taskId)
        .eq('user_id', session.user.id);
    });
    
    await Promise.all(updates);
    
    // Get updated tasks
    const { data: tasks, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('user_id', session.user.id)
      .order('order_position', { ascending: true });
    
    if (error) {
      console.error('Error fetching tasks after reordering:', error);
      return NextResponse.json({ error: 'Failed to fetch tasks after reordering' }, { status: 500 });
    }
    
    return NextResponse.json(tasks);
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}