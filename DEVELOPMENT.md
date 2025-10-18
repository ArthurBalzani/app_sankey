# 📚 Development Guide

This document describes how to extend and maintain the application.

## 🏗️ Architecture

The application follows a layered architecture:

```
app.py (Streamlit UI)
    ↓
config.py (Configuration)
    ↓
src/text_processing.py (Processing logic)
src/visualization.py (Visualization logic)
```

## 🔄 Data Flow

1. **Input**: CSV file uploaded by user
2. **Validation**: Reading with error handling
3. **Processing**: Word extraction and normalization
4. **Analysis**: Frequency calculation
5. **Visualization**: Sankey chart generation
6. **Output**: Display on interface

## 🧹 Code Patterns

### Add New Color Palettes

In `config.py`, add to the `COLOR_PALETTES` list:

```python
COLOR_PALETTES = [
    # ... existing
    "MyPalette"
]
```

In `src/visualization.py`, add to `get_color_palette()`:

```python
def get_color_palette(palette_name: str, invert: bool = False) -> List[str]:
    palettes = {
        # ... existing
        "MyPalette": pc.sequential.MyName,
    }
```

### Add New Stopwords

In `config.py`:

```python
ADDITIONAL_STOP_WORDS.add("my_word")
```

### Extend Text Processing

In `src/text_processing.py`, create new functions:

```python
def my_new_function(text: str) -> str:
    """
    Clear description.
    
    Args:
        text: Text to process.
        
    Returns:
        Processed result.
    """
    pass
```

Import in `src/__init__.py`:

```python
from src.text_processing import my_new_function

__all__ = [
    # ... existing
    'my_new_function'
]
```

## 🧪 Tests

To add tests, create files in `tests/`:

```python
# tests/test_text_processing.py
import pytest
from src.text_processing import extract_words

def test_extract_words():
    result = extract_words("hello world")
    assert isinstance(result, list)
    assert len(result) > 0
```

Run tests:

```bash
pytest tests/
```

## 📊 Add New Charts

In `src/visualization.py`:

```python
def create_new_chart(texts: List[str]) -> go.Figure:
    """Description of new chart."""
    fig = go.Figure()
    # ... logic
    return fig
```

Use in `app.py`:

```python
from src.visualization import create_new_chart

if st.button("Generate New Chart"):
    fig = create_new_chart(texts)
    st.plotly_chart(fig, use_container_width=True)
```

## 🚀 Deployment

The application is ready for deployment on:

- **Streamlit Cloud**: Connect GitHub repo
- **Heroku**: Use `runtime.txt` for Python version
- **Docker**: Create Dockerfile

### Streamlit Cloud

1. Connect GitHub repository
2. Set main file as `app.py`
3. Automatic deployment on push

### Heroku

```bash
git push heroku main
```

## 🐛 Debugging

Use `st.write()` for quick debug:

```python
st.write("Variable:", variable)
```

For more detailed debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

## 📈 Performance

### Implemented Optimizations

1. **Caching with `@st.cache_data`**: Avoids reprocessing
2. **Batch processing**: Words processed at once
3. **Lazy loading**: Data loaded on demand

### Future Improvements

- [ ] Parallel processing with multiprocessing
- [ ] Database caching
- [ ] Large CSV file compression
- [ ] Sentiment analysis
- [ ] High-resolution chart export

## 📋 Checklist for New Features

- [ ] Function or class with complete docstring
- [ ] Type hints for all parameters
- [ ] Appropriate exception handling
- [ ] Corresponding unit test
- [ ] Updated documentation in README.md
- [ ] Example usage in app.py if applicable
- [ ] Added to `src/__init__.py` if it's a module

## 🔒 Security

Security considerations:

1. **Input Validation**: Always validate CSV
2. **Encoding**: Use explicit encoding
3. **File Size**: Limit maximum size
4. **Code Injection**: Use safe string interpolation

## 📞 Support

For issues, check:

1. Requirements installed: `pip install -r requirements.txt`
2. Python version: 3.8+
3. Valid CSV file: Check delimiter
4. Streamlit logs: `streamlit logs` for debugging
