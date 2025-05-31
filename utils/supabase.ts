import { createClient } from '@supabase/supabase-js';

// Initialize the Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Create a single supabase client for the browser
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Helper function to get authenticated supabase client on the server
export const getServerSupabaseClient = async () => {
  const { createServerClient } = await import('@supabase/auth-helpers-nextjs');
  const { cookies } = await import('next/headers');
  
  const cookieStore = cookies();
  
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
    {
      cookies: {
        get: (name) => cookieStore.get(name)?.value,
        set: (name, value, options) => {
          cookieStore.set({ name, value, ...options });
        },
        remove: (name, options) => {
          cookieStore.set({ name, value: '', ...options });
        },
      },
    }
  );
};

// Types for Supabase tables
export type Tables = {
  users: {
    Row: {
      id: string;
      email: string;
      created_at: string;
      is_active: boolean;
    };
    Insert: {
      id?: string;
      email: string;
      created_at?: string;
      is_active?: boolean;
    };
    Update: {
      id?: string;
      email?: string;
      created_at?: string;
      is_active?: boolean;
    };
  };
  tasks: {
    Row: {
      id: string;
      title: string;
      description: string;
      completed: boolean;
      order_position: number;
      user_id: string;
      created_at: string;
      updated_at: string;
      completed_at?: string;
      due_date?: string;
      priority?: 'none' | 'low' | 'medium' | 'high';
      tags?: string[];
    };
    Insert: {
      id?: string;
      title: string;
      description?: string;
      completed?: boolean;
      order_position: number;
      user_id: string;
      created_at?: string;
      updated_at?: string;
      completed_at?: string;
      due_date?: string;
      priority?: 'none' | 'low' | 'medium' | 'high';
      tags?: string[];
    };
    Update: {
      id?: string;
      title?: string;
      description?: string;
      completed?: boolean;
      order_position?: number;
      user_id?: string;
      created_at?: string;
      updated_at?: string;
      completed_at?: string;
      due_date?: string;
      priority?: 'none' | 'low' | 'medium' | 'high';
      tags?: string[];
    };
  };
  knowledge_items: {
    Row: {
      id: string;
      content: string;
      meta_data: Record<string, any>;
      domain: string;
      created_at: string;
      embedding?: number[];
    };
    Insert: {
      id?: string;
      content: string;
      meta_data?: Record<string, any>;
      domain: string;
      created_at?: string;
      embedding?: number[];
    };
    Update: {
      id?: string;
      content?: string;
      meta_data?: Record<string, any>;
      domain?: string;
      created_at?: string;
      embedding?: number[];
    };
  };
  tal_blocks: {
    Row: {
      id: string;
      name: string;
      content: string;
      block_type: string;
      meta_data: Record<string, any>;
      created_at: string;
    };
    Insert: {
      id?: string;
      name: string;
      content: string;
      block_type: string;
      meta_data?: Record<string, any>;
      created_at?: string;
    };
    Update: {
      id?: string;
      name?: string;
      content?: string;
      block_type?: string;
      meta_data?: Record<string, any>;
      created_at?: string;
    };
  };
  debates: {
    Row: {
      id: string;
      topic: string;
      summary: string;
      experts: Record<string, any>;
      rounds: number;
      result: Record<string, any>;
      created_at: string;
    };
    Insert: {
      id?: string;
      topic: string;
      summary: string;
      experts: Record<string, any>;
      rounds: number;
      result: Record<string, any>;
      created_at?: string;
    };
    Update: {
      id?: string;
      topic?: string;
      summary?: string;
      experts?: Record<string, any>;
      rounds?: number;
      result?: Record<string, any>;
      created_at?: string;
    };
  };
};