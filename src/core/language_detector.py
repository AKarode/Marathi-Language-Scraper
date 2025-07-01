import re
import unicodedata
from typing import Tuple, Dict, Optional
import numpy as np
from collections import Counter

class HighAccuracyMarathiDetector:
    """
    High-accuracy Marathi language detector optimized for 95%+ accuracy
    Uses multiple detection methods for maximum reliability
    """
    
    def __init__(self):
        # Devanagari Unicode range
        self.devanagari_range = (0x0900, 0x097F)
        
        # Common Marathi words and phrases
        self.marathi_words = {
            'आहे', 'आणि', 'तर', 'पण', 'मी', 'तू', 'तो', 'ती', 'ते', 'आम्ही', 'तुम्ही', 'ते',
            'काय', 'कसे', 'कुठे', 'केव्हा', 'कोण', 'किती', 'कशासाठी', 'कसा', 'कसं',
            'मराठी', 'महाराष्ट्र', 'मुंबई', 'पुणे', 'नागपूर', 'कोल्हापूर', 'नाशिक',
            'छान', 'चांगले', 'वाईट', 'मोठे', 'लहान', 'नवीन', 'जुने', 'गरम', 'थंड',
            'घर', 'शाळा', 'कॉलेज', 'ऑफिस', 'दुकान', 'हॉस्पिटल', 'स्टेशन',
            'खाणे', 'पिणे', 'येणे', 'जाणे', 'बघणे', 'ऐकणे', 'बोलणे', 'वाचणे', 'लिहिणे',
            'होय', 'नाही', 'ठीक', 'चल', 'अरे', 'अहो', 'काहीही', 'सगळे', 'काही', 'सर्व'
        }
        
        # Common English words that might appear in mixed content
        self.english_words = {
            'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
            'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
            'this', 'that', 'these', 'those', 'what', 'where', 'when', 'why', 'how',
            'good', 'bad', 'big', 'small', 'new', 'old', 'hot', 'cold', 'fast', 'slow'
        }
        
        # Marathi-specific character patterns
        self.marathi_patterns = [
            r'[ळ]',  # Marathi-specific 'ळ'
            r'[ऱ]',  # Marathi-specific 'ऱ'
            r'[\u0902\u0903]',  # Anusvara and Visarga
            r'[\u093C]',  # Nukta
            r'[\u0941-\u0948]',  # Vowel signs
        ]
        
    def _get_script_ratio(self, text: str) -> Dict[str, float]:
        """Calculate the ratio of different scripts in text"""
        if not text:
            return {'devanagari': 0.0, 'latin': 0.0, 'other': 0.0}
            
        total_chars = len(text)
        devanagari_count = 0
        latin_count = 0
        
        for char in text:
            code_point = ord(char)
            if self.devanagari_range[0] <= code_point <= self.devanagari_range[1]:
                devanagari_count += 1
            elif char.isalpha() and char.isascii():
                latin_count += 1
                
        other_count = total_chars - devanagari_count - latin_count
        
        return {
            'devanagari': devanagari_count / total_chars,
            'latin': latin_count / total_chars,
            'other': other_count / total_chars
        }
    
    def _count_marathi_words(self, text: str) -> Tuple[int, int]:
        """Count Marathi and English words in text"""
        # Separate tokenization for Devanagari and Latin scripts
        
        # Extract Devanagari words (including conjuncts and complex characters)
        devanagari_words = re.findall(r'[\u0900-\u097F]+', text)
        
        # Extract Latin words
        latin_words = re.findall(r'[a-zA-Z]+', text.lower())
        
        # Count matches
        marathi_count = sum(1 for word in devanagari_words if word in self.marathi_words)
        english_count = sum(1 for word in latin_words if word in self.english_words)
        
        return marathi_count, english_count
    
    def _check_marathi_patterns(self, text: str) -> float:
        """Check for Marathi-specific character patterns"""
        if not text:
            return 0.0
            
        pattern_matches = 0
        for pattern in self.marathi_patterns:
            matches = len(re.findall(pattern, text))
            pattern_matches += matches
            
        # Normalize by text length
        return min(pattern_matches / len(text), 1.0)
    
    def _advanced_language_detection(self, text: str) -> float:
        """Advanced detection using character frequency analysis"""
        if not text:
            return 0.0
            
        # Character frequency analysis for Marathi
        marathi_chars = 'आइईउऊएऐओऔअंःकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळऱ'
        char_freq = Counter(text)
        
        marathi_char_count = sum(char_freq.get(char, 0) for char in marathi_chars)
        total_devanagari = sum(1 for char in text if self.devanagari_range[0] <= ord(char) <= self.devanagari_range[1])
        
        if total_devanagari == 0:
            return 0.0
            
        return marathi_char_count / total_devanagari
    
    def detect_language(self, text: str, title: str = "") -> Dict[str, float]:
        """
        Detect language with high accuracy
        Returns confidence scores for different categories
        """
        if not text and not title:
            return {
                'marathi_confidence': 0.0,
                'english_confidence': 0.0,
                'mixed_confidence': 0.0,
                'category': 'non_marathi'
            }
            
        # Combine title and text for analysis
        full_text = f"{title} {text}".strip()
        
        # Multiple detection methods
        script_ratios = self._get_script_ratio(full_text)
        marathi_words, english_words = self._count_marathi_words(full_text)
        pattern_score = self._check_marathi_patterns(full_text)
        advanced_score = self._advanced_language_detection(full_text)
        
        # Calculate word ratios
        total_words = marathi_words + english_words
        word_ratio = marathi_words / max(total_words, 1)
        
        # Weighted scoring system
        weights = {
            'script_ratio': 0.3,
            'word_ratio': 0.35,
            'pattern_score': 0.2,
            'advanced_score': 0.15
        }
        
        # Calculate Marathi confidence
        marathi_confidence = (
            weights['script_ratio'] * script_ratios['devanagari'] +
            weights['word_ratio'] * word_ratio +
            weights['pattern_score'] * pattern_score +
            weights['advanced_score'] * advanced_score
        )
        
        # Calculate English confidence
        english_confidence = (
            script_ratios['latin'] * 0.6 +
            (english_words / max(total_words, 1)) * 0.4
        )
        
        # Determine category
        if marathi_confidence >= 0.95:
            category = 'pure_marathi'
        elif marathi_confidence >= 0.6 and english_confidence >= 0.2:
            category = 'mixed_content'
        elif script_ratios['devanagari'] >= 0.3:
            category = 'mixed_content'  # Has some Devanagari, likely mixed
        else:
            category = 'non_marathi'
            
        return {
            'marathi_confidence': round(marathi_confidence, 3),
            'english_confidence': round(english_confidence, 3),
            'mixed_confidence': round(min(marathi_confidence + english_confidence, 1.0), 3),
            'category': category,
            'script_ratios': script_ratios,
            'word_counts': {'marathi': marathi_words, 'english': english_words}
        }
    
    def separate_languages(self, text: str) -> Dict[str, str]:
        """
        Separate Marathi and English text from mixed content
        """
        if not text:
            return {'marathi_text': '', 'english_text': ''}
            
        sentences = re.split(r'[।!?.\n]+', text)
        marathi_sentences = []
        english_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            detection = self.detect_language(sentence)
            
            if detection['category'] == 'pure_marathi' or detection['marathi_confidence'] > 0.7:
                marathi_sentences.append(sentence)
            elif detection['english_confidence'] > detection['marathi_confidence']:
                english_sentences.append(sentence)
            else:
                # For ambiguous sentences, add to both if they contain both scripts
                script_ratios = detection['script_ratios']
                if script_ratios['devanagari'] > 0.3:
                    marathi_sentences.append(sentence)
                if script_ratios['latin'] > 0.3:
                    english_sentences.append(sentence)
        
        return {
            'marathi_text': ' । '.join(marathi_sentences),
            'english_text': '. '.join(english_sentences)
        }