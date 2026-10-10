import config
from src.sankey_style import (
    apply_native_label_styles,
    default_style_state,
    ensure_style_state,
    make_content_key,
    needs_pinned_node_positions,
    node_id_for_question,
    node_id_for_word,
    parse_node_id,
    reset_style_customizations,
    resolve_label_style,
    resolve_plotly_node_colors,
    resolve_plotly_link_colors,
    default_question_color_for_index,
)
from src.visualization import build_sankey_diagram


def test_sankey_font_config_exists():
    assert "Arial" in config.SANKEY_FONT_FAMILIES
    assert "Georgia" in config.SANKEY_FONT_FAMILIES
    assert config.DEFAULT_QUESTION_FONT in config.SANKEY_FONT_FAMILIES
    assert config.DEFAULT_WORD_FONT in config.SANKEY_FONT_FAMILIES
    assert isinstance(config.DEFAULT_QUESTION_FONT_SIZE, int)
    assert isinstance(config.DEFAULT_WORD_FONT_SIZE, int)
    assert config.DEFAULT_QUESTION_LABEL_COLOR.startswith("#")
    assert config.DEFAULT_WORD_LABEL_COLOR.startswith("#")
    assert config.DEFAULT_QUESTION_NODE_COLOR.startswith("#")


def test_node_ids_are_stable_and_sided():
    assert node_id_for_question("Atendimento") == "q:Atendimento"
    assert node_id_for_word("rápido") == "w:rápido"
    assert parse_node_id("q:Atendimento") == ("questions", "Atendimento")
    assert parse_node_id("w:rápido") == ("words", "rápido")


def test_make_content_key_stable_for_same_multiset():
    a = make_content_key(
        file_names=["b.csv", "a.csv"],
        selected_question_ids=["x"],
        n_words=20,
        stopwords=["z", "a"],
    )
    b = make_content_key(
        file_names=["a.csv", "b.csv"],
        selected_question_ids=["x"],
        n_words=20,
        stopwords=["a", "z"],
    )
    assert a == b


def test_content_key_changes_with_inputs():
    base = make_content_key(
        file_names=["a.csv"],
        selected_question_ids=["col1"],
        n_words=20,
        stopwords=[],
    )
    other_n = make_content_key(
        file_names=["a.csv"],
        selected_question_ids=["col1"],
        n_words=10,
        stopwords=[],
    )
    other_stop = make_content_key(
        file_names=["a.csv"],
        selected_question_ids=["col1"],
        n_words=20,
        stopwords=["foo"],
    )
    assert base != other_n
    assert base != other_stop
    assert len(base) == 16


def test_ensure_style_state_resets_on_content_key_change():
    key_a = make_content_key(
        file_names=["a.csv"],
        selected_question_ids=["q1"],
        n_words=20,
        stopwords=[],
    )
    key_b = make_content_key(
        file_names=["a.csv"],
        selected_question_ids=["q2"],
        n_words=20,
        stopwords=[],
    )
    state = ensure_style_state(None, key_a)
    state["question_node_color"] = "#ff0000"
    state = ensure_style_state(state, key_b)
    assert state["content_key"] == key_b
    assert state["question_node_color"] == config.DEFAULT_QUESTION_NODE_COLOR


def test_resolve_label_style_uses_side_defaults():
    state = default_style_state()
    state["defaults"]["questions"]["color"] = "#111111"
    state["defaults"]["questions"]["size"] = 14
    nid = node_id_for_question("P1")
    style = resolve_label_style(state, nid)
    assert style["font"] == state["defaults"]["questions"]["font"]
    assert style["size"] == 14
    assert style["color"] == "#111111"


def test_reset_style_customizations_restores_defaults():
    state = default_style_state()
    state["defaults"]["words"]["size"] = 99
    state["question_node_colors"]["x"] = "#010101"
    cleared = reset_style_customizations(state)
    assert cleared["defaults"]["words"]["size"] == config.DEFAULT_WORD_FONT_SIZE
    assert cleared["question_node_colors"] == {}


def test_resolve_plotly_node_colors_word_nodes_use_palette():
    state = default_style_state()
    state["question_node_color"] = "#010101"
    colors = resolve_plotly_node_colors(
        state=state,
        question_labels=["Q1"],
        word_labels=["alpha", "beta"],
        palette_colors=["#000000", "#ffffff"],
        opacity=0.8,
        word_totals={"alpha": 2, "beta": 1},
    )
    assert len(colors) == 3
    assert "1, 1, 1" in colors[0].replace(" ", "") or "1,1,1" in colors[0].replace(
        " ", ""
    )
    assert colors[1] != colors[2]


def test_all_question_nodes_share_fill_color_when_multiple_questions():
    state = default_style_state()
    state["question_node_color"] = "#aa0000"
    colors = resolve_plotly_node_colors(
        state=state,
        question_labels=["Q1", "Q2", "Q3"],
        word_labels=["w"],
        palette_colors=["#000000", "#ffffff"],
        opacity=1.0,
    )
    q_colors = colors[:3]
    assert all(c == q_colors[0] for c in q_colors)
    assert "170, 0, 0" in q_colors[0].replace(" ", "") or "170,0,0" in q_colors[
        0
    ].replace(" ", "")


