#!/usr/bin/env python3
"""
Setup and validation script for Marathi Reddit Scraper
"""

import os
import sys
import logging
from typing import Dict, Any

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def check_environment_variables() -> Dict[str, bool]:
    """Check if all required environment variables are set"""
    # Load environment variables first
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET', 
        'REDDIT_USER_AGENT',
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    
    results = {}
    for var in required_vars:
        results[var] = bool(os.getenv(var))
        
    return results

def test_reddit_connection():
    """Test Reddit API connection"""
    try:
        from reddit_scraper import RedditScraper
        scraper = RedditScraper()
        
        # Test with a simple subreddit info fetch
        info = scraper.get_subreddit_info('marathi')
        if info:
            logging.info(f"✓ Reddit connection successful - r/marathi has {info['subscribers']} subscribers")
            return True
        else:
            logging.error("✗ Reddit connection failed - could not fetch subreddit info")
            return False
            
    except Exception as e:
        logging.error(f"✗ Reddit connection failed: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        from supabase_client import SupabaseClient
        client = SupabaseClient()
        
        # Test with a simple query
        stats = client.get_processing_stats()
        logging.info("✓ Supabase connection successful")
        return True
        
    except Exception as e:
        logging.error(f"✗ Supabase connection failed: {e}")
        return False

def test_language_detector():
    """Test language detection"""
    try:
        from language_detector import HighAccuracyMarathiDetector
        detector = HighAccuracyMarathiDetector()
        
        # Test with sample Marathi text
        test_text = "हे मराठी भाषेतील मजकूर आहे आणि तुम्ही कसे आहात"
        result = detector.detect_language(test_text)
        
        if result['marathi_confidence'] > 0.6:  # Adjusted threshold for testing
            logging.info(f"✓ Language detector working - confidence: {result['marathi_confidence']}, category: {result['category']}")
            return True
        else:
            logging.error(f"✗ Language detector failed - result: {result}")
            return False
            
    except Exception as e:
        logging.error(f"✗ Language detector failed: {e}")
        return False

def create_env_file():
    """Create .env file template"""
    if os.path.exists('.env'):
        logging.info("✓ .env file already exists")
        return
        
    try:
        with open('.env.example', 'r') as f:
            template = f.read()
            
        with open('.env', 'w') as f:
            f.write(template)
            
        logging.info("✓ Created .env file from template")
        logging.warning("Please edit .env file with your actual credentials")
        
    except Exception as e:
        logging.error(f"✗ Failed to create .env file: {e}")

def install_dependencies():
    """Install Python dependencies"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("✓ Dependencies installed successfully")
            return True
        else:
            logging.error(f"✗ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"✗ Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    setup_logging()
    
    print("Marathi Reddit Scraper - Setup & Validation")
    print("=" * 50)
    
    # Check if --install flag is provided
    install_deps = '--install' in sys.argv
    
    if install_deps:
        logging.info("Installing dependencies...")
        if not install_dependencies():
            sys.exit(1)
    
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Check environment variables
    logging.info("Checking environment variables...")
    env_vars = check_environment_variables()
    
    all_vars_set = True
    for var, is_set in env_vars.items():
        if is_set:
            logging.info(f"✓ {var} is set")
        else:
            logging.error(f"✗ {var} is not set")
            all_vars_set = False
    
    if not all_vars_set:
        logging.error("Please set all required environment variables in .env file")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test connections
    logging.info("Testing connections...")
    
    tests = [
        ("Language Detector", test_language_detector),
        ("Reddit API", test_reddit_connection),
        ("Supabase", test_supabase_connection)
    ]
    
    all_tests_passed = True
    for test_name, test_func in tests:
        logging.info(f"Testing {test_name}...")
        if not test_func():
            all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✓ All tests passed! Setup is complete.")
        print("\nYou can now run the scraper with:")
        print("  python main.py --test    # Test run")
        print("  python main.py           # Full run")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()