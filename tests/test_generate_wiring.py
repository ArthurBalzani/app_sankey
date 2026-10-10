from src.sankey_style import (
    apply_native_label_styles,
    default_style_state,
    resolve_plotly_node_colors,
)
from src.visualization import build_sankey_diagram


def test_generate_pipeline_shows_native_labels_and_applies_colors():
    sample = {"Q": ["palavra alfa beta", "palavra alfa gama"]}
    state = default_style_state("k")
    result = build_sankey_diagram(sample, n_words=5)
    assert result is not None
    colors = resolve_plotly_node_colors(
        state=state,
        question_labels=result["questions"],
        word_labels=result["words"],
        palette_colors=["#000000", "#ffffff"],
        opacity=0.8,
    )
    result2 = build_sankey_diagram(sample, n_words=5, node_colors=colors)
    assert result2 is not None
    labels = list(result2["figure"].data[0].node.label)
    assert any(lab != "" for lab in labels)
    apply_native_label_styles(result2["figure"], result2["nodes"], state)
    assert result2["figure"].layout.font.size is not None
