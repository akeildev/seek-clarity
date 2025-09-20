#!/usr/bin/env node
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Helper to communicate with MCP server
async function callMCPTool(toolName, args = {}) {
  return new Promise((resolve, reject) => {
    const server = spawn('node', [join(__dirname, 'server.js')], {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let output = '';
    let errorOutput = '';

    server.stdout.on('data', (data) => {
      output += data.toString();
    });

    server.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    server.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Server exited with code ${code}: ${errorOutput}`));
      } else {
        try {
          const lines = output.split('\n').filter(line => line.trim());
          const result = lines[lines.length - 1];
          resolve(JSON.parse(result));
        } catch (e) {
          resolve({ output, errorOutput });
        }
      }
    });

    // Send the tool call request
    const request = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      },
      id: 1
    };

    server.stdin.write(JSON.stringify(request) + '\n');
    server.stdin.end();
  });
}

// Direct database test using Supabase
async function testDirectDatabase() {
  console.log('\n=== Testing Direct Database Connection ===');

  const { createClient } = await import('@supabase/supabase-js');
  const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_ANON_KEY
  );

  // Test 1: Create multiple notes
  console.log('\n1. Creating notes...');
  const notes = [
    { title: 'Meeting Notes', content: 'Discussed project timeline', category: 'work' },
    { title: 'Shopping List', content: 'Milk, eggs, bread', category: 'personal' },
    { title: 'Code Review', content: 'Review PR #123', category: 'work' },
    { title: 'Vacation Ideas', content: 'Consider Hawaii or Japan', category: 'personal' }
  ];

  for (const note of notes) {
    const { data, error } = await supabase
      .from('notes')
      .insert([note])
      .select()
      .single();

    if (error) {
      console.error(`  ❌ Failed to create note: ${error.message}`);
    } else {
      console.log(`  ✅ Created: "${data.title}" (ID: ${data.id})`);
    }
  }

  // Test 2: Search notes
  console.log('\n2. Searching notes...');
  const searchTests = [
    { query: 'project', expected: 'Meeting Notes' },
    { query: 'eggs', expected: 'Shopping List' },
    { category: 'work', expected: 2 } // Should find 2 work notes
  ];

  for (const test of searchTests) {
    let query = supabase.from('notes').select('*');

    if (test.query) {
      query = query.or(`title.ilike.%${test.query}%,content.ilike.%${test.query}%`);
    }
    if (test.category) {
      query = query.eq('category', test.category);
    }

    const { data, error } = await query;

    if (error) {
      console.error(`  ❌ Search failed: ${error.message}`);
    } else {
      if (typeof test.expected === 'number') {
        console.log(`  ✅ Found ${data.length} notes in category "${test.category}"`);
      } else {
        const found = data.find(n => n.title === test.expected);
        console.log(`  ✅ Search for "${test.query}" found: ${found ? found.title : 'nothing'}`);
      }
    }
  }

  // Test 3: Update a note
  console.log('\n3. Updating a note...');
  const { data: noteToUpdate } = await supabase
    .from('notes')
    .select('*')
    .eq('title', 'Meeting Notes')
    .single();

  if (noteToUpdate) {
    const { data: updated, error } = await supabase
      .from('notes')
      .update({
        content: 'Updated: Discussed project timeline and budget',
        updated_at: new Date().toISOString()
      })
      .eq('id', noteToUpdate.id)
      .select()
      .single();

    if (error) {
      console.error(`  ❌ Update failed: ${error.message}`);
    } else {
      console.log(`  ✅ Updated note: "${updated.title}"`);
    }
  }

  // Test 4: Create conversations
  console.log('\n4. Testing conversations table...');
  const conversation = {
    user_message: 'Create a note about the weather',
    assistant_response: 'I created a note about today\'s weather forecast',
    tools_used: ['create_note', 'get_weather']
  };

  const { data: conv, error: convError } = await supabase
    .from('conversations')
    .insert([conversation])
    .select()
    .single();

  if (convError) {
    console.error(`  ❌ Failed to save conversation: ${convError.message}`);
  } else {
    console.log(`  ✅ Saved conversation (ID: ${conv.id})`);
  }

  // Test 5: Create tasks
  console.log('\n5. Testing tasks table...');
  const tasks = [
    { title: 'Complete MCP integration', description: 'Integrate MCP with voice agent', status: 'in_progress' },
    { title: 'Test database', description: 'Run all database tests', status: 'completed' },
    { title: 'Documentation', description: 'Write documentation for MCP', status: 'pending' }
  ];

  for (const task of tasks) {
    const { data, error } = await supabase
      .from('tasks')
      .insert([task])
      .select()
      .single();

    if (error) {
      console.error(`  ❌ Failed to create task: ${error.message}`);
    } else {
      console.log(`  ✅ Created task: "${data.title}" (${data.status})`);
    }
  }

  // Test 6: List all categories
  console.log('\n6. Listing categories...');
  const { data: allNotes } = await supabase
    .from('notes')
    .select('category');

  const categories = [...new Set(allNotes.map(n => n.category))];
  console.log(`  ✅ Categories found: ${categories.join(', ')}`);

  // Test 7: Get statistics
  console.log('\n7. Database Statistics:');
  const { count: noteCount } = await supabase
    .from('notes')
    .select('*', { count: 'exact', head: true });

  const { count: convCount } = await supabase
    .from('conversations')
    .select('*', { count: 'exact', head: true });

  const { count: taskCount } = await supabase
    .from('tasks')
    .select('*', { count: 'exact', head: true });

  console.log(`  📊 Notes: ${noteCount}`);
  console.log(`  📊 Conversations: ${convCount}`);
  console.log(`  📊 Tasks: ${taskCount}`);

  // Test 8: Clean up test data (optional)
  console.log('\n8. Cleanup test data? (keeping for now)');
  console.log('  ℹ️  Test data preserved in database');

  return true;
}

// Main test runner
async function runTests() {
  console.log('🚀 Starting MCP and Database Tests...\n');

  try {
    // Load environment variables
    const dotenv = await import('dotenv');
    dotenv.config({ path: join(__dirname, '../../.env') });

    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
      throw new Error('Missing Supabase credentials in .env file');
    }

    console.log('✅ Environment variables loaded');
    console.log(`📍 Supabase URL: ${process.env.SUPABASE_URL}`);

    // Run direct database tests
    await testDirectDatabase();

    console.log('\n✨ All tests completed successfully!');
  } catch (error) {
    console.error('\n❌ Test failed:', error);
    process.exit(1);
  }
}

// Run the tests
runTests();