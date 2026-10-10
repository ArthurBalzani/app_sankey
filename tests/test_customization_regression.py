"""Regression coverage for Sankey / table customization (no browser E2E)."""

import re

import pandas as pd
import pytest

import config
from src.color_utils import convert_color_to_hex
from src.sankey_style import (
    apply_native_label_styles,
    default_style_state,
    default_question_color_for_index,
    ensure_style_state,
    make_content_key,
    question_color_hex,
    resolve_plotly_link_colors,
    resolve_plotly_node_colors,
)
from src.table_display import expanded_dataframe_display
from src.visualization import build_sankey_diagram, get_color_palette

_HEX6 = re.compile(r"^#[0-9A-Fa-f]{6}$")


def test_single_question_node_uses_picker_hex_links_palette():
    state = default_style_state()
    state["question_node_color"] = "#ABCDEF"
    sample = {"Q1": ["alfa alfa beta beta gamma"]}
    draft = build_sankey_diagram(sample, n_words=3)
    trace = draft["figure"].data[0]
    palette = ["#000000", "#ffffff"]
    nodes = resolve_plotly_node_colors(
        state=state,
        question_labels=draft["questions"],
        word_labels=draft["words"],
        palette_colors=palette,
        opacity=0.8,
        word_totals=draft["word_totals"],
    )
    links = resolve_plotly_link_colors(
        state=state,
        question_labels=draft["questions"],
        link_sources=list(trace.link.source),
        link_targets=list(trace.link.target),
        word_labels=draft["words"],
        palette_colors=palette,
        word_totals=draft["word_totals"],
        opacity=0.8,
    )
    assert question_color_hex(state, "Q1", n_questions=1) == "#ABCDEF"
    assert "171, 205, 239" in nodes[0].replace(" ", "") or "171,205,239" in nodes[
        0
    ].replace(" ", "")
    q_fill = nodes[0]
    assert len(links) >= 2
    assert not all(link == q_fill for link in links)
    assert len(set(links)) >= 2


def test_multi_question_links_match_per_question_node_fills():
    state = default_style_state()
    state["question_node_colors"] = {"Q1": "#ff0000", "Q2": "#0000ff"}
    labels = ["Q1", "Q2"]
    nodes = resolve_plotly_node_colors(
        state=state,
        question_labels=labels,
        word_labels=["shared"],
        palette_colors=["#111111", "#eeeeee"],
        opacity=0.6,
    )
    links = resolve_plotly_link_colors(
        state=state,
        question_labels=labels,
        link_sources=[0, 1, 0],
        opacity=0.6,
    )
    assert links[0] == nodes[0]
    assert links[1] == nodes[1]
    assert links[2] == nodes[0]
    assert links[0] != links[1]


def test_multi_question_palette_defaults_never_rgb_strings():
    palette = get_color_palette(config.DEFAULT_COLOR_PALETTE, invert=False)
    for count in (2, 3, 5):
        for i in range(count):
            color = default_question_color_for_index(i, count, palette)
            assert _HEX6.match(color), color
            assert not color.lower().startswith("rgb")


def test_convert_color_to_hex_plotly_rgb_is_streamlit_safe():
    assert convert_color_to_hex("rgb(68, 1, 84)") == "#440154"
    assert _HEX6.match(convert_color_to_hex("rgb(68,1,84)"))


def test_native_labels_apply_unified_font_and_size():
    sample = {"Pergunta?": ["texto exemplo"]}
    result = build_sankey_diagram(sample, n_words=3)
    state = default_style_state()
    state["defaults"]["questions"]["font"] = "Georgia"
    state["defaults"]["questions"]["size"] = 16
    state["defaults"]["words"]["size"] = 12
    state = ensure_style_state(state, state["content_key"])
    apply_native_label_styles(result["figure"], result["nodes"], state)
    assert not result["figure"].layout.annotations
    assert result["figure"].layout.font.family == "Georgia"
    assert result["figure"].layout.font.size == 16


def test_content_key_change_clears_question_node_color_maps():
    key_a = make_content_key(
        file_names=["a.csv"],
        selected_question_ids=["q1"],
        n_words=20,
        stopwords=[],
    )
    key_b = make_content_key(
        file_names=["a.csv"],
        selected_question_ids=["q1", "q2"],
        n_words=20,
        stopwords=[],
    )
    state = ensure_style_state(None, key_a)
    state["question_node_color"] = "#ff00ff"
    state["question_node_colors"] = {"Q1": "#010101", "Q2": "#020202"}
    state = ensure_style_state(state, key_b)
    assert state["content_key"] == key_b
    assert state["question_node_color"] == config.DEFAULT_QUESTION_NODE_COLOR
    assert state["question_node_colors"] == {}


def test_expanded_display_styler_when_jinja2_available():
    from pandas.compat._optional import import_optional_dependency

    if not import_optional_dependency("jinja2", errors="ignore"):
        pytest.skip("pandas Styler needs jinja2>=3.1.6")
    df = pd.DataFrame({"col": [1, 2]})
    out = expanded_dataframe_display(df, has_jinja2=True)
    assert out.__class__.__name__ == "Styler"
    html = out.to_html()
    assert "pre-wrap" in html
    assert "word-break" in html


def test_expanded_display_plain_dataframe_without_jinja2():
    df = pd.DataFrame({"col": [1]})
    out = expanded_dataframe_display(df, has_jinja2=False)
    assert out is df


def test_sankey_color_wiring_lengths_and_trace_application():
    sample = {"Q1": ["alfa beta"], "Q2": ["alfa gama"]}
    draft = build_sankey_diagram(sample, n_words=3)
    trace = draft["figure"].data[0]
    state = default_style_state()
    state["question_node_colors"] = {"Q1": "#aa0000", "Q2": "#0000aa"}
    palette = get_color_palette("Viridis", invert=False)
    opacity = 0.7
    node_colors = resolve_plotly_node_colors(
        state=state,
        question_labels=draft["questions"],
        word_labels=draft["words"],
        palette_colors=palette,
        opacity=opacity,
        word_totals=draft["word_totals"],
    )
    link_colors = resolve_plotly_link_colors(
        state=state,
        question_labels=draft["questions"],
        link_sources=list(trace.link.source),
        link_targets=list(trace.link.target),
        word_labels=draft["words"],
        palette_colors=palette,
        word_totals=draft["word_totals"],
        opacity=opacity,
    )
    n_nodes = len(trace.node.label)
    n_links = len(trace.link.source)
    assert len(node_colors) == n_nodes
    assert len(link_colors) == n_links
    built = build_sankey_diagram(
        sample,
        n_words=3,
        node_colors=node_colors,
        link_colors=link_colors,
    )
    applied = built["figure"].data[0]
    assert list(applied.node.color) == node_colors
    assert list(applied.link.color) == link_colors
