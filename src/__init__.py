"""
src package - Core modules of the application.
"""

from src.text_processing import (
    extract_words,
    extract_words_cached,
    get_word_frequency,
    parse_custom_stopwords,
    get_portuguese_stopwords,
    normalize_text
)

from src.visualization import (
    create_sankey_diagram,
    create_word_frequency_dataframe,
    get_color_palette
)

__all__ = [
    'extract_words',
    'extract_words_cached',
    'get_word_frequency',
    'parse_custom_stopwords',
    'get_portuguese_stopwords',
    'normalize_text',
    'create_sankey_diagram',
    'create_word_frequency_dataframe',
    'get_color_palette'
]
