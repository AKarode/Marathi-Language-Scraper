import re
import unicodedata
from typing import Dict, List, Optional, Tuple
import html

class LLMOptimizedTextProcessor:
    """
    Text processor optimized for LLM tokenization and training
    Handles Marathi/Devanagari text preprocessing for optimal token efficiency
    """
    
    def __init__(self):
        # Common Reddit formatting patterns to clean
        self.reddit_patterns = [
            (r'\*\*(.*?)\*\*', r'\1'),  # Bold markdown
            (r'\*(.*?)\*', r'\1'),      # Italic markdown
            (r'~~(.*?)~~', r'\1'),      # Strikethrough
            (r'\[([^\]]+)\]\([^)]+\)', r'\1'),  # Links [text](url) -> text
            (r'&gt;!([^!]+)!&lt;', r'\1'),  # Spoiler tags
            (r'^&gt;\s*', '', re.MULTILINE),  # Quote markers
            (r'^\s*\*\s+', '', re.MULTILINE),  # List bullets
            (r'^\s*\d+\.\s+', '', re.MULTILINE),  # Numbered lists
        ]
        
        # Devanagari normalization patterns
        self.devanagari_normalizations = [
            # Normalize similar looking characters
            ('।', '.'),  # Devanagari danda to period for consistency
            ('॥', '..'), # Double danda to double period
            # Normalize zero-width characters
            ('\u200c', ''),  # Zero-width non-joiner
            ('\u200d', ''),  # Zero-width joiner
            ('\ufeff', ''),  # Byte order mark
        ]
        
        # Token-efficient sentence markers
        self.sentence_markers = {
            'marathi': ' । ',  # Devanagari sentence separator
            'english': '. ',   # English sentence separator
            'mixed': ' | ',    # Mixed content separator
        }
    
    def clean_reddit_formatting(self, text: str) -> str:
        """Remove Reddit-specific formatting for cleaner tokenization"""
        if not text:
            return ""
        
        # HTML decode first
        text = html.unescape(text)
        
        # Apply Reddit formatting cleanup
        for pattern, replacement, *flags in self.reddit_patterns:
            if flags:
                text = re.sub(pattern, replacement, text, flags=flags[0])
            else:
                text = re.sub(pattern, replacement, text)
        
        return text.strip()
    
    def normalize_devanagari(self, text: str) -> str:
        """Normalize Devanagari text for consistent tokenization"""
        if not text:
            return ""
        
        # Unicode normalization (NFKC for compatibility)
        text = unicodedata.normalize('NFKC', text)
        
        # Apply Devanagari-specific normalizations
        for old, new in self.devanagari_normalizations:
            text = text.replace(old, new)
        
        # Normalize whitespace around Devanagari punctuation
        text = re.sub(r'\s*([।॥])\s*', r'\1 ', text)
        
        return text
    
    def segment_sentences(self, text: str, language_hint: str = 'mixed') -> List[str]:
        """
        Segment text into sentences optimized for LLM context windows
        
        Args:
            text: Input text
            language_hint: 'marathi', 'english', or 'mixed'
        
        Returns:
            List of sentence segments
        """
        if not text:
            return []
        
        # Clean and normalize first
        text = self.clean_reddit_formatting(text)
        text = self.normalize_devanagari(text)
        
        # Language-specific sentence splitting
        if language_hint == 'marathi':
            # Devanagari sentence patterns
            sentences = re.split(r'[।॥]+\s*', text)
        elif language_hint == 'english':
            # English sentence patterns
            sentences = re.split(r'[.!?]+\s+', text)
        else:
            # Mixed content - split on both patterns
            # First split on Devanagari, then on English within each segment
            segments = re.split(r'[।॥]+\s*', text)
            sentences = []
            for segment in segments:
                if re.search(r'[a-zA-Z]', segment):
                    # Has English, further split
                    sub_sentences = re.split(r'[.!?]+\s+', segment)
                    sentences.extend(sub_sentences)
                else:
                    sentences.append(segment)
        
        # Clean up and filter
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def create_llm_optimized_content(self, title: str, body: str, 
                                   marathi_text: str, english_text: str,
                                   metadata: Dict) -> Dict[str, str]:
        """
        Create LLM-optimized content versions for different use cases
        
        Returns:
            Dictionary with different formatted versions for LLM consumption
        """
        
        # Clean inputs
        title = self.clean_reddit_formatting(title or "")
        body = self.clean_reddit_formatting(body or "")
        marathi_text = self.normalize_devanagari(marathi_text or "")
        english_text = self.clean_reddit_formatting(english_text or "")
        
        result = {}
        
        # 1. Compact format (for token efficiency)
        compact_parts = []
        if title:
            compact_parts.append(f"शीर्षक: {title}" if marathi_text else f"Title: {title}")
        if marathi_text:
            compact_parts.append(f"मराठी: {marathi_text}")
        if english_text:
            compact_parts.append(f"English: {english_text}")
        
        result['compact'] = " | ".join(compact_parts)
        
        # 2. Training format (structured for fine-tuning)
        result['training'] = {
            'instruction': f"Analyze this {metadata.get('content_type', 'post')} from r/{metadata.get('subreddit', 'unknown')}",
            'input': f"{title}\n\n{body}".strip(),
            'output': {
                'marathi_content': marathi_text,
                'english_content': english_text,
                'language_category': metadata.get('language_category', 'unknown'),
                'confidence': metadata.get('marathi_confidence', 0.0)
            }
        }
        
        # 3. Context format (for RAG/embeddings)
        context_parts = []
        if title and body:
            context_parts.append(f"Reddit {metadata.get('content_type', 'post')}: {title}")
            context_parts.append(body)
        elif title:
            context_parts.append(title)
        elif body:
            context_parts.append(body)
        
        if marathi_text and english_text:
            context_parts.append(f"Marathi content: {marathi_text}")
            context_parts.append(f"English content: {english_text}")
        
        result['context'] = "\n\n".join(context_parts)
        
        # 4. Segmented format (for long context handling)
        sentences = self.segment_sentences(
            f"{title} {body}".strip(), 
            metadata.get('language_category', 'mixed')
        )
        
        result['segmented'] = {
            'sentences': sentences,
            'marathi_sentences': self.segment_sentences(marathi_text, 'marathi') if marathi_text else [],
            'english_sentences': self.segment_sentences(english_text, 'english') if english_text else []
        }
        
        # 5. Clean format (minimal processing, preserves structure)
        clean_content = []
        if title:
            clean_content.append(title)
        if body:
            clean_content.append(body)
        
        result['clean'] = "\n\n".join(clean_content)
        
        # 6. Token count estimates (approximate)
        result['token_estimates'] = {
            'compact': len(result['compact'].split()) * 1.3,  # Rough estimate for mixed content
            'context': len(result['context'].split()) * 1.3,
            'clean': len(result['clean'].split()) * 1.3
        }
        
        return result
    
    def create_training_dataset_entry(self, processed_content: Dict) -> Dict:
        """
        Create a standardized training dataset entry
        
        Args:
            processed_content: Output from main processing pipeline
            
        Returns:
            Training-ready dataset entry
        """
        
        # Create optimized content
        llm_content = self.create_llm_optimized_content(
            title=processed_content.get('title', ''),
            body=processed_content.get('body', ''),
            marathi_text=processed_content.get('marathi_text', ''),
            english_text=processed_content.get('english_text', ''),
            metadata={
                'content_type': processed_content.get('content_type'),
                'subreddit': processed_content.get('subreddit'),
                'language_category': processed_content.get('language_category'),
                'marathi_confidence': processed_content.get('marathi_confidence', 0.0)
            }
        )
        
        # Training dataset format
        training_entry = {
            'id': processed_content.get('reddit_id'),
            'source': f"reddit_r_{processed_content.get('subreddit')}",
            'metadata': {
                'language': 'marathi',
                'category': processed_content.get('language_category'),
                'confidence': processed_content.get('marathi_confidence'),
                'content_type': processed_content.get('content_type'),
                'subreddit': processed_content.get('subreddit'),
                'created_utc': processed_content.get('reddit_created_utc')
            },
            'text_formats': {
                'raw': processed_content.get('body', ''),
                'clean': llm_content['clean'],
                'compact': llm_content['compact'],
                'context': llm_content['context']
            },
            'language_separated': {
                'marathi': processed_content.get('marathi_text', ''),
                'english': processed_content.get('english_text', '')
            },
            'segmented': llm_content['segmented'],
            'token_estimates': llm_content['token_estimates']
        }
        
        return training_entry
    
    def validate_for_llm_training(self, content: str, min_length: int = 10, 
                                 max_length: int = 2048) -> Tuple[bool, str]:
        """
        Validate content for LLM training suitability
        
        Returns:
            (is_valid, reason)
        """
        if not content or not content.strip():
            return False, "Empty content"
        
        content = content.strip()
        
        if len(content) < min_length:
            return False, f"Content too short ({len(content)} < {min_length})"
        
        if len(content) > max_length:
            return False, f"Content too long ({len(content)} > {max_length})"
        
        # Check for meaningful content (not just punctuation/numbers)
        meaningful_chars = re.sub(r'[\s\d\W]', '', content)
        if len(meaningful_chars) < min_length // 2:
            return False, "Insufficient meaningful content"
        
        # Check for Devanagari content if this is supposed to be Marathi
        devanagari_chars = re.findall(r'[\u0900-\u097F]', content)
        if len(devanagari_chars) < 3:  # At least some Devanagari for Marathi content
            return False, "Insufficient Devanagari characters for Marathi content"
        
        return True, "Valid for training"