import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { OpenAIEmbeddings } from 'langchain/embeddings/openai';

export const runtime = 'edge';
export const maxDuration = 60; // Set max duration to 60 seconds for vector operations

// POST /api/vector-search - Search for similar documents
export async function POST(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get request body
    const body = await request.json();
    
    // Validate required fields
    if (!body.query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }
    
    // Set defaults
    const collection = body.collection || 'knowledge_items';
    const limit = body.limit || 5;
    const threshold = body.threshold || 0.75;
    
    // Generate embedding for query
    const embeddings = new OpenAIEmbeddings({
      openAIApiKey: process.env.OPENAI_API_KEY,
      modelName: process.env.OPENAI_EMBEDDING_MODEL || 'text-embedding-ada-002',
    });
    
    const queryEmbedding = await embeddings.embedQuery(body.query);
    
    // Perform vector search using Supabase's pgvector
    let { data: results, error } = await supabase.rpc(
      'match_knowledge_items',
      {
        query_embedding: queryEmbedding,
        match_threshold: threshold,
        match_count: limit
      }
    );
    
    // If there's an error about the vector type or function not existing
    if (error && error.message.includes('does not exist')) {
      console.error('Vector extension error:', error);
      return NextResponse.json({
        error: 'Vector search is not available. Please ensure the pgvector extension is enabled in your Supabase project.',
        details: 'Go to Database → Extensions in your Supabase dashboard and enable the "vector" extension.'
      }, { status: 500 });
    }
    
    if (error) {
      console.error('Error performing vector search:', error);
      return NextResponse.json({ error: 'Failed to perform vector search' }, { status: 500 });
    }
    
    // Format results
    const formattedResults = results.map(item => ({
      content: item.content,
      metadata: item.meta_data,
      domain: item.domain,
      score: item.similarity
    }));
    
    return NextResponse.json({
      results: formattedResults,
      metrics: {
        query_time_ms: 0, // Not tracked in Edge function
        result_count: formattedResults.length
      }
    });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// POST /api/vector-search/add - Add documents to vector store
export async function PUT(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get request body
    const body = await request.json();
    
    // Validate required fields
    if (!body.documents || !Array.isArray(body.documents) || body.documents.length === 0) {
      return NextResponse.json({ error: 'Documents array is required' }, { status: 400 });
    }
    
    // Set defaults
    const collection = body.collection || 'knowledge_items';
    
    // Generate embeddings for documents
    const embeddings = new OpenAIEmbeddings({
      openAIApiKey: process.env.OPENAI_API_KEY,
      modelName: process.env.OPENAI_EMBEDDING_MODEL || 'text-embedding-ada-002',
    });
    
    // Process documents in batches
    const batchSize = 10;
    const results = [];
    
    for (let i = 0; i < body.documents.length; i += batchSize) {
      const batch = body.documents.slice(i, i + batchSize);
      
      // Generate embeddings for batch
      const texts = batch.map(doc => doc.content);
      const embeddingVectors = await embeddings.embedDocuments(texts);
      
      // Insert documents with embeddings
      const { data, error } = await supabase
        .from(collection)
        .insert(
          batch.map((doc, index) => ({
            content: doc.content,
            meta_data: doc.metadata || {},
            domain: doc.domain || 'general',
            embedding: embeddingVectors[index]
          }))
        )
        .select('id');
      
      if (error) {
        // If there's an error about the vector type not existing
        if (error.message.includes('does not exist')) {
          console.error('Vector extension error:', error);
          return NextResponse.json({
            error: 'Vector storage is not available. Please ensure the pgvector extension is enabled in your Supabase project.',
            details: 'Go to Database → Extensions in your Supabase dashboard and enable the "vector" extension.'
          }, { status: 500 });
        }
        
        console.error(`Error inserting batch ${i / batchSize + 1}:`, error);
        return NextResponse.json({ error: 'Failed to insert documents' }, { status: 500 });
      }
      
      results.push(...(data || []));
    }
    
    return NextResponse.json({
      success: true,
      count: results.length,
      ids: results.map(item => item.id)
    });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}