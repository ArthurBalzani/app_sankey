"""Shared color string conversions for Plotly/Matplotlib."""

import re

from matplotlib.colors import to_rgba

# Plotly returns rgb(...); matplotlib only accepts rgba(...) or hex/names.
_RGB_RGBA_RE = re.compile(
    r"^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*"
    r"(?:,\s*([0-9.]+)\s*)?\)$",
    re.IGNORECASE,
)


def _channel(value: str) -> str:
    """Format a color channel for Plotly rgba() strings."""
    f = float(value)
    if f <= 1.0 and "." in value:
        return str(int(round(f * 255)))
    if f == int(f):
        return str(int(f))
    return value.strip()


def convert_color_to_hex(color: str) -> str:
    """Normalize hex, rgb(...), rgba(...), or named colors to #RRGGBB for Streamlit."""
    color = str(color).strip()
    if not color:
        raise ValueError("empty color string")

    if color.startswith("#"):
        rgba = to_rgba(color)
        r, g, b = (int(round(c * 255)) for c in rgba[:3])
        return f"#{r:02x}{g:02x}{b:02x}"

    m = _RGB_RGBA_RE.match(color)
    if m:
        r, g, b = (int(_channel(m.group(i))) for i in (1, 2, 3))
        return f"#{r:02x}{g:02x}{b:02x}"

    rgba = to_rgba(color)
    r, g, b = (int(round(c * 255)) for c in rgba[:3])
    return f"#{r:02x}{g:02x}{b:02x}"


def convert_color_to_rgba(color: str, opacity: float) -> str:
    """
    Convert hex, rgb(...), rgba(...), or named colors to rgba(r, g, b, opacity).
    """
    color = str(color).strip()
    if not color:
        raise ValueError("empty color string")

    m = _RGB_RGBA_RE.match(color)
    if m:
        r, g, b = (_channel(m.group(i)) for i in (1, 2, 3))
        return f"rgba({r}, {g}, {b}, {opacity})"

    if color.startswith("#"):
        rgba = to_rgba(color)
        return (
            f"rgba({int(rgba[0] * 255)}, {int(rgba[1] * 255)}, "
            f"{int(rgba[2] * 255)}, {opacity})"
        )

    rgba = to_rgba(color)
    return (
        f"rgba({int(rgba[0] * 255)}, {int(rgba[1] * 255)}, "
        f"{int(rgba[2] * 255)}, {opacity})"
    )
