"""
Module for creating visualizations, especially Sankey charts.
"""

from typing import List, Optional, Dict, Mapping, Union, TYPE_CHECKING
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.express as px
from matplotlib.colors import to_rgba
from collections import Counter
import pandas as pd

from config import (
    DEFAULT_OPACITY,
    DEFAULT_MAIN_NODE_COLOR,
    SANKEY_TITLE,
    WORD_COLUMN_NAME,
    FREQUENCY_COLUMN_NAME,
)
from src.text_processing import extract_words, get_word_frequency

if TYPE_CHECKING:
    pass

# Accept either the legacy single-column API or multi-question mapping.
QuestionTexts = Mapping[str, List[str]]


def _convert_color_to_rgba(color: str, opacity: float) -> str:
    """
    Converts a hex or rgb color to rgba format.
    
    Args:
        color: Color in hex or rgb format.
        opacity: Opacity (0-1).
        
    Returns:
        String in rgba format.
    """
    if color.startswith("#"):
        rgba = to_rgba(color)
        return f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {opacity})"
    
    elif color.startswith("rgb("):
        color_values = color.replace("rgb(", "").replace(")", "")
        r, g, b = map(int, color_values.split(","))
        return f"rgba({r}, {g}, {b}, {opacity})"
    
    return color


def get_color_palette(palette_name: str, invert: bool = False) -> List[str]:
    """
    Gets a color palette by name.
    
    Args:
        palette_name: Name of the palette (ex: 'Viridis', 'Plasma').
        invert: If True, reverses the order of colors.
        
    Returns:
        List of colors from the palette.
    """
    palettes = {
        "Viridis": pc.sequential.Viridis,
        "Plasma": pc.sequential.Plasma,
        "Inferno": pc.sequential.Inferno,
        "Magma": pc.sequential.Magma,
        "Cividis": pc.sequential.Cividis,
        "Rainbow": pc.sequential.Rainbow,
        "Jet": pc.sequential.Jet,
        "Turbo": pc.sequential.Turbo,
        "Blues": pc.sequential.Blues,
        "Greens": pc.sequential.Greens,
        "Reds": pc.sequential.Reds,
        "YlOrRd": pc.sequential.YlOrRd,
        "YlGnBu": pc.sequential.YlGnBu,
        "PuRd": pc.sequential.PuRd,
        "RdPu": pc.sequential.RdPu,
        "Spectral": px.colors.diverging.Spectral,
        "RdYlBu": px.colors.diverging.RdYlBu
    }
    
    colorscale = palettes.get(palette_name, pc.sequential.Viridis)
    
    if invert:
        colorscale = colorscale[::-1]
    
    return colorscale


def _normalize_question_texts(
    texts_or_questions: Union[List[str], QuestionTexts],
    single_label: str = "Pergunta",
) -> Dict[str, List[str]]:
    """Normalize legacy list-of-texts or multi-question mapping."""
    if isinstance(texts_or_questions, Mapping):
        return {str(k): list(v) for k, v in texts_or_questions.items()}
    return {single_label: list(texts_or_questions)}


def build_question_word_frequencies(
    question_texts: QuestionTexts,
    n_words: int = 20,
    custom_stop_words: Optional[set] = None,
) -> tuple[Dict[str, Dict[str, int]], List[str], Dict[str, int]]:
    """
    Build per-question word frequencies and the shared top-N word universe.

    Returns:
        per_question: {question -> {word -> freq}}
        top_words: ordered list of unique words by total frequency (desc)
        totals: {word -> sum of freqs across questions}
    """
    per_question: Dict[str, Dict[str, int]] = {}
    totals: Counter = Counter()

    for question, texts in question_texts.items():
        all_words: List[str] = []
        for text in texts:
            all_words.extend(extract_words(text, custom_stop_words))
        counts = Counter(all_words)
        per_question[question] = dict(counts)
        totals.update(counts)

    if not totals:
        return {}, [], {}

    top_words = [word for word, _ in totals.most_common(n_words)]
    top_totals = {word: totals[word] for word in top_words}

    # Keep only top words in per-question maps for link creation
    trimmed: Dict[str, Dict[str, int]] = {}
    for question, counts in per_question.items():
        trimmed[question] = {
            word: counts[word] for word in top_words if counts.get(word, 0) > 0
        }

    return trimmed, top_words, top_totals


