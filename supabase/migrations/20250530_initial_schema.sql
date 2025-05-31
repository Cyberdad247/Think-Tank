-- Enable the pgvector extension first
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create tasks table
CREATE TABLE IF NOT EXISTS public.tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  completed BOOLEAN DEFAULT FALSE NOT NULL,
  order_position INTEGER NOT NULL,
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  completed_at TIMESTAMP WITH TIME ZONE,
  due_date TIMESTAMP WITH TIME ZONE,
  priority TEXT CHECK (priority IN ('none', 'low', 'medium', 'high')),
  tags TEXT[] DEFAULT '{}'::TEXT[]
);

-- Enable Row Level Security
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

-- Create knowledge_items table
CREATE TABLE IF NOT EXISTS public.knowledge_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  meta_data JSONB DEFAULT '{}'::JSONB,
  domain TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  embedding vector(1536)
);

-- Enable Row Level Security
ALTER TABLE public.knowledge_items ENABLE ROW LEVEL SECURITY;

-- Create tal_blocks table
CREATE TABLE IF NOT EXISTS public.tal_blocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  content TEXT NOT NULL,
  block_type TEXT NOT NULL,
  meta_data JSONB DEFAULT '{}'::JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.tal_blocks ENABLE ROW LEVEL SECURITY;

-- Create debates table
CREATE TABLE IF NOT EXISTS public.debates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  summary TEXT,
  experts JSONB DEFAULT '{}'::JSONB,
  rounds INTEGER DEFAULT 0,
  result JSONB DEFAULT '{}'::JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.debates ENABLE ROW LEVEL SECURITY;

-- Create RLS policies

-- Users policies
CREATE POLICY "Users can view their own data" ON public.users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own data" ON public.users
  FOR UPDATE USING (auth.uid() = id);

-- Tasks policies
CREATE POLICY "Users can view their own tasks" ON public.tasks
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own tasks" ON public.tasks
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tasks" ON public.tasks
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tasks" ON public.tasks
  FOR DELETE USING (auth.uid() = user_id);

-- Knowledge items policies
CREATE POLICY "Knowledge items are readable by all authenticated users" ON public.knowledge_items
  FOR SELECT USING (auth.role() = 'authenticated');

-- TAL blocks policies
CREATE POLICY "TAL blocks are readable by all authenticated users" ON public.tal_blocks
  FOR SELECT USING (auth.role() = 'authenticated');

-- Debates policies
CREATE POLICY "Debates are readable by all authenticated users" ON public.debates
  FOR SELECT USING (auth.role() = 'authenticated');

-- Create functions and triggers

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for tasks table
CREATE TRIGGER update_tasks_updated_at
BEFORE UPDATE ON public.tasks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Function to handle task completion
CREATE OR REPLACE FUNCTION handle_task_completion()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.completed = TRUE AND OLD.completed = FALSE THEN
    NEW.completed_at = now();
  ELSIF NEW.completed = FALSE AND OLD.completed = TRUE THEN
    NEW.completed_at = NULL;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for task completion
CREATE TRIGGER handle_task_completion_trigger
BEFORE UPDATE ON public.tasks
FOR EACH ROW
WHEN (NEW.completed IS DISTINCT FROM OLD.completed)
EXECUTE FUNCTION handle_task_completion();

-- Create vector search functions
CREATE OR REPLACE FUNCTION match_knowledge_items(query_embedding vector(1536), match_threshold FLOAT, match_count INT)
RETURNS TABLE (
  id UUID,
  content TEXT,
  meta_data JSONB,
  domain TEXT,
  similarity FLOAT
) LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    ki.id,
    ki.content,
    ki.meta_data,
    ki.domain,
    1 - (ki.embedding <=> query_embedding) AS similarity
  FROM knowledge_items ki
  WHERE 1 - (ki.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;