#!/usr/bin/env python3
"""
Marathi Reddit Scraper - MVP
High-performance scraper for Marathi language content from Reddit
Optimized for millions of records with 95%+ accuracy language detection
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any
import signal
import sys

from src.utils.config import Config
from src.core.reddit_scraper import RedditScraper
from src.core.language_detector import HighAccuracyMarathiDetector
from src.database.supabase_client import SupabaseClient
from src.core.text_processor import LLMOptimizedTextProcessor

class MarathiRedditScraper:
    """Main scraper pipeline orchestrating all components"""
    
    def __init__(self):
        self.setup_logging()
        
        # Initialize components
        self.reddit_scraper = RedditScraper()
        self.language_detector = HighAccuracyMarathiDetector()
        self.supabase_client = SupabaseClient()
        self.text_processor = LLMOptimizedTextProcessor()
        
        # Processing stats
        self.stats = {
            'total_processed': 0,
            'pure_marathi': 0,
            'mixed_content': 0,
            'non_marathi': 0,
            'failed_inserts': 0,
            'start_time': datetime.now()
        }
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        
        logging.info("Marathi Reddit Scraper initialized successfully")
    
    def setup_logging(self):
        """Configure logging for production use"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def process_content(self, raw_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw Reddit content through language detection pipeline
        
        Args:
            raw_content: Raw content from Reddit scraper
            
        Returns:
            Processed content ready for database insertion
        """
        try:
            # Combine title and body for language detection
            text_content = f"{raw_content.get('title', '')} {raw_content.get('body', '')}".strip()
            
            if not text_content:
                return None
            
            # Detect language with high accuracy
            detection_result = self.language_detector.detect_language(
                text=raw_content.get('body', ''),
                title=raw_content.get('title', '')
            )
            
            # Only process if meets confidence threshold
            if detection_result['category'] == 'non_marathi':
                self.stats['non_marathi'] += 1
                return None
            
            # Separate mixed content if needed
            separated_text = {'marathi_text': '', 'english_text': ''}
            if detection_result['category'] == 'mixed_content':
                separated_text = self.language_detector.separate_languages(text_content)
            elif detection_result['category'] == 'pure_marathi':
                separated_text['marathi_text'] = text_content
            
            # Process text for LLM optimization
            llm_content = self.text_processor.create_llm_optimized_content(
                title=raw_content.get('title', ''),
                body=raw_content.get('body', ''),
                marathi_text=separated_text['marathi_text'],
                english_text=separated_text['english_text'],
                metadata={
                    'content_type': raw_content['content_type'],
                    'subreddit': raw_content['subreddit'],
                    'language_category': detection_result['category'],
                    'marathi_confidence': detection_result['marathi_confidence']
                }
            )
            
            # Prepare data for database
            processed_content = {
                'reddit_id': raw_content['reddit_id'],
                'content_type': raw_content['content_type'],
                'subreddit': raw_content['subreddit'],
                'title': raw_content.get('title'),
                'body': raw_content.get('body'),
                'language_category': detection_result['category'],
                'marathi_confidence': detection_result['marathi_confidence'],
                'marathi_text': separated_text['marathi_text'] or None,
                'english_text': separated_text['english_text'] or None,
                'reddit_created_utc': raw_content.get('reddit_created_utc'),
                'parent_id': raw_content.get('parent_id'),
                
                # LLM-optimized content formats
                'llm_clean_text': llm_content['clean'],
                'llm_compact_text': llm_content['compact'],
                'llm_context_text': llm_content['context'],
                'token_count_estimate': llm_content['token_estimates']['clean']
            }
            
            # Update stats
            if detection_result['category'] == 'pure_marathi':
                self.stats['pure_marathi'] += 1
            elif detection_result['category'] == 'mixed_content':
                self.stats['mixed_content'] += 1
            
            return processed_content
            
        except Exception as e:
            logging.error(f"Error processing content {raw_content.get('reddit_id', 'unknown')}: {e}")
            return None
    
    def scrape_and_process_batch(self, subreddit_names: List[str], 
                                batch_size: int = 100) -> None:
        """
        Scrape and process content in batches for optimal performance
        
        Args:
            subreddit_names: List of subreddit names to scrape
            batch_size: Size of processing batches
        """
        logging.info(f"Starting batch processing for subreddits: {subreddit_names}")
        
        batch = []
        
        try:
            # Scrape content from multiple subreddits
            for raw_content in self.reddit_scraper.scrape_multiple_subreddits(
                subreddit_names=subreddit_names,
                max_posts_per_subreddit=Config.MAX_POSTS_PER_SUBREDDIT,
                include_comments=True
            ):
                # Skip if already exists
                if self.supabase_client.content_exists(raw_content['reddit_id']):
                    continue
                
                # Process content
                processed_content = self.process_content(raw_content)
                
                if processed_content:
                    batch.append(processed_content)
                    self.stats['total_processed'] += 1
                
                # Process batch when full
                if len(batch) >= batch_size:
                    self.store_batch(batch)
                    batch = []
                    
                    # Progress update
                    if self.stats['total_processed'] % 500 == 0:
                        self.log_progress()
            
            # Process remaining batch
            if batch:
                self.store_batch(batch)
                
        except Exception as e:
            logging.error(f"Error in batch processing: {e}")
            # Store partial batch before failing
            if batch:
                self.store_batch(batch)
            raise
    
    def store_batch(self, batch: List[Dict[str, Any]]) -> None:
        """Store processed batch in Supabase"""
        try:
            successful, failed = self.supabase_client.bulk_insert_content(
                batch, 
                batch_size=Config.BATCH_SIZE
            )
            
            self.stats['failed_inserts'] += failed
            
            if failed > 0:
                logging.warning(f"Batch storage: {successful} successful, {failed} failed")
            else:
                logging.info(f"Batch stored successfully: {successful} records")
                
        except Exception as e:
            logging.error(f"Error storing batch: {e}")
            self.stats['failed_inserts'] += len(batch)
    
    def log_progress(self) -> None:
        """Log current processing progress"""
        elapsed = datetime.now() - self.stats['start_time']
        rate = self.stats['total_processed'] / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        
        logging.info(f"""
