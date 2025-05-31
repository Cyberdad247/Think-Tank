import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

export const runtime = 'edge';

// POST /api/auth/signup - Sign up a new user
export async function POST(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get request body
    const body = await request.json();
    
    // Validate required fields
    if (!body.email || !body.password) {
      return NextResponse.json({ error: 'Email and password are required' }, { status: 400 });
    }
    
    // Sign up user
    const { data, error } = await supabase.auth.signUp({
      email: body.email,
      password: body.password,
      options: {
        data: {
          full_name: body.full_name || '',
        },
      },
    });
    
    if (error) {
      console.error('Error signing up:', error);
      return NextResponse.json({ error: error.message }, { status: 400 });
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