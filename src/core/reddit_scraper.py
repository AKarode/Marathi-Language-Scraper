import praw
import time
import logging
from typing import List, Dict, Generator, Optional
from datetime import datetime
from ..utils.config import Config

class RedditScraper:
    """
    High-performance Reddit scraper optimized for large-scale data collection
    """
    
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT
        )
        
        # Verify connection
        try:
            self.reddit.user.me()
            logging.info("Reddit API connection established successfully")
        except Exception as e:
            logging.error(f"Reddit API connection failed: {e}")
            raise
    
    def scrape_subreddit_posts(self, subreddit_name: str, limit: int = 1000, 
                             time_filter: str = 'month') -> Generator[Dict, None, None]:
        """
        Scrape posts from a subreddit with efficient pagination
        
        Args:
            subreddit_name: Name of the subreddit
            limit: Maximum number of posts to scrape
            time_filter: Time filter for posts (hour, day, week, month, year, all)
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts from multiple sources for comprehensive coverage
            post_sources = [
                subreddit.hot(limit=limit//3),
                subreddit.new(limit=limit//3),
                subreddit.top(time_filter=time_filter, limit=limit//3)
            ]
            
            seen_posts = set()
            
            for posts in post_sources:
                for post in posts:
                    # Skip if already processed
                    if post.id in seen_posts:
                        continue
                    
                    seen_posts.add(post.id)
                    
                    # Skip if no text content
                    if not post.title and not post.selftext:
                        continue
                    
                    yield {
                        'reddit_id': post.id,
                        'content_type': 'post',
                        'subreddit': subreddit_name,
                        'title': post.title,
                        'body': post.selftext,
                        'reddit_created_utc': datetime.fromtimestamp(post.created_utc),
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'url': post.url if hasattr(post, 'url') else None
                    }
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
        except Exception as e:
            logging.error(f"Error scraping subreddit {subreddit_name}: {e}")
            raise
    
    def scrape_post_comments(self, post_id: str, max_comments: int = 500) -> Generator[Dict, None, None]:
        """
        Scrape comments from a specific post
        
        Args:
            post_id: Reddit post ID
            max_comments: Maximum number of comments to scrape
        """
        try:
            submission = self.reddit.submission(id=post_id)
            
            # Replace MoreComments objects to get all comments
            submission.comments.replace_more(limit=0)
            
            comment_count = 0
            for comment in submission.comments.list():
                if comment_count >= max_comments:
                    break
                
                # Skip deleted/removed comments
                if comment.body in ['[deleted]', '[removed]', '']:
                    continue
                
                yield {
                    'reddit_id': comment.id,
                    'content_type': 'comment',
                    'subreddit': submission.subreddit.display_name,
                    'title': None,
                    'body': comment.body,
                    'reddit_created_utc': datetime.fromtimestamp(comment.created_utc),
                    'parent_id': post_id,
                    'score': comment.score
                }
                
                comment_count += 1
                
                # Rate limiting
                time.sleep(0.05)
                
        except Exception as e:
            logging.error(f"Error scraping comments for post {post_id}: {e}")
            raise
    
    def scrape_subreddit_comprehensive(self, subreddit_name: str, 
                                     max_posts: int = 1000,
                                     include_comments: bool = True,
                                     max_comments_per_post: int = 100) -> Generator[Dict, None, None]:
        """
        Comprehensive scraping of subreddit including posts and comments
        
        Args:
            subreddit_name: Name of the subreddit
            max_posts: Maximum number of posts to scrape
            include_comments: Whether to scrape comments
            max_comments_per_post: Maximum comments per post
        """
        logging.info(f"Starting comprehensive scrape of r/{subreddit_name}")
        
        post_count = 0
        comment_count = 0
        
        try:
            # Scrape posts
            for post_data in self.scrape_subreddit_posts(subreddit_name, max_posts):
                yield post_data
                post_count += 1
                
                # Scrape comments for this post if enabled
                if include_comments and post_data.get('num_comments', 0) > 0:
                    try:
                        for comment_data in self.scrape_post_comments(
                            post_data['reddit_id'], 
                            max_comments_per_post
                        ):
                            yield comment_data
                            comment_count += 1
                    except Exception as e:
                        logging.warning(f"Failed to scrape comments for post {post_data['reddit_id']}: {e}")
                        continue
                
                # Progress logging
                if post_count % 50 == 0:
                    logging.info(f"Scraped {post_count} posts and {comment_count} comments from r/{subreddit_name}")
                
        except Exception as e:
            logging.error(f"Error in comprehensive scraping of r/{subreddit_name}: {e}")
            raise
        
        logging.info(f"Completed scraping r/{subreddit_name}: {post_count} posts, {comment_count} comments")
    
    def scrape_multiple_subreddits(self, subreddit_names: List[str], 
                                  max_posts_per_subreddit: int = 1000,
                                  include_comments: bool = True) -> Generator[Dict, None, None]:
        """
        Scrape multiple subreddits efficiently
        
        Args:
            subreddit_names: List of subreddit names
            max_posts_per_subreddit: Maximum posts per subreddit
            include_comments: Whether to include comments
        """
        for subreddit_name in subreddit_names:
            logging.info(f"Starting scrape of r/{subreddit_name}")
            
            try:
                yield from self.scrape_subreddit_comprehensive(
                    subreddit_name=subreddit_name,
                    max_posts=max_posts_per_subreddit,
                    include_comments=include_comments
                )
                
                # Brief pause between subreddits to be respectful
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Failed to scrape r/{subreddit_name}: {e}")
                continue
    
    def get_subreddit_info(self, subreddit_name: str) -> Dict:
        """Get basic information about a subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            return {
                'name': subreddit.display_name,
                'subscribers': subreddit.subscribers,
                'description': subreddit.public_description,
                'created_utc': datetime.fromtimestamp(subreddit.created_utc),
                'is_active': subreddit.subscribers > 1000  # Basic activity check
            }
        except Exception as e:
            logging.error(f"Error getting info for r/{subreddit_name}: {e}")
            return None
    
    def validate_subreddits(self, subreddit_names: List[str]) -> List[str]:
        """Validate that subreddits exist and are accessible"""
        valid_subreddits = []
        
        for name in subreddit_names:
            info = self.get_subreddit_info(name)
            if info and info['is_active']:
                valid_subreddits.append(name)
                logging.info(f"✓ r/{name} - {info['subscribers']} subscribers")
            else:
                logging.warning(f"✗ r/{name} - Invalid or inactive")
        
        return valid_subreddits