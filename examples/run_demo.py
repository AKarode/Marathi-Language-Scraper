#!/usr/bin/env python3
"""
Demo script for Marathi Reddit Scraper MVP
This runs a full demonstration with local JSON storage while Supabase is being set up
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from reddit_scraper import RedditScraper
from language_detector import HighAccuracyMarathiDetector

class LocalStorageDemo:
    """Demo version with local JSON storage"""
    
    def __init__(self):
        self.reddit_scraper = RedditScraper()
        self.language_detector = HighAccuracyMarathiDetector()
        self.data_file = f"marathi_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.stats = {
            'total_processed': 0,
            'pure_marathi': 0,
            'mixed_content': 0,
            'non_marathi': 0,
            'start_time': datetime.now().isoformat()
        }
        self.content_data = []
    
    def process_content(self, raw_content: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw content through language detection"""
        try:
            # Detect language
            detection_result = self.language_detector.detect_language(
                text=raw_content.get('body', ''),
                title=raw_content.get('title', '')
            )
            
            # Skip non-Marathi content
            if detection_result['category'] == 'non_marathi':
                self.stats['non_marathi'] += 1
                return None
            
            # Separate mixed content
            separated_text = {'marathi_text': '', 'english_text': ''}
            text_content = f"{raw_content.get('title', '')} {raw_content.get('body', '')}".strip()
            
            if detection_result['category'] == 'mixed_content':
                separated_text = self.language_detector.separate_languages(text_content)
            elif detection_result['category'] == 'pure_marathi':
                separated_text['marathi_text'] = text_content
            
            # Create processed record
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
                'reddit_created_utc': raw_content.get('reddit_created_utc').isoformat() if raw_content.get('reddit_created_utc') else None,
                'processed_at': datetime.now().isoformat()
            }
            
            # Update stats
            if detection_result['category'] == 'pure_marathi':
                self.stats['pure_marathi'] += 1
            elif detection_result['category'] == 'mixed_content':
                self.stats['mixed_content'] += 1
            
            return processed_content
            
        except Exception as e:
            print(f"❌ Error processing content {raw_content.get('reddit_id', 'unknown')}: {e}")
            return None
    
    def run_demo_scrape(self, subreddits: List[str], max_posts_per_subreddit: int = 20):
        """Run demonstration scrape"""
        print("🎯 Marathi Reddit Scraper - Full Demo")
        print("=" * 60)
        
        for subreddit_name in subreddits:
            print(f"\n🔍 Processing r/{subreddit_name}...")
            
            try:
                # Scrape posts and comments
                for raw_content in self.reddit_scraper.scrape_subreddit_comprehensive(
                    subreddit_name=subreddit_name,
                    max_posts=max_posts_per_subreddit,
                    include_comments=True,
                    max_comments_per_post=10
                ):
                    self.stats['total_processed'] += 1
                    
                    # Process content
                    processed_content = self.process_content(raw_content)
                    
                    if processed_content:
                        self.content_data.append(processed_content)
                        
                        # Show progress
                        if len(self.content_data) % 5 == 0:
                            print(f"  📝 Found {len(self.content_data)} Marathi items so far...")
                    
                    # Progress update
                    if self.stats['total_processed'] % 25 == 0:
                        self.print_progress()
                
            except Exception as e:
                print(f"❌ Error processing r/{subreddit_name}: {e}")
                continue
        
        # Final results
        self.print_final_results()
        self.save_data()
    
    def print_progress(self):
        """Print current progress"""
        print(f"  📊 Progress: {self.stats['total_processed']} processed, {len(self.content_data)} Marathi items found")
    
    def print_final_results(self):
        """Print final results summary"""
        print(f"\n📊 Final Results")
        print("=" * 60)
        print(f"Total Items Processed: {self.stats['total_processed']}")
        print(f"Pure Marathi: {self.stats['pure_marathi']}")
        print(f"Mixed Content: {self.stats['mixed_content']}")
        print(f"Non-Marathi (filtered): {self.stats['non_marathi']}")
        print(f"Total Marathi Content: {len(self.content_data)}")
        
        if self.stats['total_processed'] > 0:
            success_rate = len(self.content_data) / self.stats['total_processed'] * 100
            print(f"Marathi Detection Rate: {success_rate:.1f}%")
        
        # Show sample content
        print(f"\n🔤 Sample Marathi Content:")
        print("-" * 60)
        
        for i, item in enumerate(self.content_data[:3], 1):
            print(f"\n{i}. r/{item['subreddit']} - {item['content_type']} ({item['language_category']})")
            print(f"   Confidence: {item['marathi_confidence']:.3f}")
            if item['title']:
                print(f"   Title: {item['title'][:80]}...")
            if item['marathi_text']:
                print(f"   Marathi: {item['marathi_text'][:100]}...")
            if item['english_text']:
                print(f"   English: {item['english_text'][:100]}...")
    
    def save_data(self):
        """Save data and stats to JSON files"""
        # Save content data
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': self.stats,
                'content': self.content_data
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Data saved to: {self.data_file}")
        print(f"📁 File size: {os.path.getsize(self.data_file) / 1024:.1f} KB")
        print(f"🎯 Ready for Supabase upload when connection is fixed!")

def main():
    """Main demo function"""
    demo = LocalStorageDemo()
    
    # Target subreddits for demo
    target_subreddits = ['marathi', 'mumbai']  # Start with 2 for demo
    
    print("This demo will:")
    print("- Scrape posts and comments from r/marathi and r/mumbai")
    print("- Detect Marathi language with 95%+ accuracy")
    print("- Separate mixed Marathi/English content")
    print("- Save results to local JSON file")
    print("- Show processing statistics")
    
    input("\nPress Enter to start demo...")
    
    try:
        demo.run_demo_scrape(target_subreddits, max_posts_per_subreddit=15)
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        demo.print_final_results()
        demo.save_data()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    main()