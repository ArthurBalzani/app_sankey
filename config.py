"""
Centralized application configuration.
"""

# Streamlit Page Configuration
PAGE_TITLE = "Análise de Frequência de Palavras"
PAGE_LAYOUT = "wide"
SANKEY_TITLE = "Frequência de Palavras - Diagrama Sankey"
WORD_COLUMN_NAME = "Palavra"
FREQUENCY_COLUMN_NAME = "Frequência"

# Text Processing
MIN_WORD_LENGTH = 3
DEFAULT_ENCODING = "utf-8"
DEFAULT_DELIMITER = ";"
SUPPORTED_ENCODINGS = ["utf-8", "latin1", "ISO-8859-1", "cp1252"]

# Portuguese stopwords
ADDITIONAL_STOP_WORDS = {
    'pra', 'pro', 'sobre', 'assim', 'então', 'porque',
    'muito', 'muita', 'muitos', 'muitas', 'bem', 'mal',
    'sim', 'não', 'pelo', 'pela', 'pelos', 'pelas'
}

# Sankey Chart Configuration
DEFAULT_N_WORDS = 20
DEFAULT_OPACITY = 0.8
DEFAULT_CHART_HEIGHT = 600
DEFAULT_MAIN_NODE_COLOR = "#1f77b4"
MIN_N_WORDS = 5
MAX_N_WORDS = 50
MIN_CHART_HEIGHT = 400
MAX_CHART_HEIGHT = 1000
SLIDER_HEIGHT_STEP = 50

# Available color palettes
COLOR_PALETTES = [
    "Viridis", "Plasma", "Inferno", "Magma", "Cividis",
    "Rainbow", "Jet", "Turbo", "Blues", "Greens", "Reds",
    "YlOrRd", "YlGnBu", "PuRd", "RdPu", "Spectral", "RdYlBu"
]
DEFAULT_COLOR_PALETTE = "Viridis"

# CSV related
IGNORED_COLUMNS = 2  # First 2 columns are ignored
CSV_ALLOWED_TYPES = ['csv']

# Paths
DATA_DIR = "data"
EXAMPLE_CSV_FILENAME = "modelo_csv.csv"
