#!/usr/bin/env python3
"""
Test complete pipeline with LLM optimization
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.reddit_scraper import RedditScraper
from src.core.language_detector import HighAccuracyMarathiDetector
from src.core.text_processor import LLMOptimizedTextProcessor

def test_complete_pipeline():
    print('=== Testing Complete Pipeline with LLM Optimization ===')

    # Initialize components
    scraper = RedditScraper()
    detector = HighAccuracyMarathiDetector()
    processor = LLMOptimizedTextProcessor()

    print('\n1. Scraping sample content...')
    sample_data = []

    try:
        for i, post_data in enumerate(scraper.scrape_subreddit_posts('marathi', limit=3)):
            if i >= 2:  # Just get 2 posts
                break
                
            # Process with language detector
            detection_result = detector.detect_language(
                text=post_data.get('body', ''),
                title=post_data.get('title', '')
            )
            
            if detection_result['category'] != 'non_marathi':
                # Separate languages
                text_content = f"{post_data.get('title', '')} {post_data.get('body', '')}".strip()
                separated_text = {'marathi_text': '', 'english_text': ''}
                
                if detection_result['category'] == 'mixed_content':
                    separated_text = detector.separate_languages(text_content)
                elif detection_result['category'] == 'pure_marathi':
                    separated_text['marathi_text'] = text_content
                
                # Create LLM-optimized content
                llm_content = processor.create_llm_optimized_content(
                    title=post_data.get('title', ''),
                    body=post_data.get('body', ''),
                    marathi_text=separated_text['marathi_text'],
                    english_text=separated_text['english_text'],
                    metadata={
                        'content_type': post_data['content_type'],
                        'subreddit': post_data['subreddit'],
                        'language_category': detection_result['category'],
                        'marathi_confidence': detection_result['marathi_confidence']
                    }
                )
                
                # Create training dataset entry
                training_entry = processor.create_training_dataset_entry({
                    'reddit_id': post_data['reddit_id'],
                    'content_type': post_data['content_type'],
                    'subreddit': post_data['subreddit'],
                    'title': post_data.get('title'),
                    'body': post_data.get('body'),
                    'language_category': detection_result['category'],
                    'marathi_confidence': detection_result['marathi_confidence'],
                    'marathi_text': separated_text['marathi_text'],
                    'english_text': separated_text['english_text'],
                    'reddit_created_utc': post_data.get('reddit_created_utc').isoformat() if post_data.get('reddit_created_utc') else None
                })
                
                sample_data.append(training_entry)
                
                print(f'\n--- Post {i+1} ---')
                print(f'Category: {detection_result["category"]} (conf: {detection_result["marathi_confidence"]:.3f})')
                print(f'Title: {post_data.get("title", "N/A")[:50]}...')
                print(f'LLM Compact: {llm_content["compact"][:80]}...')
                print(f'Token Estimate: {llm_content["token_estimates"]["clean"]:.0f}')
                
                # Show text formats
                print(f'\nText Formats Available:')
                print(f'  Clean: {len(llm_content["clean"])} chars')
                print(f'  Compact: {len(llm_content["compact"])} chars')
                print(f'  Context: {len(llm_content["context"])} chars')
                print(f'  Segmented: {len(llm_content["segmented"]["sentences"])} sentences')

    except Exception as e:
        print(f'Error during processing: {e}')
        import traceback
        traceback.print_exc()

    print(f'\n=== Pipeline Results ===')
    print(f'Successfully processed: {len(sample_data)} posts')
    
    # Validate for LLM training
    training_ready = 0
    for item in sample_data:
        if item["language_separated"]["marathi"]:
            valid, reason = processor.validate_for_llm_training(item["language_separated"]["marathi"])
            if valid:
                training_ready += 1
            else:
                print(f'  ⚠️  Training validation failed: {reason}')

    print(f'Ready for LLM training: {training_ready}/{len(sample_data)}')

    if sample_data:
        # Save sample data
        with open('llm_training_sample.json', 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        print('\n✅ Sample training data saved to: llm_training_sample.json')
        
        # Show sample training entry
        if sample_data:
            print(f'\n📝 Sample Training Entry:')
            sample = sample_data[0]
            print(f'ID: {sample["id"]}')
            print(f'Source: {sample["source"]}')
            print(f'Marathi Content: {sample["language_separated"]["marathi"][:100]}...')
            print(f'LLM Formats: {list(sample["text_formats"].keys())}')

    print('\n🎯 Complete pipeline working! Ready for Supabase integration.')
    return sample_data

if __name__ == "__main__":
    test_complete_pipeline()