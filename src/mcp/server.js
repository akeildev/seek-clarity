#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema
} from '@modelcontextprotocol/sdk/types.js';
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

let supabase = null;
if (supabaseUrl && supabaseKey) {
  supabase = createClient(supabaseUrl, supabaseKey);
  console.error('[MCP] Supabase client initialized');
} else {
  console.error('[MCP] Warning: Supabase credentials not found');
}

// Create MCP server
const server = new Server(
  {
    name: 'clarity-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
const TOOLS = [
  {
    name: 'create_note',
    description: 'Create a new note in the database',
    inputSchema: {
      type: 'object',
      properties: {
        title: {
          type: 'string',
          description: 'Title of the note',
        },
        content: {
          type: 'string',
          description: 'Content of the note',
        },
        category: {
          type: 'string',
          description: 'Category of the note (optional)',
          default: 'general',
        },
      },
      required: ['title', 'content'],
    },
  },
  {
    name: 'search_notes',
    description: 'Search for notes in the database',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query',
        },
        category: {
          type: 'string',
          description: 'Filter by category (optional)',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'get_note',
    description: 'Get a specific note by ID',
    inputSchema: {
      type: 'object',
      properties: {
        id: {
          type: 'string',
          description: 'ID of the note',
        },
      },
      required: ['id'],
    },
  },
  {
    name: 'update_note',
    description: 'Update an existing note',
    inputSchema: {
      type: 'object',
      properties: {
        id: {
          type: 'string',
          description: 'ID of the note to update',
        },
        title: {
          type: 'string',
          description: 'New title (optional)',
        },
        content: {
          type: 'string',
          description: 'New content (optional)',
        },
        category: {
          type: 'string',
          description: 'New category (optional)',
        },
      },
      required: ['id'],
    },
  },
  {
    name: 'delete_note',
    description: 'Delete a note',
    inputSchema: {
      type: 'object',
      properties: {
        id: {
          type: 'string',
          description: 'ID of the note to delete',
        },
      },
      required: ['id'],
    },
  },
  {
    name: 'list_categories',
    description: 'List all note categories',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
];

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS,
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  console.error(`[MCP] Executing tool: ${name}`, args);

  try {
    switch (name) {
      case 'create_note': {
        if (!supabase) {
          return {
            content: [
              {
                type: 'text',
                text: 'Database not connected. Please configure Supabase credentials.',
              },
            ],
          };
        }

        const { data, error } = await supabase
          .from('notes')
          .insert([
            {
              title: args.title,
              content: args.content,
              category: args.category || 'general',
              created_at: new Date().toISOString(),
            },
          ])
          .select()
          .single();

        if (error) throw error;

        return {
          content: [
            {
              type: 'text',
              text: `Note created successfully: ${data.title} (ID: ${data.id})`,
            },
          ],
        };
      }

      case 'search_notes': {
        if (!supabase) {
          return {
            content: [
              {
                type: 'text',
                text: 'Database not connected. Please configure Supabase credentials.',
              },
            ],
          };
        }

        let query = supabase
          .from('notes')
          .select('*')
          .ilike('title', `%${args.query}%`);

        if (args.category) {
          query = query.eq('category', args.category);
        }

        const { data, error } = await query;

        if (error) throw error;

        const results = data.map(note =>
          `- ${note.title} (${note.category}): ${note.content.substring(0, 100)}...`
        ).join('\n');

        return {
          content: [
            {
              type: 'text',
              text: data.length > 0
                ? `Found ${data.length} notes:\n${results}`
                : 'No notes found matching your query.',
            },
          ],
        };
      }

      case 'get_note': {
        if (!supabase) {
          return {
            content: [
              {
                type: 'text',
                text: 'Database not connected. Please configure Supabase credentials.',
              },
            ],
          };
        }

        const { data, error } = await supabase
          .from('notes')
          .select('*')
          .eq('id', args.id)
          .single();

        if (error) throw error;

        return {
          content: [
            {
              type: 'text',
              text: `Title: ${data.title}\nCategory: ${data.category}\nContent: ${data.content}`,
            },
          ],
        };
      }

      case 'update_note': {
        if (!supabase) {
          return {
            content: [
              {
                type: 'text',
                text: 'Database not connected. Please configure Supabase credentials.',
              },
            ],
          };
        }

        const updates = {};
        if (args.title) updates.title = args.title;
        if (args.content) updates.content = args.content;
        if (args.category) updates.category = args.category;
        updates.updated_at = new Date().toISOString();

        const { data, error } = await supabase
          .from('notes')
          .update(updates)
          .eq('id', args.id)
          .select()
          .single();

        if (error) throw error;

        return {
          content: [
            {
              type: 'text',
              text: `Note updated successfully: ${data.title}`,
            },
          ],
        };
      }

      case 'delete_note': {
        if (!supabase) {
          return {
            content: [
              {
                type: 'text',
                text: 'Database not connected. Please configure Supabase credentials.',
              },
            ],
          };
        }

        const { error } = await supabase
          .from('notes')
          .delete()
          .eq('id', args.id);

        if (error) throw error;

        return {
          content: [
            {
              type: 'text',
              text: 'Note deleted successfully.',
            },
          ],
        };
      }

      case 'list_categories': {
        if (!supabase) {
          return {
            content: [
              {
                type: 'text',
                text: 'Database not connected. Please configure Supabase credentials.',
              },
            ],
          };
        }

        const { data, error } = await supabase
          .from('notes')
          .select('category')
          .distinct();

        if (error) throw error;

        const categories = [...new Set(data.map(item => item.category))];

        return {
          content: [
            {
              type: 'text',
              text: `Available categories:\n${categories.map(c => `- ${c}`).join('\n')}`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    console.error(`[MCP] Error executing ${name}:`, error);
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('[MCP] Server started successfully');
}

main().catch((error) => {
  console.error('[MCP] Server error:', error);
  process.exit(1);
});