// Supabase database configuration and helpers
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, '../../.env') });

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

export let supabase = null;

if (supabaseUrl && supabaseKey) {
  supabase = createClient(supabaseUrl, supabaseKey);
  console.error('[Database] Supabase client initialized');
} else {
  console.error('[Database] Warning: Supabase credentials not found');
}

// Database schema setup
export const SCHEMA = {
  notes: `
    CREATE TABLE IF NOT EXISTS notes (
      id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
      title text NOT NULL,
      content text NOT NULL,
      category text DEFAULT 'general',
      created_at timestamp with time zone DEFAULT now(),
      updated_at timestamp with time zone DEFAULT now()
    );
  `,

  conversations: `
    CREATE TABLE IF NOT EXISTS conversations (
      id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
      user_message text NOT NULL,
      assistant_response text NOT NULL,
      tools_used jsonb,
      created_at timestamp with time zone DEFAULT now()
    );
  `,

  tasks: `
    CREATE TABLE IF NOT EXISTS tasks (
      id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
      title text NOT NULL,
      description text,
      status text DEFAULT 'pending',
      due_date timestamp with time zone,
      created_at timestamp with time zone DEFAULT now(),
      completed_at timestamp with time zone
    );
  `
};

// Database helper functions
export const db = {
  // Notes operations
  notes: {
    async create({ title, content, category = 'general' }) {
      if (!supabase) throw new Error('Database not connected');

      const { data, error } = await supabase
        .from('notes')
        .insert([{ title, content, category }])
        .select()
        .single();

      if (error) throw error;
      return data;
    },

    async search(query, category = null) {
      if (!supabase) throw new Error('Database not connected');

      let q = supabase.from('notes').select('*');

      if (query) {
        q = q.or(`title.ilike.%${query}%,content.ilike.%${query}%`);
      }

      if (category) {
        q = q.eq('category', category);
      }

      const { data, error } = await q;
      if (error) throw error;
      return data;
    },

    async get(id) {
      if (!supabase) throw new Error('Database not connected');

      const { data, error } = await supabase
        .from('notes')
        .select('*')
        .eq('id', id)
        .single();

      if (error) throw error;
      return data;
    },

    async update(id, updates) {
      if (!supabase) throw new Error('Database not connected');

      const { data, error } = await supabase
        .from('notes')
        .update({ ...updates, updated_at: new Date().toISOString() })
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;
      return data;
    },

    async delete(id) {
      if (!supabase) throw new Error('Database not connected');

      const { error } = await supabase
        .from('notes')
        .delete()
        .eq('id', id);

      if (error) throw error;
      return true;
    }
  },

  // Conversations operations
  conversations: {
    async save(userMessage, assistantResponse, toolsUsed = []) {
      if (!supabase) throw new Error('Database not connected');

      const { data, error } = await supabase
        .from('conversations')
        .insert([{
          user_message: userMessage,
          assistant_response: assistantResponse,
          tools_used: toolsUsed
        }])
        .select()
        .single();

      if (error) throw error;
      return data;
    },

    async getRecent(limit = 10) {
      if (!supabase) throw new Error('Database not connected');

      const { data, error } = await supabase
        .from('conversations')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) throw error;
      return data;
    }
  },

  // Tasks operations
  tasks: {
    async create({ title, description, dueDate }) {
      if (!supabase) throw new Error('Database not connected');

      const { data, error } = await supabase
        .from('tasks')
        .insert([{
          title,
          description,
          due_date: dueDate
        }])
        .select()
        .single();

      if (error) throw error;
      return data;
    },

    async list(status = null) {
      if (!supabase) throw new Error('Database not connected');

      let q = supabase.from('tasks').select('*');

      if (status) {
        q = q.eq('status', status);
      }

      const { data, error } = await q.order('created_at', { ascending: false });
      if (error) throw error;
      return data;
    },

    async updateStatus(id, status) {
      if (!supabase) throw new Error('Database not connected');

      const updates = { status };
      if (status === 'completed') {
        updates.completed_at = new Date().toISOString();
      }

      const { data, error } = await supabase
        .from('tasks')
        .update(updates)
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;
      return data;
    }
  }
};

// Initialize database tables
export async function initializeDatabase() {
  if (!supabase) {
    console.error('[Database] Cannot initialize - no connection');
    return false;
  }

  try {
    // Check if tables exist by attempting to query them
    const tables = ['notes', 'conversations', 'tasks'];

    for (const table of tables) {
      const { error } = await supabase.from(table).select('id').limit(1);

      if (error && error.code === '42P01') {
        console.error(`[Database] Table '${table}' does not exist. Please create it in Supabase dashboard.`);
      }
    }

    console.error('[Database] Database initialized successfully');
    return true;
  } catch (error) {
    console.error('[Database] Initialization error:', error);
    return false;
  }
}

export default {
  supabase,
  db,
  initializeDatabase
};