Progress Update:
- Total Processed: {self.stats['total_processed']}
- Pure Marathi: {self.stats['pure_marathi']}
- Mixed Content: {self.stats['mixed_content']}
- Non-Marathi: {self.stats['non_marathi']}
- Failed Inserts: {self.stats['failed_inserts']}
- Processing Rate: {rate:.2f} items/second
- Elapsed Time: {elapsed}
        """.strip())
    
    def run_full_scrape(self) -> None:
        """Run complete scraping process"""
        logging.info("Starting full Marathi Reddit scrape")
        
        try:
            # Validate target subreddits
            valid_subreddits = self.reddit_scraper.validate_subreddits(Config.TARGET_SUBREDDITS)
            
            if not valid_subreddits:
                logging.error("No valid subreddits found")
                return
            
            logging.info(f"Validated subreddits: {valid_subreddits}")
            
            # Run scraping and processing
            self.scrape_and_process_batch(valid_subreddits)
            
            # Final progress report
            self.log_progress()
            
            # Get database stats
            db_stats = self.supabase_client.get_processing_stats()
            logging.info(f"Database stats: {db_stats}")
            
            logging.info("Scraping completed successfully")
            
        except Exception as e:
            logging.error(f"Error in full scrape: {e}")
            raise
    
    def run_test_scrape(self, limit_per_subreddit: int = 50) -> None:
        """Run a limited test scrape for testing"""
        logging.info(f"Starting test scrape (limit: {limit_per_subreddit} per subreddit)")
        
        # Temporarily override config for testing
        original_limit = Config.MAX_POSTS_PER_SUBREDDIT
        Config.MAX_POSTS_PER_SUBREDDIT = limit_per_subreddit
        
        try:
            self.run_full_scrape()
        finally:
            # Restore original config
            Config.MAX_POSTS_PER_SUBREDDIT = original_limit
    
    def shutdown_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logging.info(f"Received shutdown signal {signum}")
        self.log_progress()
        logging.info("Shutting down gracefully...")
        sys.exit(0)

def main():
    """Main entry point"""
    print("Marathi Reddit Scraper MVP")
    print("=" * 40)
    
    try:
        scraper = MarathiRedditScraper()
        
        # Check if this is a test run
        if len(sys.argv) > 1 and sys.argv[1] == '--test':
            scraper.run_test_scrape(limit_per_subreddit=10)
        else:
            scraper.run_full_scrape()
            
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()