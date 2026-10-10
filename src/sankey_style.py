"""Session style model for Sankey native labels and node colors."""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Literal, Optional, Sequence, TypedDict

from src.color_utils import convert_color_to_hex, convert_color_to_rgba

import config

SideName = Literal["questions", "words"]


class StyleFields(TypedDict):
    font: str
    size: int
    color: str


def node_id_for_question(label: str) -> str:
    return f"q:{label}"


def node_id_for_word(label: str) -> str:
    return f"w:{label}"


def parse_node_id(node_id: str) -> tuple[SideName, str]:
    if node_id.startswith("q:"):
        return "questions", node_id[2:]
    if node_id.startswith("w:"):
        return "words", node_id[2:]
    raise ValueError(f"Invalid node_id: {node_id}")


def make_content_key(
    *,
    file_names: Sequence[str],
    selected_question_ids: Sequence[str],
    n_words: int,
    stopwords: Sequence[str],
) -> str:
    payload = {
        "files": sorted(file_names),
        "questions": list(selected_question_ids),
        "n_words": int(n_words),
        "stopwords": sorted(stopwords),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _side_defaults() -> Dict[SideName, StyleFields]:
    return {
        "questions": {
            "font": config.DEFAULT_QUESTION_FONT,
            "size": config.DEFAULT_QUESTION_FONT_SIZE,
            "color": config.DEFAULT_QUESTION_LABEL_COLOR,
        },
        "words": {
            "font": config.DEFAULT_WORD_FONT,
            "size": config.DEFAULT_WORD_FONT_SIZE,
            "color": config.DEFAULT_WORD_LABEL_COLOR,
        },
    }


def default_style_state(content_key: str = "") -> dict:
    return {
        "content_key": content_key,
        "defaults": _side_defaults(),
        "question_node_color": config.DEFAULT_QUESTION_NODE_COLOR,
        "question_node_colors": {},  # question label -> fill color (optional per question)
    }


def _normalize_legacy_state(state: dict) -> dict:
    """Fill missing keys when reusing session state from older schema versions."""
    if "question_node_color" not in state:
        state["question_node_color"] = config.DEFAULT_QUESTION_NODE_COLOR
    if "question_node_colors" not in state:
        state["question_node_colors"] = {}
    state.pop("use_palette", None)
    state.pop("word_node_color", None)
    state.pop("overrides", None)
    state.pop("offsets", None)
    _sync_unified_label_typography(state)
    return state


def _sync_unified_label_typography(state: dict) -> None:
    """Plotly Sankey labels share one font/size; keep both sides in sync."""
    q = state["defaults"]["questions"]
    w = state["defaults"]["words"]
    font = q["font"]
    size = int(q["size"])
    color = q["color"]
    for side in ("questions", "words"):
        state["defaults"][side]["font"] = font
        state["defaults"][side]["size"] = size
        state["defaults"][side]["color"] = color


def ensure_style_state(state: Optional[dict], content_key: str) -> dict:
    if not state or state.get("content_key") != content_key:
        return default_style_state(content_key)
    return _normalize_legacy_state(state)


def reset_style_customizations(state: dict) -> dict:
    key = state.get("content_key", "")
    return default_style_state(key)


def resolve_label_style(state: dict, node_id: str) -> StyleFields:
    side, _ = parse_node_id(node_id)
    base = state["defaults"][side]
    return StyleFields(
        font=base["font"],
        size=int(base["size"]),
        color=base["color"],
    )


def _to_rgba(color: str, opacity: float) -> str:
    return convert_color_to_rgba(color, opacity)


def _sample_colorscale_rgb(palette_colors: Sequence[str], position: float) -> str:
    import plotly.colors as pc

    sampled = pc.sample_colorscale(list(palette_colors), position)[0]
    if isinstance(sampled, tuple):
        r, g, b = [int(c * 255) for c in sampled[:3]]
        return f"rgb({r}, {g}, {b})"
    return str(sampled)


def default_question_color_for_index(
    index: int,
    count: int,
    palette_colors: Sequence[str],
) -> str:
    """Default fill/link color when the user has not picked one yet (#RRGGBB)."""
    import plotly.colors as pc

    if count <= 1:
        return config.DEFAULT_QUESTION_NODE_COLOR
    pos = index / max(count - 1, 1)
    sampled = pc.sample_colorscale(list(palette_colors), pos)[0]
    if isinstance(sampled, tuple):
        r, g, b = [int(c * 255) for c in sampled[:3]]
        return convert_color_to_hex(f"rgb({r}, {g}, {b})")
    return convert_color_to_hex(str(sampled))


def question_color_hex(
    state: dict, question_label: str, *, n_questions: int
) -> str:
    """Fill and link color for one question (per-question map only when n >= 2)."""
    if n_questions >= 2:
        per = state.get("question_node_colors") or {}
        if question_label in per:
            return str(per[question_label])
    return str(
        state.get("question_node_color", config.DEFAULT_QUESTION_NODE_COLOR)
    )


def _question_node_fill(
    state: dict, question_label: str, opacity: float, n_questions: int
) -> str:
    return _to_rgba(
        question_color_hex(state, question_label, n_questions=n_questions), opacity
    )


def resolve_plotly_link_colors(
    *,
    state: dict,
    question_labels: Sequence[str],
    link_sources: Sequence[int],
    opacity: float,
    link_targets: Optional[Sequence[int]] = None,
    word_labels: Optional[Sequence[str]] = None,
    palette_colors: Optional[Sequence[str]] = None,
    word_totals: Optional[Dict[str, int]] = None,
) -> List[str]:
    """Ribbon colors: per-question fill when n>=2; frequency palette when n==1."""
    n_q = len(question_labels)
    if n_q == 1 and link_targets is not None and word_labels is not None and palette_colors:
        totals = word_totals or {}
        max_total = max(totals.values()) if totals else 1
        out: List[str] = []
        for t_idx in link_targets:
            word = word_labels[int(t_idx) - n_q]
            normalized = totals.get(word, 0) / max_total
            base = _sample_colorscale_rgb(palette_colors, normalized)
            out.append(_to_rgba(base, opacity))
        return out

    out: List[str] = []
    for q_idx in link_sources:
        label = question_labels[int(q_idx)]
        out.append(_question_node_fill(state, label, opacity, n_q))
    return out


def resolve_plotly_node_colors(
    *,
    state: dict,
    question_labels: Sequence[str],
    word_labels: Sequence[str],
    palette_colors: Sequence[str],
    opacity: float,
    main_node_color: Optional[str] = None,
    word_totals: Optional[Dict[str, int]] = None,
) -> List[str]:
    """Colors for Plotly node rectangles (questions then words)."""
    n_w = len(word_labels)
    colors: List[str] = []

    n_q = len(question_labels)
    for label in question_labels:
        colors.append(_question_node_fill(state, label, opacity, n_q))

    totals = word_totals or {}
    max_total = max(totals.values()) if totals else 1
    for i, word in enumerate(word_labels):
        if n_q == 1 and totals:
            pos = totals.get(word, 0) / max_total
        else:
            pos = i / max(n_w - 1, 1) if n_w > 1 else 0.0
        sampled = _sample_colorscale_rgb(palette_colors, pos)
        colors.append(_to_rgba(sampled, opacity))
    return colors


def needs_pinned_node_positions(state: dict) -> bool:
    """v1 always uses Plotly native node.label placement (no typography annotations)."""
    return False


def unified_label_typography(state: dict) -> StyleFields:
    """Single font/size/color for all Sankey node labels (Plotly native limit)."""
    q_def = state["defaults"]["questions"]
    w_def = state["defaults"]["words"]
    color = (
        q_def["color"]
        if q_def["color"] == w_def["color"]
        else "#333333"
    )
    return StyleFields(
        font=q_def["font"],
        size=int(q_def["size"]),
        color=color,
    )


def apply_native_label_styles(
    fig,
    nodes: Sequence[dict],
    state: dict,
) -> None:
    """Apply label typography via Plotly native node.label + layout font (v1)."""
    if not nodes or not fig.data:
        return

    sankey = fig.data[0]
    labels = list(sankey.node.label)
    custom = list(sankey.node.customdata or [])
    typo = unified_label_typography(state)

    if custom and all(not lab for lab in labels):
        sankey.node.label = list(custom)

    fig.update_layout(
        font=dict(
            family=typo["font"],
            size=int(typo["size"]),
            color=typo["color"],
        ),
        margin=dict(l=25, r=25, t=50, b=25),
        annotations=[],
    )