def create_sankey_diagram(
    texts_or_questions: Union[List[str], QuestionTexts],
    n_words: int = 20,
    colorscale: Optional[List[str]] = None,
    main_node_color: str = DEFAULT_MAIN_NODE_COLOR,
    opacity: float = DEFAULT_OPACITY,
    height: int = 600,
    custom_stop_words: Optional[set] = None,
    single_question_label: str = "Pergunta",
) -> Optional[go.Figure]:
    """
    Creates a Sankey chart: questions (left) → unique words (right).

    - Left nodes: one per selected question/column.
    - Right nodes: unique words across the selected questions (shared).
    - Link weight: frequency of that word within that question.
    - With a single question (legacy list or one mapping entry), behavior
      matches the previous star diagram (one source → words by frequency).

    Args:
        texts_or_questions: List of texts (legacy) or {question_label: texts}.
        n_words: Number of most frequent words (by total across questions).
        colorscale: Color palette for word-frequency coloring (single question).
        main_node_color: Color of question node(s) / origin coloring base.
        opacity: Opacity of connections (0-1).
        height: Height of the chart in pixels.
        custom_stop_words: Set of custom words to filter.
        single_question_label: Label used when passing a bare list of texts.

    Returns:
        Plotly Figure or None if there are no significant words.
    """
    question_texts = _normalize_question_texts(
        texts_or_questions, single_label=single_question_label
    )
    if not question_texts:
        return None

    per_question, top_words, word_totals = build_question_word_frequencies(
        question_texts, n_words=n_words, custom_stop_words=custom_stop_words
    )

    if not top_words:
        return None

    questions = list(question_texts.keys())
    n_questions = len(questions)

    # Node layout: questions first (left), then shared words (right)
    nodes_labels = list(questions) + list(top_words)
    word_index = {word: n_questions + i for i, word in enumerate(top_words)}

    source: List[int] = []
    target: List[int] = []
    value: List[int] = []

    for q_idx, question in enumerate(questions):
        for word, freq in per_question.get(question, {}).items():
            source.append(q_idx)
            target.append(word_index[word])
            value.append(freq)

    if not value:
        return None

    if colorscale is None:
        colorscale = pc.sequential.Viridis

    main_node_rgba = _convert_color_to_rgba(main_node_color, opacity)
    max_total = max(word_totals.values()) if word_totals else 1

    # Question (left) node colors — distinct when multiple questions
    question_colors: List[str] = []
    if n_questions == 1:
        question_colors = [main_node_rgba]
    else:
        positions = [
            i / max(n_questions - 1, 1) for i in range(n_questions)
        ]
        for i, pos in enumerate(positions):
            if i == 0:
                question_colors.append(main_node_rgba)
                continue
            sampled = pc.sample_colorscale(colorscale, pos)[0]
            if isinstance(sampled, tuple):
                r, g, b = [int(c * 255) for c in sampled[:3]]
                sampled = f"rgb({r}, {g}, {b})"
            question_colors.append(_convert_color_to_rgba(str(sampled), 1.0))

    # Word (right) node colors — by total frequency (same spirit as before)
    word_node_colors: List[str] = []
    for word in top_words:
        normalized = word_totals[word] / max_total
        color_base = pc.sample_colorscale(colorscale, normalized)[0]
        if isinstance(color_base, tuple):
            r, g, b = [int(c * 255) for c in color_base[:3]]
            color_base = f"rgb({r}, {g}, {b})"
        word_node_colors.append(_convert_color_to_rgba(str(color_base), opacity))

    # Link colors: single question → by word frequency (legacy look);
    # multiple questions → by origin (question), like Dim1→Dim2 reference.
    link_colors: List[str] = []
    if n_questions == 1:
        for word_idx_in_link in target:
            word = top_words[word_idx_in_link - n_questions]
            normalized = word_totals[word] / max_total
            color_base = pc.sample_colorscale(colorscale, normalized)[0]
            if isinstance(color_base, tuple):
                r, g, b = [int(c * 255) for c in color_base[:3]]
                color_base = f"rgb({r}, {g}, {b})"
            link_colors.append(_convert_color_to_rgba(str(color_base), opacity))
    else:
        for q_idx in source:
            # Solid origin color with link opacity
            base = question_colors[q_idx]
            # Re-apply opacity on already-rgba question colors
            if base.startswith("rgba("):
                inner = base[5:-1].split(",")
                r, g, b = inner[0].strip(), inner[1].strip(), inner[2].strip()
                link_colors.append(f"rgba({r}, {g}, {b}, {opacity})")
            else:
                link_colors.append(_convert_color_to_rgba(base, opacity))

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes_labels,
            color=question_colors + word_node_colors,
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
        ),
    )])

    fig.update_layout(
        title_text=SANKEY_TITLE,
        font_size=12,
        height=height,
        margin=dict(l=25, r=25, t=50, b=25),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def create_word_frequency_dataframe(
    texts_or_questions: Union[List[str], QuestionTexts],
    n_words: int = 20,
    custom_stop_words: Optional[set] = None,
    single_question_label: str = "Pergunta",
) -> "pd.DataFrame":
    """
    Creates a DataFrame with word frequency.

    With multiple questions, returns columns:
    Palavra | Total | <each question> (freq in that question).

    With a single question / legacy list, returns:
    Palavra | Frequência (same as before).
    """
    question_texts = _normalize_question_texts(
        texts_or_questions, single_label=single_question_label
    )
    per_question, top_words, word_totals = build_question_word_frequencies(
        question_texts, n_words=n_words, custom_stop_words=custom_stop_words
    )

    if not top_words:
        return pd.DataFrame(columns=[WORD_COLUMN_NAME, FREQUENCY_COLUMN_NAME])

    questions = list(question_texts.keys())

    if len(questions) == 1:
        q = questions[0]
        rows = [
            (word, per_question.get(q, {}).get(word, word_totals[word]))
            for word in top_words
        ]
        return pd.DataFrame(rows, columns=[WORD_COLUMN_NAME, FREQUENCY_COLUMN_NAME])

    rows = []
    for word in top_words:
        row = {WORD_COLUMN_NAME: word, "Total": word_totals[word]}
        for q in questions:
            row[q] = per_question.get(q, {}).get(word, 0)
        rows.append(row)

    columns = [WORD_COLUMN_NAME, "Total"] + questions
    return pd.DataFrame(rows, columns=columns)
