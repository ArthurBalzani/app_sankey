"""
Module for creating visualizations, especially Sankey charts.
"""

from typing import List, Optional, Dict, Mapping, Union, TYPE_CHECKING, TypedDict
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.express as px
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
from src.color_utils import convert_color_to_rgba
from src.sankey_style import SideName, node_id_for_question, node_id_for_word

if TYPE_CHECKING:
    pass

# Accept either the legacy single-column API or multi-question mapping.
QuestionTexts = Mapping[str, List[str]]


def _convert_color_to_rgba(color: str, opacity: float) -> str:
    """Backward-compatible alias for convert_color_to_rgba."""
    return convert_color_to_rgba(color, opacity)


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


class SankeyNodeLayout(TypedDict):
    node_id: str
    label: str
    side: SideName
    x: float
    y: float


class SankeyBuildResult(TypedDict):
    figure: go.Figure
    nodes: List[SankeyNodeLayout]
    questions: List[str]
    words: List[str]
    word_totals: Dict[str, int]


def _even_ys(count: int) -> List[float]:
    if count <= 0:
        return []
    if count == 1:
        return [0.5]
    return [0.05 + (0.90 * i / (count - 1)) for i in range(count)]


def build_sankey_diagram(
    texts_or_questions: Union[List[str], QuestionTexts],
    n_words: int = 20,
    colorscale: Optional[List[str]] = None,
    main_node_color: str = DEFAULT_MAIN_NODE_COLOR,
    opacity: float = DEFAULT_OPACITY,
    height: int = 600,
    custom_stop_words: Optional[set] = None,
    single_question_label: str = "Pergunta",
    node_colors: Optional[List[str]] = None,
    link_colors: Optional[List[str]] = None,
    hide_native_labels: bool = False,
    arrangement: str = "snap",
    pin_node_positions: bool = False,
) -> Optional[SankeyBuildResult]:
    """
    Builds a Sankey chart with explicit node anchors and optional hidden labels.

    Plotly ``arrangement`` is set only when ``pin_node_positions`` is True.

    Returns figure plus layout metadata (node anchors for style overrides).
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

    word_node_colors: List[str] = []
    for word in top_words:
        normalized = word_totals[word] / max_total
        color_base = pc.sample_colorscale(colorscale, normalized)[0]
        if isinstance(color_base, tuple):
            r, g, b = [int(c * 255) for c in color_base[:3]]
            color_base = f"rgb({r}, {g}, {b})"
        word_node_colors.append(_convert_color_to_rgba(str(color_base), opacity))

    computed_link_colors: List[str] = []
    if n_questions == 1:
        for word_idx_in_link in target:
            word = top_words[word_idx_in_link - n_questions]
            normalized = word_totals[word] / max_total
            color_base = pc.sample_colorscale(colorscale, normalized)[0]
            if isinstance(color_base, tuple):
                r, g, b = [int(c * 255) for c in color_base[:3]]
                color_base = f"rgb({r}, {g}, {b})"
            computed_link_colors.append(
                _convert_color_to_rgba(str(color_base), opacity)
            )
    else:
        for q_idx in source:
            base = question_colors[q_idx]
            if base.startswith("rgba("):
                inner = base[5:-1].split(",")
                r, g, b = inner[0].strip(), inner[1].strip(), inner[2].strip()
                computed_link_colors.append(
                    f"rgba({r}, {g}, {b}, {opacity})"
                )
            else:
                computed_link_colors.append(_convert_color_to_rgba(base, opacity))

    if link_colors is not None:
        if len(link_colors) != len(source):
            raise ValueError("link_colors length must match link count")
        final_link_colors = list(link_colors)
    else:
        final_link_colors = computed_link_colors

    if node_colors is not None:
        if len(node_colors) != len(nodes_labels):
            raise ValueError("node_colors length must match node count")
        final_colors = list(node_colors)
    else:
        final_colors = question_colors + word_node_colors

    q_ys = _even_ys(n_questions)
    w_ys = _even_ys(len(top_words))
    xs = [0.01] * n_questions + [0.99] * len(top_words)
    ys = q_ys + w_ys

    display_labels = (
        [""] * len(nodes_labels) if hide_native_labels else list(nodes_labels)
    )

    node_kwargs = dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=display_labels,
        customdata=list(nodes_labels),
        hovertemplate="%{customdata}<extra></extra>",
        color=final_colors,
    )
    if pin_node_positions:
        node_kwargs["x"] = xs
        node_kwargs["y"] = ys

    sankey_trace_kwargs = dict(
        node=dict(**node_kwargs),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=final_link_colors,
        ),
    )
    if pin_node_positions:
        sankey_trace_kwargs["arrangement"] = arrangement

    fig = go.Figure(data=[go.Sankey(**sankey_trace_kwargs)])

    fig.update_layout(
        title_text=SANKEY_TITLE,
        font_size=12,
        height=height,
        margin=dict(l=25, r=25, t=50, b=25),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    layout_nodes: List[SankeyNodeLayout] = []
    for i, question in enumerate(questions):
        layout_nodes.append({
            "node_id": node_id_for_question(question),
            "label": question,
            "side": "questions",
            "x": xs[i],
            "y": ys[i],
        })
    for j, word in enumerate(top_words):
        idx = n_questions + j
        layout_nodes.append({
            "node_id": node_id_for_word(word),
            "label": word,
            "side": "words",
            "x": xs[idx],
            "y": ys[idx],
        })

    return {
        "figure": fig,
        "nodes": layout_nodes,
        "questions": list(questions),
        "words": list(top_words),
        "word_totals": dict(word_totals),
    }


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
    result = build_sankey_diagram(
        texts_or_questions,
        n_words=n_words,
        colorscale=colorscale,
        main_node_color=main_node_color,
        opacity=opacity,
        height=height,
        custom_stop_words=custom_stop_words,
        single_question_label=single_question_label,
        hide_native_labels=False,
    )
    return None if result is None else result["figure"]


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
