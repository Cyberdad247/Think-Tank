import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

export const runtime = 'edge';

// GET /api/auth/session - Get the current user's session
export async function GET(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get session
    const { data: { session }, error } = await supabase.auth.getSession();
    
    if (error) {
      console.error('Error getting session:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    if (!session) {
      return NextResponse.json({ user: null, session: null });
    }
    
    return NextResponse.json({
      user: session.user,
      session: {
        expires_at: session.expires_at,
        access_token: session.access_token,
      },
    });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}