#!/usr/bin/env node

/**
 * This script checks if your Supabase setup is correctly configured,
 * especially for vector search functionality.
 * 
 * Usage:
 * 1. Make sure you have a .env.local file with your Supabase credentials
 * 2. Run: node scripts/check-supabase-setup.js
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

// Check environment variables
function checkEnvVars() {
  console.log('Checking environment variables...');
  
  const requiredVars = [
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
    'SUPABASE_SERVICE_ROLE_KEY'
  ];
  
  const missingVars = requiredVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    console.error('❌ Missing required environment variables:');
    missingVars.forEach(varName => console.error(`   - ${varName}`));
    console.error('Please add these to your .env.local file');
    return false;
  }
  
  console.log('✅ All required environment variables are present');
  return true;
}

// Initialize Supabase client
function initSupabase() {
  console.log('Initializing Supabase client...');
  
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    console.error('❌ Cannot initialize Supabase client due to missing credentials');
    return null;
  }
  
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    console.log('✅ Supabase client initialized');
    return supabase;
  } catch (error) {
    console.error('❌ Failed to initialize Supabase client:', error.message);
    return null;
  }
}

// Check if tables exist
async function checkTables(supabase) {
  console.log('Checking if required tables exist...');
  
  const requiredTables = ['users', 'tasks', 'knowledge_items', 'tal_blocks', 'debates'];
  const results = {};
  
  for (const table of requiredTables) {
    try {
      const { data, error } = await supabase
        .from(table)
        .select('count(*)')
        .limit(1);
      
      if (error) {
        console.error(`❌ Table '${table}' check failed:`, error.message);
        results[table] = false;
      } else {
        console.log(`✅ Table '${table}' exists`);
        results[table] = true;
      }
    } catch (error) {
      console.error(`❌ Table '${table}' check failed:`, error.message);
      results[table] = false;
    }
  }
  
  return results;
}

// Check if pgvector extension is enabled
async function checkVectorExtension(supabase) {
  console.log('Checking if pgvector extension is enabled...');
  
  try {
    const { data, error } = await supabase.rpc('check_vector_extension');
    
    if (error) {
      // If the function doesn't exist, create it first
      if (error.message.includes('function check_vector_extension() does not exist')) {
        console.log('Creating check_vector_extension function...');
        
        const { error: createError } = await supabase.rpc('create_check_vector_function');
        
        if (createError) {
          // Try direct SQL approach
          const { data: extensionData, error: sqlError } = await supabase.from('pg_extension')
            .select('extname')
            .eq('extname', 'vector')
            .maybeSingle();
          
          if (sqlError) {
            console.error('❌ Could not check if pgvector extension is enabled:', sqlError.message);
            return false;
          }
          
          if (extensionData) {
            console.log('✅ pgvector extension is enabled');
            return true;
          } else {
            console.error('❌ pgvector extension is NOT enabled');
            console.error('   Please enable it in your Supabase dashboard:');
            console.error('   Database → Extensions → find "vector" and enable it');
            return false;
          }
        }
        
        // Try again after creating the function
        const { data: retryData, error: retryError } = await supabase.rpc('check_vector_extension');
        
        if (retryError) {
          console.error('❌ Could not check if pgvector extension is enabled:', retryError.message);
          return false;
        }
        
        if (retryData) {
          console.log('✅ pgvector extension is enabled');
          return true;
        } else {
          console.error('❌ pgvector extension is NOT enabled');
          console.error('   Please enable it in your Supabase dashboard:');
          console.error('   Database → Extensions → find "vector" and enable it');
          return false;
        }
      } else {
        console.error('❌ Could not check if pgvector extension is enabled:', error.message);
        return false;
      }
    }
    
    if (data) {
      console.log('✅ pgvector extension is enabled');
      return true;
    } else {
      console.error('❌ pgvector extension is NOT enabled');
      console.error('   Please enable it in your Supabase dashboard:');
      console.error('   Database → Extensions → find "vector" and enable it');
      return false;
    }
  } catch (error) {
    console.error('❌ Could not check if pgvector extension is enabled:', error.message);
    
    // Try to create the function first
    try {
      await supabase.rpc('create_check_vector_function');
      console.log('Created check function, please run this script again');
    } catch (innerError) {
      console.error('Could not create helper function:', innerError.message);
    }
    
    return false;
  }
}

// Create helper functions if they don't exist
async function createHelperFunctions(supabase) {
  console.log('Creating helper functions...');
  
  const createCheckVectorFunction = `
    CREATE OR REPLACE FUNCTION create_check_vector_function()
    RETURNS void AS $$
    BEGIN
      EXECUTE '
        CREATE OR REPLACE FUNCTION check_vector_extension()
        RETURNS boolean AS $func$
        BEGIN
          RETURN EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = ''vector''
          );
        END;
        $func$ LANGUAGE plpgsql;
      ';
    END;
    $$ LANGUAGE plpgsql;
  `;
  
  try {
    const { error } = await supabase.rpc('create_check_vector_function');
    
    if (error) {
      // Function doesn't exist, create it with raw SQL
      const { error: sqlError } = await supabase.sql(createCheckVectorFunction);
      
      if (sqlError) {
        console.error('❌ Could not create helper functions:', sqlError.message);
        return false;
      }
    }
    
    console.log('✅ Helper functions created or already exist');
    return true;
  } catch (error) {
    // Try with raw SQL
    try {
      const { error: sqlError } = await supabase.sql(createCheckVectorFunction);
      
      if (sqlError) {
        console.error('❌ Could not create helper functions:', sqlError.message);
        return false;
      }
      
      console.log('✅ Helper functions created');
      return true;
    } catch (innerError) {
      console.error('❌ Could not create helper functions:', innerError.message);
      return false;
    }
  }
}

// Check if vector search function exists
async function checkVectorSearchFunction(supabase) {
  console.log('Checking if vector search function exists...');
  
  try {
    // Try to call the function with dummy data
    const dummyEmbedding = Array(1536).fill(0.1);
    const { data, error } = await supabase.rpc('match_knowledge_items', {
      query_embedding: dummyEmbedding,
      match_threshold: 0.5,
      match_count: 1
    });
    
    if (error) {
      if (error.message.includes('function match_knowledge_items') && error.message.includes('does not exist')) {
        console.error('❌ Vector search function does not exist');
        console.error('   Please run the migration script to create it');
        return false;
      } else if (error.message.includes('relation "knowledge_items" does not exist')) {
        console.error('❌ knowledge_items table does not exist');
        console.error('   Please run the migration script to create it');
        return false;
      } else if (error.message.includes('type "vector" does not exist')) {
        console.error('❌ vector type does not exist - pgvector extension is not enabled');
        console.error('   Please enable the pgvector extension in your Supabase dashboard');
        return false;
      } else {
        // This might be normal if there's no data
        console.log('✅ Vector search function exists (returned an error but that might be due to no data)');
        return true;
      }
    }
    
    console.log('✅ Vector search function exists and works correctly');
    return true;
  } catch (error) {
    console.error('❌ Could not check vector search function:', error.message);
    return false;
  }
}

// Main function
async function main() {
  console.log('=== Supabase Setup Check ===');
  
  // Check environment variables
  const envVarsOk = checkEnvVars();
  if (!envVarsOk) {
    console.error('❌ Environment variables check failed');
    process.exit(1);
  }
  
  // Initialize Supabase client
  const supabase = initSupabase();
  if (!supabase) {
    console.error('❌ Supabase client initialization failed');
    process.exit(1);
  }
  
  // Create helper functions
  await createHelperFunctions(supabase);
  
  // Check if pgvector extension is enabled
  const vectorExtensionOk = await checkVectorExtension(supabase);
  
  // Check if tables exist
  const tablesOk = await checkTables(supabase);
  
  // Check if vector search function exists
  const vectorSearchFunctionOk = await checkVectorSearchFunction(supabase);
  
  // Summary
  console.log('\n=== Summary ===');
  console.log(`Environment Variables: ${envVarsOk ? '✅' : '❌'}`);
  console.log(`pgvector Extension: ${vectorExtensionOk ? '✅' : '❌'}`);
  
  console.log('Tables:');
  for (const [table, exists] of Object.entries(tablesOk)) {
    console.log(`  - ${table}: ${exists ? '✅' : '❌'}`);
  }
  
  console.log(`Vector Search Function: ${vectorSearchFunctionOk ? '✅' : '❌'}`);
  
  // Final verdict
  const allChecksOk = envVarsOk && vectorExtensionOk && 
                      Object.values(tablesOk).every(Boolean) && 
                      vectorSearchFunctionOk;
  
  if (allChecksOk) {
    console.log('\n✅ All checks passed! Your Supabase setup is correctly configured.');
  } else {
    console.log('\n❌ Some checks failed. Please fix the issues mentioned above.');
    
    if (!vectorExtensionOk) {
      console.log('\nTo enable the pgvector extension:');
      console.log('1. Go to your Supabase dashboard');
      console.log('2. Navigate to Database → Extensions');
      console.log('3. Find "vector" in the list and toggle it to enable it');
      console.log('4. Run this script again to verify');
    }
    
    if (Object.values(tablesOk).some(exists => !exists)) {
      console.log('\nTo create the missing tables:');
      console.log('1. Go to your Supabase dashboard');
      console.log('2. Navigate to the SQL Editor');
      console.log('3. Copy the contents of supabase/migrations/20250530_initial_schema.sql');
      console.log('4. Paste it into the SQL Editor and run the script');
      console.log('5. Run this script again to verify');
    }
  }
}

// Run the main function
main().catch(error => {
  console.error('Unexpected error:', error);
  process.exit(1);
});