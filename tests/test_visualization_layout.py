from src.visualization import build_sankey_diagram, create_sankey_diagram


SAMPLE = {
    "Pergunta A": [
        "atendimento rápido e eficiente",
        "atendimento excelente",
        "serviço rápido",
    ],
    "Pergunta B": [
        "produto excelente qualidade",
        "qualidade ótima",
        "serviço bom",
    ],
}


def test_build_sankey_returns_layout_and_shows_native_labels_by_default():
    result = build_sankey_diagram(
        SAMPLE,
        n_words=5,
        node_colors=None,
    )
    assert result is not None
    fig = result["figure"]
    nodes = result["nodes"]
    sankey = fig.data[0]
    assert all(label != "" for label in sankey.node.label)
    assert len(nodes) == len(result["questions"]) + len(result["words"])
    assert all(0.0 <= n["x"] <= 1.0 for n in nodes)
    assert all(0.0 <= n["y"] <= 1.0 for n in nodes)
    q_nodes = [n for n in nodes if n["side"] == "questions"]
    w_nodes = [n for n in nodes if n["side"] == "words"]
    assert all(n["x"] == 0.01 for n in q_nodes)
    assert all(n["x"] == 0.99 for n in w_nodes)
    sankey_x = getattr(sankey.node, "x", None)
    assert sankey_x is None or sankey_x == ()
    assert sankey.arrangement is None


def test_build_sankey_can_pin_node_positions_on_trace():
    result = build_sankey_diagram(SAMPLE, n_words=5, pin_node_positions=True)
    assert result is not None
    sankey = result["figure"].data[0]
    assert list(sankey.node.x)[: len(result["questions"])] == [0.01] * len(
        result["questions"]
    )
    assert sankey.arrangement == "snap"


def test_build_sankey_can_hide_native_labels():
    result = build_sankey_diagram(
        SAMPLE,
        n_words=5,
        hide_native_labels=True,
        node_colors=None,
    )
    assert result is not None
    sankey = result["figure"].data[0]
    assert all(label == "" for label in sankey.node.label)


def test_build_sankey_accepts_explicit_node_colors():
    result = build_sankey_diagram(SAMPLE, n_words=5, hide_native_labels=True)
    assert result is not None
    n = len(result["nodes"])
    custom = ["rgba(1,2,3,0.8)"] * n
    result2 = build_sankey_diagram(
        SAMPLE, n_words=5, hide_native_labels=True, node_colors=custom
    )
    assert list(result2["figure"].data[0].node.color) == custom


def test_create_sankey_diagram_still_returns_figure():
    fig = create_sankey_diagram(SAMPLE, n_words=5)
    assert fig is not None
    assert fig.data[0].type == "sankey"
