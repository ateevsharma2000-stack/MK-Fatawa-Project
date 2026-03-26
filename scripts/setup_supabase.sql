-- Run this in Supabase SQL Editor to set up the fatawa search tables

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the main chunks table
CREATE TABLE IF NOT EXISTS fatawa_chunks (
  id TEXT PRIMARY KEY,
  collection TEXT NOT NULL,
  volume INT NOT NULL,
  part_no INT,
  page_no_start INT,
  page_no_end INT,
  section_title TEXT,
  content TEXT NOT NULL,
  token_count INT,
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast vector similarity search
CREATE INDEX IF NOT EXISTS fatawa_chunks_embedding_idx
  ON fatawa_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Create index for collection filtering
CREATE INDEX IF NOT EXISTS fatawa_chunks_collection_idx
  ON fatawa_chunks (collection);

-- RPC function for semantic search
CREATE OR REPLACE FUNCTION match_fatawa(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.3,
  match_count INT DEFAULT 10,
  filter_collection TEXT DEFAULT NULL
)
RETURNS TABLE (
  id TEXT,
  collection TEXT,
  volume INT,
  part_no INT,
  page_no_start INT,
  page_no_end INT,
  section_title TEXT,
  content TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    fc.id,
    fc.collection,
    fc.volume,
    fc.part_no,
    fc.page_no_start,
    fc.page_no_end,
    fc.section_title,
    fc.content,
    1 - (fc.embedding <=> query_embedding) AS similarity
  FROM fatawa_chunks fc
  WHERE (filter_collection IS NULL OR fc.collection = filter_collection)
    AND 1 - (fc.embedding <=> query_embedding) > match_threshold
  ORDER BY fc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
