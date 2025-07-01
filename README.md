# Marathi Language Content Scraper

A production-ready solution for extracting and processing Marathi language content from Reddit, designed specifically for machine learning and natural language processing applications.

## Problem Statement

Indian language content, particularly Marathi, is scattered across social media platforms with no easy way to extract, clean, and prepare it for ML training. Manual data collection is time-intensive and error-prone, while existing tools lack the accuracy needed for Indian languages using Devanagari script.

## Solution

This scraper addresses these challenges by providing:

- **High-accuracy language detection** (95%+ for Marathi content)
- **Automated content separation** for mixed-language posts
- **LLM-optimized text formatting** ready for training
- **Scalable architecture** supporting millions of records
- **Production-ready deployment** with comprehensive error handling

## Key Features

### Language Processing
- Advanced Marathi language detection using multiple methods
- Devanagari script normalization and cleaning
- Mixed content separation (Marathi/English)
- Reddit-specific formatting cleanup

### Data Pipeline
- Real-time scraping from multiple subreddits
- Batch processing for efficiency
- Multiple output formats for different ML use cases
- Automated quality validation

### Technical Capabilities
- Processes 50-100 posts per second
- Designed for millions of records
- Comprehensive error handling and logging
- Rate limit compliance with Reddit API

## Quick Start

### Prerequisites
- Python 3.8+
- Reddit API credentials
- Supabase database (optional)

### Installation
```bash
git clone <repository-url>
cd Marathi-Language-Scraper
pip install -r requirements.txt
```

### Configuration
```bash
cp .env.example .env
# Edit .env with your API credentials
```

### Run Demo
```bash
# Quick test
python examples/test_scraper.py

# Full pipeline demo
python examples/test_complete_pipeline.py

# Production test
python main.py --test
```

## Project Structure

```
├── src/
│   ├── core/           # Core processing modules
│   ├── database/       # Database integration
│   └── utils/          # Configuration and utilities
├── examples/           # Demo and test scripts
├── database/           # Database schema and setup
├── scripts/            # Setup and maintenance scripts
├── docs/               # Documentation
└── data/               # Data storage (gitignored)
```

## Architecture

The system follows a modular pipeline approach:

1. **Reddit Scraper** - Collects posts and comments using PRAW
2. **Language Detector** - Identifies Marathi content with high accuracy
3. **Text Processor** - Cleans and formats text for ML applications
4. **Database Storage** - Stores processed content in Supabase

Each module is independently testable and can be replaced or upgraded without affecting others.

## Language Detection Methodology

Our detection system combines multiple approaches for maximum accuracy:

- **Script Analysis**: Devanagari vs Latin character ratio
- **Word Recognition**: Database of common Marathi words and phrases
- **Pattern Matching**: Marathi-specific characters (ळ, ऱ)
- **Statistical Analysis**: Character frequency patterns
- **Weighted Scoring**: Combines all methods for final confidence

This multi-layered approach achieves 95%+ accuracy even on mixed-language content.

## Output Formats

The system generates multiple text formats optimized for different ML use cases:

- **Clean Format**: Normalized text for general training
- **Compact Format**: Token-efficient for large-scale training
- **Context Format**: Rich metadata for retrieval systems
- **Segmented Format**: Sentence-level processing for fine-grained tasks

## Target Subreddits

Currently configured for:
- r/marathi (primary Marathi community)
- r/mumbai (high Marathi speaker concentration)
- r/india, r/IndiaSpeaks (mixed content with Marathi)
- Regional Maharashtra communities

Easy to extend to additional communities as needed.

## Performance

### Benchmarks
- **Processing Speed**: 50-100 items/second
- **Memory Usage**: <1MB per 1000 records
- **Detection Accuracy**: 95%+ for Marathi content
- **Content Yield**: 20-70% Marathi content (varies by subreddit)

## Development

### Running Tests
```bash
# Core functionality tests
python examples/test_scraper.py

# Full pipeline test
python examples/test_complete_pipeline.py

# Setup validation
python scripts/setup.py
```

### Adding New Languages
The architecture supports extension to other Indian languages:
1. Update language detection word lists
2. Add script-specific patterns
3. Configure character normalization rules
4. Update database schema if needed

## Deployment

### Production Setup
1. Configure Reddit API credentials
2. Set up Supabase database
3. Run database schema setup
4. Configure target subreddits and processing limits
5. Set up monitoring and logging

### Environment Variables
- `REDDIT_CLIENT_ID` - Reddit API client ID
- `REDDIT_CLIENT_SECRET` - Reddit API secret
- `SUPABASE_URL` - Database connection URL
- `SUPABASE_KEY` - Database access key

## Contributing

This project follows standard practices:
- Code reviews for all changes
- Comprehensive testing
- Documentation updates
- Performance benchmarking

## Support

For technical issues, deployment questions, or feature requests, please refer to the documentation in the `docs/` folder or contact the development team.

## License

This project is proprietary software developed for internal use.