def test_single_question_link_colors_differ_from_question_when_palette_on():
    sample = {"Q1": ["alfa alfa alfa beta beta gamma"]}
    state = default_style_state()
    state["question_node_color"] = "#0000ff"
    draft = build_sankey_diagram(sample, n_words=3)
    assert draft is not None
    trace = draft["figure"].data[0]
    links = resolve_plotly_link_colors(
        state=state,
        question_labels=draft["questions"],
        link_sources=list(trace.link.source),
        link_targets=list(trace.link.target),
        word_labels=draft["words"],
        palette_colors=["#000000", "#ffffff"],
        word_totals=draft["word_totals"],
        opacity=0.8,
    )
    from src.sankey_style import question_color_hex
    from src.color_utils import convert_color_to_rgba

    q_rgba = convert_color_to_rgba(
        question_color_hex(state, "Q1", n_questions=1), 0.8
    )
    assert len(links) >= 2
    assert not all(link == q_rgba for link in links)
    assert len(set(links)) >= 2


def test_resolve_plotly_link_colors_match_question_fill():
    state = default_style_state()
    state["question_node_colors"] = {"Q1": "#ff0000", "Q2": "#0000ff"}
    links = resolve_plotly_link_colors(
        state=state,
        question_labels=["Q1", "Q2"],
        link_sources=[0, 0, 1],
        opacity=0.5,
    )
    assert len(links) == 3
    assert links[0] == links[1]
    assert links[0] != links[2]
    assert "255, 0, 0" in links[0].replace(" ", "") or "255,0,0" in links[
        0
    ].replace(" ", "")
    assert "0, 0, 255" in links[2].replace(" ", "") or "0,0,255" in links[
        2
    ].replace(" ", "")


def test_build_sankey_accepts_custom_link_colors():
    sample = {"Q1": ["alfa beta"], "Q2": ["alfa gama"]}
    draft = build_sankey_diagram(sample, n_words=3)
    assert draft is not None
    trace = draft["figure"].data[0]
    custom = ["rgba(1,2,3,0.8)"] * len(trace.link.source)
    result = build_sankey_diagram(sample, n_words=3, link_colors=custom)
    assert list(result["figure"].data[0].link.color) == custom


def test_single_question_ignores_stale_per_question_colors():
    state = default_style_state()
    state["question_node_color"] = "#00ff00"
    state["question_node_colors"] = {"Q1": "#ff0000"}
    colors = resolve_plotly_node_colors(
        state=state,
        question_labels=["Q1"],
        word_labels=[],
        palette_colors=["#000000", "#ffffff"],
        opacity=1.0,
    )
    assert len(colors) == 1
    assert "0, 255, 0" in colors[0].replace(" ", "") or "0,255,0" in colors[
        0
    ].replace(" ", "")


def test_per_question_node_colors_override_shared_fill():
    state = default_style_state()
    state["question_node_color"] = "#000000"
    state["question_node_colors"] = {"Q2": "#ffffff"}
    colors = resolve_plotly_node_colors(
        state=state,
        question_labels=["Q1", "Q2"],
        word_labels=[],
        palette_colors=["#000000", "#ffffff"],
        opacity=1.0,
    )
    assert len(colors) == 2
    assert colors[0] != colors[1]


def test_apply_native_label_styles_unified_typography_keeps_native_labels():
    sample = {"Q": ["alfa beta gamma"]}
    result = build_sankey_diagram(sample, n_words=3)
    assert result is not None
    state = default_style_state()
    state["defaults"]["words"] = dict(state["defaults"]["questions"])
    apply_native_label_styles(result["figure"], result["nodes"], state)
    sankey = result["figure"].data[0]
    assert any(lab != "" for lab in sankey.node.label)
    assert not result["figure"].layout.annotations


def test_default_style_uses_native_labels_not_annotations():
    sample = {"Pergunta longa sobre trabalho?": ["bom trabalho"]}
    state = default_style_state()
    assert not needs_pinned_node_positions(state)
    result = build_sankey_diagram(sample, n_words=3, pin_node_positions=False)
    apply_native_label_styles(result["figure"], result["nodes"], state)
    assert not result["figure"].layout.annotations
    assert result["figure"].layout.margin.l == 25
    assert any(lab != "" for lab in result["figure"].data[0].node.label)


def test_mismatched_font_sizes_still_use_native_labels_after_normalize():
    sample = {"Q": ["alfa beta"]}
    state = default_style_state()
    state["defaults"]["words"]["size"] = 18
    assert not needs_pinned_node_positions(state)
    state = ensure_style_state(state, state["content_key"])
    assert state["defaults"]["words"]["size"] == state["defaults"]["questions"]["size"]
    result = build_sankey_diagram(sample, n_words=3, pin_node_positions=False)
    apply_native_label_styles(result["figure"], result["nodes"], state)
    assert not result["figure"].layout.annotations
    assert any(lab != "" for lab in result["figure"].data[0].node.label)
    assert result["figure"].layout.font.size == int(state["defaults"]["questions"]["size"])


def test_font_size_11_uses_native_labels_not_annotations():
    sample = {"Pergunta?": ["palavra teste"]}
    state = default_style_state()
    state["defaults"]["questions"]["size"] = 11
    state["defaults"]["words"]["size"] = 11
    result = build_sankey_diagram(sample, n_words=3)
    apply_native_label_styles(result["figure"], result["nodes"], state)
    assert not result["figure"].layout.annotations
    assert result["figure"].layout.font.size == 11


def test_default_question_color_for_index_is_hex_for_streamlit_picker():
    from src.visualization import get_color_palette

    palette = get_color_palette("Viridis", invert=False)
    for i in range(3):
        color = default_question_color_for_index(i, 3, palette)
        assert color.startswith("#"), color
        assert len(color) == 7
