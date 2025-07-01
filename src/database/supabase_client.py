import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from supabase import create_client, Client
from ..utils.config import Config

class SupabaseClient:
    """
    High-performance Supabase client optimized for millions of records
    """
    
    def __init__(self):
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError("Supabase URL and KEY must be configured")
            
        try:
            self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        except Exception as e:
            # Fallback for older supabase versions
            logging.warning(f"Standard supabase init failed, trying alternative: {e}")
            from supabase.client import ClientOptions
            self.supabase: Client = create_client(
                Config.SUPABASE_URL, 
                Config.SUPABASE_KEY,
                options=ClientOptions()
            )
        
        # Test connection
        try:
            # Try a simple query to test connection
            self.supabase.table('reddit_content').select('id').limit(1).execute()
            logging.info("Supabase connection established successfully")
        except Exception as e:
            logging.error(f"Supabase connection failed: {e}")
            raise
    
    def insert_content(self, content_data: Dict[str, Any]) -> bool:
        """
        Insert a single content record
        
        Args:
            content_data: Dictionary containing content data
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure required fields
            required_fields = ['reddit_id', 'content_type', 'subreddit', 'language_category']
            for field in required_fields:
                if field not in content_data:
                    logging.error(f"Missing required field: {field}")
                    return False
            
            # Insert data
            result = self.supabase.table('reddit_content').insert(content_data).execute()
            
            if result.data:
                logging.debug(f"Successfully inserted content: {content_data['reddit_id']}")
                return True
            else:
                logging.error(f"Failed to insert content: {content_data['reddit_id']}")
                return False
                
        except Exception as e:
            logging.error(f"Error inserting content {content_data.get('reddit_id', 'unknown')}: {e}")
            return False
    
    def bulk_insert_content(self, content_list: List[Dict[str, Any]], 
                           batch_size: int = 100) -> Tuple[int, int]:
        """
        Bulk insert content records for better performance
        
        Args:
            content_list: List of content dictionaries
            batch_size: Number of records per batch
            
        Returns:
            Tuple[int, int]: (successful_inserts, failed_inserts)
        """
        successful = 0
        failed = 0
        
        # Process in batches
        for i in range(0, len(content_list), batch_size):
            batch = content_list[i:i + batch_size]
            
            try:
                # Validate batch data
                valid_batch = []
                for item in batch:
                    if self._validate_content_data(item):
                        valid_batch.append(item)
                    else:
                        failed += 1
                
                if not valid_batch:
                    continue
                
                # Insert batch
                result = self.supabase.table('reddit_content').insert(valid_batch).execute()
                
                if result.data:
                    batch_success = len(result.data)
                    successful += batch_success
                    logging.info(f"Batch insert successful: {batch_success} records")
                else:
                    failed += len(valid_batch)
                    logging.error(f"Batch insert failed for {len(valid_batch)} records")
                    
            except Exception as e:
                failed += len(batch)
                logging.error(f"Error in batch insert: {e}")
                
                # Try individual inserts as fallback
                for item in batch:
                    if self.insert_content(item):
                        successful += 1
                        failed -= 1
        
        return successful, failed
    
    def _validate_content_data(self, data: Dict[str, Any]) -> bool:
        """Validate content data before insertion"""
        required_fields = ['reddit_id', 'content_type', 'subreddit', 'language_category']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                logging.warning(f"Invalid data - missing {field}: {data}")
                return False
        
        # Validate content_type
        if data['content_type'] not in ['post', 'comment']:
            logging.warning(f"Invalid content_type: {data['content_type']}")
            return False
        
        # Validate language_category
        if data['language_category'] not in ['pure_marathi', 'mixed_content', 'non_marathi']:
            logging.warning(f"Invalid language_category: {data['language_category']}")
            return False
        
        # Validate confidence score if present
        if 'marathi_confidence' in data:
            confidence = data['marathi_confidence']
            if not (0 <= confidence <= 1):
                logging.warning(f"Invalid confidence score: {confidence}")
                return False
        
        return True
    
    def content_exists(self, reddit_id: str) -> bool:
        """Check if content already exists in database"""
        try:
            result = self.supabase.table('reddit_content').select('reddit_id').eq('reddit_id', reddit_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logging.error(f"Error checking if content exists: {e}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            result = self.supabase.table('scraping_stats').select('*').execute()
            
            stats = {
                'total_records': 0,
                'pure_marathi': 0,
                'mixed_content': 0,
                'subreddit_breakdown': {}
            }
            
            for row in result.data:
                stats['total_records'] += row['total_posts'] + row['total_comments']
                stats['pure_marathi'] += row['pure_marathi_count']
                stats['mixed_content'] += row['mixed_content_count']
                stats['subreddit_breakdown'][row['subreddit']] = {
                    'posts': row['total_posts'],
                    'comments': row['total_comments'],
                    'marathi': row['pure_marathi_count'],
                    'mixed': row['mixed_content_count'],
                    'last_scraped': row['last_scraped']
                }
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting processing stats: {e}")
            return {}
    
    def get_marathi_content(self, subreddit: Optional[str] = None, 
                           limit: int = 100,
                           category: str = 'pure_marathi') -> List[Dict[str, Any]]:
        """
        Retrieve Marathi content from database
        
        Args:
            subreddit: Filter by specific subreddit
            limit: Maximum number of records
            category: Language category filter
            
        Returns:
            List of content records
        """
        try:
            query = self.supabase.table('reddit_content').select('*').eq('language_category', category)
            
            if subreddit:
                query = query.eq('subreddit', subreddit)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data
            
        except Exception as e:
            logging.error(f"Error retrieving Marathi content: {e}")
            return []
    
    def search_content(self, search_text: str, 
                      language_category: Optional[str] = None,
                      subreddit: Optional[str] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search content by text (requires full-text search setup in Supabase)
        
        Args:
            search_text: Text to search for
            language_category: Filter by language category
            subreddit: Filter by subreddit
            limit: Maximum results
            
        Returns:
            List of matching records
        """
        try:
            query = self.supabase.table('reddit_content').select('*')
            
            # Text search (basic implementation - can be enhanced with full-text search)
            query = query.or_(f'title.ilike.%{search_text}%,body.ilike.%{search_text}%')
            
            if language_category:
                query = query.eq('language_category', language_category)
            
            if subreddit:
                query = query.eq('subreddit', subreddit)
            
            result = query.limit(limit).execute()
            return result.data
            
        except Exception as e:
            logging.error(f"Error searching content: {e}")
            return []
    
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """
        Clean up old data to manage database size
        
        Args:
            days_old: Delete records older than this many days
            
        Returns:
            Number of deleted records
        """
        try:
            cutoff_date = datetime.now().isoformat()
            
            # Note: This is a basic implementation
            # For production, you'd want more sophisticated cleanup logic
            result = self.supabase.table('reddit_content').delete().lt('created_at', cutoff_date).execute()
            
            deleted_count = len(result.data) if result.data else 0
            logging.info(f"Cleaned up {deleted_count} old records")
            return deleted_count
            
        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")
            return 0
    
    def update_content_language(self, reddit_id: str, 
                               language_data: Dict[str, Any]) -> bool:
        """
        Update language detection results for existing content
        
        Args:
            reddit_id: Reddit ID of the content
            language_data: Updated language detection data
            
        Returns:
            Success status
        """
        try:
            result = self.supabase.table('reddit_content').update(language_data).eq('reddit_id', reddit_id).execute()
            
            if result.data:
                logging.debug(f"Updated language data for {reddit_id}")
                return True
            else:
                logging.error(f"Failed to update language data for {reddit_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error updating language data for {reddit_id}: {e}")
            return False