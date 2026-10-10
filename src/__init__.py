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
    build_sankey_diagram,
    create_sankey_diagram,
    create_word_frequency_dataframe,
    get_color_palette,
    build_question_word_frequencies,
)

from src.sankey_style import (
    default_style_state,
    ensure_style_state,
    make_content_key,
    node_id_for_question,
    node_id_for_word,
    parse_node_id,
    reset_style_customizations,
    resolve_label_style,
    resolve_plotly_node_colors,
    resolve_plotly_link_colors,
    default_question_color_for_index,
    apply_native_label_styles,
    needs_pinned_node_positions,
)

__all__ = [
    'extract_words',
    'extract_words_cached',
    'get_word_frequency',
    'parse_custom_stopwords',
    'get_portuguese_stopwords',
    'normalize_text',
    'build_sankey_diagram',
    'create_sankey_diagram',
    'create_word_frequency_dataframe',
    'get_color_palette',
    'build_question_word_frequencies',
    'default_style_state',
    'ensure_style_state',
    'make_content_key',
    'node_id_for_question',
    'node_id_for_word',
    'parse_node_id',
    'reset_style_customizations',
    'resolve_label_style',
    'resolve_plotly_node_colors',
    'resolve_plotly_link_colors',
    'default_question_color_for_index',
    'apply_native_label_styles',
    'needs_pinned_node_positions',
]
