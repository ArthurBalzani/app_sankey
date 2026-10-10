"""Table preview helpers (no Streamlit dependency)."""

from __future__ import annotations

import pandas as pd

EXPANDED_TABLE_CSS = """
<style>
.sankey-expanded-wrap {
  overflow-x: auto;
  max-width: 100%;
}
.sankey-expanded-wrap table.sankey-expanded-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
}
.sankey-expanded-wrap table.sankey-expanded-table td,
.sankey-expanded-wrap table.sankey-expanded-table th {
  white-space: pre-wrap !important;
  word-break: break-word;
  vertical-align: top;
  line-height: 1.55;
  padding: 12px 16px !important;
  max-width: 28rem;
}
.sankey-expanded-wrap table.sankey-expanded-table th {
  font-weight: 600;
}
</style>
"""


def expanded_dataframe_display(
    df: pd.DataFrame, *, has_jinja2: bool
) -> pd.DataFrame | "pd.io.formats.style.Styler":
    """Expandido mode: wrapped cells and roomy rows when jinja2 is available."""
    if not has_jinja2:
        return df

    cell_props = {
        "text-align": "left",
        "white-space": "pre-wrap",
        "word-break": "break-word",
        "vertical-align": "top",
        "padding": "12px 16px",
        "line-height": "1.55",
        "max-width": "28rem",
    }
    return (
        df.style.set_properties(subset=None, **cell_props)
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("white-space", "pre-wrap"),
                        ("word-break", "break-word"),
                        ("padding", "12px 16px"),
                        ("vertical-align", "top"),
                    ],
                },
            ],
            overwrite=False,
        )
    )


def expanded_dataframe_html(styler: "pd.io.formats.style.Styler") -> str:
    """HTML fragment for Streamlit markdown (Expandido preview)."""
    return styler.to_html(
        classes="sankey-expanded-table",
        table_uuid="sankey-expanded-preview",
    )
