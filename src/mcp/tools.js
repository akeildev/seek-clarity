// Tool definitions and handlers for MCP server
export const toolDefinitions = {
  // System tools
  system: {
    execute_command: {
      description: 'Execute a system command',
      parameters: {
        command: { type: 'string', required: true },
        args: { type: 'array', items: { type: 'string' } }
      }
    },
    get_system_info: {
      description: 'Get system information',
      parameters: {}
    }
  },

  // File system tools
  filesystem: {
    read_file: {
      description: 'Read a file from the filesystem',
      parameters: {
        path: { type: 'string', required: true }
      }
    },
    write_file: {
      description: 'Write content to a file',
      parameters: {
        path: { type: 'string', required: true },
        content: { type: 'string', required: true }
      }
    },
    list_directory: {
      description: 'List contents of a directory',
      parameters: {
        path: { type: 'string', required: true }
      }
    }
  },

  // Web tools
  web: {
    search: {
      description: 'Search the web',
      parameters: {
        query: { type: 'string', required: true },
        limit: { type: 'number', default: 5 }
      }
    },
    fetch_url: {
      description: 'Fetch content from a URL',
      parameters: {
        url: { type: 'string', required: true }
      }
    }
  },

  // Calendar tools
  calendar: {
    create_event: {
      description: 'Create a calendar event',
      parameters: {
        title: { type: 'string', required: true },
        start: { type: 'string', required: true },
        end: { type: 'string', required: true },
        description: { type: 'string' },
        location: { type: 'string' }
      }
    },
    get_events: {
      description: 'Get calendar events',
      parameters: {
        start_date: { type: 'string' },
        end_date: { type: 'string' }
      }
    }
  },

  // Screenshot tools
  screenshot: {
    capture: {
      description: 'Capture a screenshot',
      parameters: {
        area: { type: 'string', enum: ['full', 'window', 'selection'] }
      }
    },
    analyze: {
      description: 'Analyze a screenshot with AI',
      parameters: {
        image_path: { type: 'string', required: true },
        prompt: { type: 'string' }
      }
    }
  }
};

// Tool execution handlers
export const toolHandlers = {
  system: {
    async execute_command(params) {
      const { exec } = await import('child_process');
      const { promisify } = await import('util');
      const execAsync = promisify(exec);

      try {
        const { stdout, stderr } = await execAsync(params.command);
        return { success: true, output: stdout, error: stderr };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },

    async get_system_info() {
      const os = await import('os');
      return {
        platform: os.platform(),
        arch: os.arch(),
        cpus: os.cpus().length,
        memory: {
          total: os.totalmem(),
          free: os.freemem()
        },
        uptime: os.uptime(),
        hostname: os.hostname()
      };
    }
  },

  filesystem: {
    async read_file(params) {
      const fs = await import('fs/promises');
      try {
        const content = await fs.readFile(params.path, 'utf-8');
        return { success: true, content };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },

    async write_file(params) {
      const fs = await import('fs/promises');
      try {
        await fs.writeFile(params.path, params.content, 'utf-8');
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },

    async list_directory(params) {
      const fs = await import('fs/promises');
      const path = await import('path');

      try {
        const files = await fs.readdir(params.path, { withFileTypes: true });
        const items = files.map(file => ({
          name: file.name,
          type: file.isDirectory() ? 'directory' : 'file',
          path: path.join(params.path, file.name)
        }));
        return { success: true, items };
      } catch (error) {
        return { success: false, error: error.message };
      }
    }
  }
};

// Export a function to get all tools for registration
export function getAllTools() {
  const tools = [];

  for (const [category, categoryTools] of Object.entries(toolDefinitions)) {
    for (const [name, definition] of Object.entries(categoryTools)) {
      tools.push({
        name: `${category}_${name}`,
        description: definition.description,
        inputSchema: {
          type: 'object',
          properties: definition.parameters,
          required: Object.keys(definition.parameters).filter(
            key => definition.parameters[key].required
          )
        }
      });
    }
  }

  return tools;
}

// Export a function to execute a tool
export async function executeTool(toolName, params) {
  const [category, ...nameParts] = toolName.split('_');
  const name = nameParts.join('_');

  if (toolHandlers[category]?.[name]) {
    return await toolHandlers[category][name](params);
  }

  throw new Error(`Tool handler not found: ${toolName}`);
}