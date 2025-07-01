-- Supabase Schema for Marathi Reddit Scraper
-- Run this in your Supabase SQL editor

-- Create enum for content types
CREATE TYPE content_type AS ENUM ('post', 'comment');
CREATE TYPE language_category AS ENUM ('pure_marathi', 'mixed_content', 'non_marathi');

-- Main content table optimized for millions of records
CREATE TABLE reddit_content (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    reddit_id VARCHAR(50) UNIQUE NOT NULL,
    content_type content_type NOT NULL,
    subreddit VARCHAR(100) NOT NULL,
    title TEXT,
    body TEXT,
    language_category language_category NOT NULL,
    marathi_confidence DECIMAL(3,2),
    marathi_text TEXT,
    english_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reddit_created_utc TIMESTAMP WITH TIME ZONE,
    parent_id VARCHAR(50), -- For comments, references parent post/comment
    
    -- LLM-optimized content formats
    llm_clean_text TEXT,      -- Clean, normalized text for training
    llm_compact_text TEXT,    -- Token-efficient compact format
    llm_context_text TEXT,    -- Context-aware format for RAG
    token_count_estimate INTEGER DEFAULT 0,  -- Estimated token count
    
    -- Indexes for performance
    CONSTRAINT valid_confidence CHECK (marathi_confidence >= 0 AND marathi_confidence <= 1)
);

-- Indexes for fast queries on millions of records
CREATE INDEX idx_reddit_content_subreddit ON reddit_content(subreddit);
CREATE INDEX idx_reddit_content_language_category ON reddit_content(language_category);
CREATE INDEX idx_reddit_content_created_at ON reddit_content(created_at);
CREATE INDEX idx_reddit_content_type ON reddit_content(content_type);
CREATE INDEX idx_reddit_content_confidence ON reddit_content(marathi_confidence);
CREATE INDEX idx_reddit_content_reddit_id ON reddit_content(reddit_id);

-- Composite index for common queries
CREATE INDEX idx_reddit_content_subreddit_language ON reddit_content(subreddit, language_category);

-- Enable Row Level Security (optional)
ALTER TABLE reddit_content ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users (adjust as needed)
CREATE POLICY "Enable read access for authenticated users" ON reddit_content
    FOR SELECT USING (auth.role() = 'authenticated');

-- Statistics table for monitoring
CREATE TABLE scraping_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    subreddit VARCHAR(100) NOT NULL,
    total_posts INTEGER DEFAULT 0,
    total_comments INTEGER DEFAULT 0,
    pure_marathi_count INTEGER DEFAULT 0,
    mixed_content_count INTEGER DEFAULT 0,
    last_scraped TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(subreddit)
);

-- Function to update stats (called by trigger)
CREATE OR REPLACE FUNCTION update_scraping_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO scraping_stats (subreddit, total_posts, total_comments, pure_marathi_count, mixed_content_count)
    VALUES (
        NEW.subreddit,
        CASE WHEN NEW.content_type = 'post' THEN 1 ELSE 0 END,
        CASE WHEN NEW.content_type = 'comment' THEN 1 ELSE 0 END,
        CASE WHEN NEW.language_category = 'pure_marathi' THEN 1 ELSE 0 END,
        CASE WHEN NEW.language_category = 'mixed_content' THEN 1 ELSE 0 END
    )
    ON CONFLICT (subreddit) DO UPDATE SET
        total_posts = scraping_stats.total_posts + (CASE WHEN NEW.content_type = 'post' THEN 1 ELSE 0 END),
        total_comments = scraping_stats.total_comments + (CASE WHEN NEW.content_type = 'comment' THEN 1 ELSE 0 END),
        pure_marathi_count = scraping_stats.pure_marathi_count + (CASE WHEN NEW.language_category = 'pure_marathi' THEN 1 ELSE 0 END),
        mixed_content_count = scraping_stats.mixed_content_count + (CASE WHEN NEW.language_category = 'mixed_content' THEN 1 ELSE 0 END),
        last_scraped = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update stats
CREATE TRIGGER update_stats_trigger
    AFTER INSERT ON reddit_content
    FOR EACH ROW
    EXECUTE FUNCTION update_scraping_stats();