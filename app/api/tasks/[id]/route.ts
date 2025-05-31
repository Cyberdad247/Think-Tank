import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

export const runtime = 'edge';

// GET /api/tasks/[id] - Get a specific task by ID
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get task by ID
    const { data: task, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('id', params.id)
      .eq('user_id', session.user.id)
      .single();
    
    if (error) {
      if (error.code === 'PGRST116') {
        return NextResponse.json({ error: 'Task not found' }, { status: 404 });
      }
      console.error('Error fetching task:', error);
      return NextResponse.json({ error: 'Failed to fetch task' }, { status: 500 });
    }
    
    return NextResponse.json(task);
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// PUT /api/tasks/[id] - Update a task
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get request body
    const body = await request.json();
    
    // Remove fields that shouldn't be updated directly
    const { id, user_id, created_at, ...updateData } = body;
    
    // Update task
    const { data: updatedTask, error } = await supabase
      .from('tasks')
      .update(updateData)
      .eq('id', params.id)
      .eq('user_id', session.user.id)
      .select()
      .single();
    
    if (error) {
      if (error.code === 'PGRST116') {
        return NextResponse.json({ error: 'Task not found' }, { status: 404 });
      }
      console.error('Error updating task:', error);
      return NextResponse.json({ error: 'Failed to update task' }, { status: 500 });
    }
    
    return NextResponse.json(updatedTask);
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// DELETE /api/tasks/[id] - Delete a task
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Delete task
    const { error } = await supabase
      .from('tasks')
      .delete()
      .eq('id', params.id)
      .eq('user_id', session.user.id);
    
    if (error) {
      console.error('Error deleting task:', error);
      return NextResponse.json({ error: 'Failed to delete task' }, { status: 500 });
    }
    
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}