-- ThinkBank Database Initialization Script
-- PostgreSQL 16 + pgvector Extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create assets table (core metadata storage)
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_name VARCHAR(64) NOT NULL,
    object_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(127) NOT NULL,
    size_bytes BIGINT NOT NULL,
    caption TEXT,                    -- AI description or Doc summary
    content_text TEXT,               -- Full OCR/Doc text
    metadata JSONB DEFAULT '{}',     -- EXIF, dimensions, etc.
    processing_status VARCHAR(32) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create asset_embeddings table (separated for performance)
CREATE TABLE IF NOT EXISTS asset_embeddings (
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    semantic_vector vector(1024),    -- BGE-M3 embedding
    visual_vector vector(1152),      -- SigLIP embedding
    PRIMARY KEY (asset_id)
);

-- Create vector similarity indexes using IVFFlat
CREATE INDEX IF NOT EXISTS idx_semantic_vector
ON asset_embeddings USING ivfflat (semantic_vector vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_visual_vector
ON asset_embeddings USING ivfflat (visual_vector vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_assets_mime_type ON assets(mime_type);
CREATE INDEX IF NOT EXISTS idx_assets_processing_status ON assets(processing_status);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assets_metadata ON assets USING GIN (metadata);

-- Create update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create chat_history table for conversation persistence
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    role VARCHAR(16) NOT NULL,       -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id, created_at);

-- Create processing_tasks table for async job tracking
CREATE TABLE IF NOT EXISTS processing_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    status VARCHAR(32) DEFAULT 'PENDING',
    stage VARCHAR(32) DEFAULT 'QUEUED',
    progress FLOAT DEFAULT 0.0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_processing_tasks_status ON processing_tasks(status);

-- Grant permissions (adjust username as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO thinkbank;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO thinkbank;
