import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

export const runtime = 'edge';

// POST /api/auth/signin - Sign in a user
export async function POST(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get request body
    const body = await request.json();
    
    // Validate required fields
    if (!body.email || !body.password) {
      return NextResponse.json({ error: 'Email and password are required' }, { status: 400 });
    }
    
    // Sign in user
    const { data, error } = await supabase.auth.signInWithPassword({
      email: body.email,
      password: body.password,
    });
    
    if (error) {
      console.error('Error signing in:', error);
      return NextResponse.json({ error: error.message }, { status: 401 });
    }
    
    return NextResponse.json({
      user: data.user,
      session: data.session,
    });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}