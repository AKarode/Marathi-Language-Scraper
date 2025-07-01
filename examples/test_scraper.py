#!/usr/bin/env python3
"""
Test script for Marathi Reddit Scraper (without Supabase)
This demonstrates the working components while Supabase connection is being resolved
"""

import json
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.reddit_scraper import RedditScraper
from src.core.language_detector import HighAccuracyMarathiDetector

def test_scraper():
    """Run a comprehensive test of the scraper components"""
    
    print("🎯 Marathi Reddit Scraper - Test Run")
    print("=" * 50)
    
    # Initialize components
    scraper = RedditScraper()
    detector = HighAccuracyMarathiDetector()
    
    # Test subreddits
    test_subreddits = ['marathi', 'mumbai']
    
    results = {
        'total_processed': 0,
        'pure_marathi': 0,
        'mixed_content': 0,
        'non_marathi': 0,
        'sample_data': []
    }
    
    for subreddit_name in test_subreddits:
        print(f"\n🔍 Scraping r/{subreddit_name}...")
        
        try:
            post_count = 0
            for post_data in scraper.scrape_subreddit_posts(subreddit_name, limit=10):
                if post_count >= 5:  # Limit for testing
                    break
                    
                post_count += 1
                results['total_processed'] += 1
                
                # Process with language detector
                detection_result = detector.detect_language(
                    text=post_data.get('body', ''),
                    title=post_data.get('title', '')
                )
                
                # Update stats
                category = detection_result['category']
                if category == 'pure_marathi':
                    results['pure_marathi'] += 1
                elif category == 'mixed_content':
                    results['mixed_content'] += 1
                else:
                    results['non_marathi'] += 1
                
                # Store sample data
                sample_entry = {
                    'reddit_id': post_data['reddit_id'],
                    'subreddit': subreddit_name,
                    'title': post_data.get('title', '')[:100],
                    'body_preview': post_data.get('body', '')[:200],
                    'category': category,
                    'confidence': detection_result['marathi_confidence'],
                    'created_utc': post_data.get('reddit_created_utc').isoformat() if post_data.get('reddit_created_utc') else None
                }
                
                if category in ['pure_marathi', 'mixed_content']:
                    results['sample_data'].append(sample_entry)
                
                print(f"  📄 Post {post_count}: {category} (conf: {detection_result['marathi_confidence']:.3f})")
                
        except Exception as e:
            print(f"❌ Error scraping r/{subreddit_name}: {e}")
            continue
    
    # Print results
    print(f"\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Total Posts Processed: {results['total_processed']}")
    print(f"Pure Marathi: {results['pure_marathi']}")
    print(f"Mixed Content: {results['mixed_content']}")
    print(f"Non-Marathi: {results['non_marathi']}")
    
    if results['total_processed'] > 0:
        marathi_percentage = (results['pure_marathi'] + results['mixed_content']) / results['total_processed'] * 100
        print(f"Marathi Content Rate: {marathi_percentage:.1f}%")
    
    # Show sample Marathi content
    print(f"\n🔤 Sample Marathi Content Found:")
    print("-" * 50)
    
    for i, sample in enumerate(results['sample_data'][:3], 1):
        print(f"\n{i}. r/{sample['subreddit']} - {sample['category']} (conf: {sample['confidence']:.3f})")
        print(f"   Title: {sample['title']}")
        if sample['body_preview']:
            print(f"   Preview: {sample['body_preview']}...")
    
    # Save results to file
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Test completed! Results saved to test_results.json")
    print(f"📝 Found {len(results['sample_data'])} posts/comments with Marathi content")
    
    return results

if __name__ == "__main__":
    test_scraper()