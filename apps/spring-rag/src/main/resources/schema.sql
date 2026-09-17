-- ============================================================================
-- OpsPilot: UrbanThread Enterprise RAG & Vector Storage Schema
-- Target: PostgreSQL 15+ with pgvector extension enabled
-- ============================================================================

-- 1. Initialize Vector and UUID Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Document Master Table
-- Stores metadata for uploaded PDFs, DOCX, Markdown, Text, CSV, and Web Pages.
CREATE TABLE IF NOT EXISTS rag_documents (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL DEFAULT 'urbanthread',
    title VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'GENERAL_SOP',
    document_type VARCHAR(32) NOT NULL, -- PDF, DOCX, TXT, MARKDOWN, CSV, WEBSITE
    source_url TEXT,
    file_size_bytes BIGINT,
    checksum VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'INDEXED',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Document Chunk Table
-- Stores extracted segments with 1536-dimensional embeddings and TSVector for lexical search.
CREATE TABLE IF NOT EXISTS rag_document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(64) NOT NULL DEFAULT 'urbanthread',
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT NOT NULL,
    tsv_content tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
);

-- 4. High-Performance Retrieval Indexes
-- Foreign Key and Tenant Partitioning
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc_id ON rag_document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_org_id ON rag_document_chunks(organization_id);

-- Full-Text Lexical Search Index (GIN)
CREATE INDEX IF NOT EXISTS idx_rag_chunks_tsv ON rag_document_chunks USING GIN(tsv_content);

-- Dense Vector Cosine Similarity Index (HNSW for sub-millisecond approximate nearest neighbors)
CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding_hnsw 
    ON rag_document_chunks USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 64);
