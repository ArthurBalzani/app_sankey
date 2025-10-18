"""
Module for text processing and extraction of significant words.
"""

import re
import unicodedata
from collections import Counter
from typing import List, Set, Optional
import nltk
from nltk.corpus import stopwords
import streamlit as st

from config import MIN_WORD_LENGTH, ADDITIONAL_STOP_WORDS


def get_portuguese_stopwords(custom_stop_words: Optional[Set[str] | frozenset[str]] = None) -> Set[str]:
    """
    Gets the list of Portuguese stopwords and adds custom words.
    
    Args:
        custom_stop_words: Set or frozenset of custom words to add.
        
    Returns:
        Set of all stopwords (default + custom).
    """
    try:
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('portuguese'))
        stop_words.update(ADDITIONAL_STOP_WORDS)
        
        if custom_stop_words:
            stop_words.update(custom_stop_words)
            
    except Exception as e:
        print(f"Error loading stopwords: {e}")
        stop_words = set()
    
    return stop_words


def normalize_text(text: str) -> str:
    """
    Normalizes text by removing accents.
    
    Args:
        text: Text to be normalized.
        
    Returns:
        Normalized text.
    """
    text_nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in text_nfkd if not unicodedata.combining(c)])


def extract_words(text, custom_stop_words: Optional[Set[str] | frozenset[str]] = None) -> List[str]:
    """
    Extracts significant words from text.
    
    Filters stopwords, very short words, and normalizes the text.
    
    Args:
        text: Text to process. If NaN, returns empty list.
        custom_stop_words: Set of custom words to filter.
        
    Returns:
        List of significant words.
    """
    import pandas as pd
    
    if pd.isna(text):
        return []
    
    stop_words = get_portuguese_stopwords(custom_stop_words)
    
    # Convert to string and lowercase
    text_str = str(text).lower()
    
    # Normalize (remove accents)
    text_norm = normalize_text(text_str)
    
    # Extract words
    words = re.findall(r'\b\w+\b', text_norm)
    
    # Filter stopwords and short words
    words = [w for w in words if w not in stop_words and len(w) > MIN_WORD_LENGTH]
    
    return words


@st.cache_data
def extract_words_cached(text, custom_stop_words: Optional[Set[str]] = None) -> List[str]:
    """
    Cached version of extract_words for better performance.
    
    Note: Caching is essential in Streamlit to avoid reprocessing.
    
    Args:
        text: Text to process.
        custom_stop_words: Set of custom words to filter.
        
    Returns:
        List of significant words.
    """
    # Convert set to frozenset to be hashable (cache requirement)
    custom_stop_words_frozen = frozenset(custom_stop_words) if custom_stop_words else frozenset()
    
    return extract_words(text, custom_stop_words_frozen)


def get_word_frequency(texts: List[str], 
                       n_words: int = 20,
                       custom_stop_words: Optional[Set[str]] = None) -> dict:
    """
    Calculates the frequency of the most common words.
    
    Args:
        texts: List of texts to analyze.
        n_words: Number of most frequent words to return.
        custom_stop_words: Set of custom words to filter.
        
    Returns:
        Dictionary with words and their frequencies (sorted).
    """
    all_words = []
    
    for text in texts:
        all_words.extend(extract_words(text, custom_stop_words))
    
    if not all_words:
        return {}
    
    counter = Counter(all_words)
    return dict(counter.most_common(n_words))


def parse_custom_stopwords(input_string: str) -> Set[str]:
    """
    Converts a string with words into a set of stopwords.
    
    Supports separation by comma, space, or line break.
    
    Args:
        input_string: String with words separated.
        
    Returns:
        Set of cleaned and lowercase words.
    """
    if not input_string:
        return set()
    
    words = set(
        word.strip().lower() 
        for word in re.split(r'[,\s]+', input_string) 
        if word.strip()
    )
    
    return words
