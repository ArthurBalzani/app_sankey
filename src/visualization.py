"""
Module for creating visualizations, especially Sankey charts.
"""

from typing import List, Optional, Dict, TYPE_CHECKING
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.express as px
from matplotlib.colors import to_rgba
from collections import Counter
import pandas as pd

from config import DEFAULT_OPACITY, DEFAULT_MAIN_NODE_COLOR, SANKEY_TITLE, WORD_COLUMN_NAME, FREQUENCY_COLUMN_NAME
from src.text_processing import extract_words, get_word_frequency

if TYPE_CHECKING:
    pass


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


def create_sankey_diagram(texts: List[str],
                         n_words: int = 20,
                         colorscale: Optional[List[str]] = None,
                         main_node_color: str = DEFAULT_MAIN_NODE_COLOR,
                         opacity: float = DEFAULT_OPACITY,
                         height: int = 600,
                         custom_stop_words: Optional[set] = None) -> Optional[go.Figure]:
    """
    Creates a Sankey chart showing word frequency.
    
    Args:
        texts: List of texts to analyze.
        n_words: Number of most frequent words to show.
        colorscale: Color palette (list of hex colors or valid name).
        main_node_color: Color of the main node (source).
        opacity: Opacity of connections (0-1).
        height: Height of the chart in pixels.
        custom_stop_words: Set of custom words to filter.
        
    Returns:
        Plotly Figure or None if there are no significant words.
    """
    # Get word frequency
    word_freq = get_word_frequency(texts, n_words, custom_stop_words)
    
    if not word_freq:
        return None
    
    # Prepare data for Sankey
    nodes_labels = ["Pergunta"] + list(word_freq.keys())
    
    source = []
    target = []
    value = []
    
    # Connections from "Question" node to each word
    for i, (word, freq) in enumerate(word_freq.items(), 1):
        source.append(0)  # Index of "Question" node
        target.append(i)
        value.append(freq)
    
    # Use default palette if not specified
    if colorscale is None:
        colorscale = pc.sequential.Viridis
    
    # Generate colors for connections
    freq_values = list(word_freq.values())
    max_freq = max(freq_values) if freq_values else 1
    
    colors = []
    node_colors = []
    
    # Convert main node color to rgba
    main_node_rgba = _convert_color_to_rgba(main_node_color, opacity)
    
    # Generate colors for each word
    for word, freq in word_freq.items():
        normalized_freq = freq / max_freq
        color_base = pc.sample_colorscale(colorscale, normalized_freq)[0]
        
        # Ensure color_base is a string
        if isinstance(color_base, tuple):
            r, g, b = [int(c * 255) for c in color_base[:3]]
            color_base = f"rgb({r}, {g}, {b})"
        
        color_rgba = _convert_color_to_rgba(str(color_base), opacity)
        colors.append(color_rgba)
        node_colors.append(color_rgba)
    
    # Create Sankey figure
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes_labels,
            color=[main_node_rgba] + node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=colors
        )
    )])
    
    fig.update_layout(
        title_text=SANKEY_TITLE,
        font_size=12,
        height=height,
        margin=dict(l=25, r=25, t=50, b=25),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_word_frequency_dataframe(texts: List[str],
                                    n_words: int = 20,
                                    custom_stop_words: Optional[set] = None) -> 'pd.DataFrame':
    """
    Creates a DataFrame with word frequency.
    
    Args:
        texts: List of texts to analyze.
        n_words: Number of words to display.
        custom_stop_words: Set of custom words to filter.
        
    Returns:
        DataFrame with columns ['Word', 'Frequency'].
    """
    word_freq = get_word_frequency(texts, n_words, custom_stop_words)
    
    if not word_freq:
        return pd.DataFrame(columns=[WORD_COLUMN_NAME, FREQUENCY_COLUMN_NAME])
    
    return pd.DataFrame(
        list(word_freq.items()),
        columns=[WORD_COLUMN_NAME, FREQUENCY_COLUMN_NAME]
    )
