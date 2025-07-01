import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Reddit API
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'MarathiScraper/1.0')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Scraping
    TARGET_SUBREDDITS = os.getenv('TARGET_SUBREDDITS', 'marathi,mumbai,india').split(',')
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))
    MAX_POSTS_PER_SUBREDDIT = int(os.getenv('MAX_POSTS_PER_SUBREDDIT', 1000))
    
    # Language Detection
    MARATHI_CONFIDENCE_THRESHOLD = 0.95
    MIXED_CONTENT_THRESHOLD = 0.7