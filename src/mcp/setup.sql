-- Create notes table
CREATE TABLE IF NOT EXISTS notes (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  title text NOT NULL,
  content text NOT NULL,
  category text DEFAULT 'general',
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_message text NOT NULL,
  assistant_response text NOT NULL,
  tools_used jsonb,
  created_at timestamp with time zone DEFAULT now()
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  title text NOT NULL,
  description text,
  status text DEFAULT 'pending',
  due_date timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone
);

-- Disable Row Level Security (no restrictions)
ALTER TABLE notes DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE tasks DISABLE ROW LEVEL SECURITY;

-- Drop any existing policies
DROP POLICY IF EXISTS "Allow anonymous access" ON notes;
DROP POLICY IF EXISTS "Allow anonymous access" ON conversations;
DROP POLICY IF EXISTS "Allow anonymous access" ON tasks;

-- Grant all permissions to anonymous users (no security)
GRANT ALL ON notes TO anon;
GRANT ALL ON conversations TO anon;
GRANT ALL ON tasks TO anon;

-- Grant permissions for the sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;