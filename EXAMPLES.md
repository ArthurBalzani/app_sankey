# 💡 Code Examples

## Using the main application

### 1. Run the Streamlit application

```bash
streamlit run app.py
```

Access at `http://localhost:8501`

### 2. Upload a CSV

```csv
id;date;Question 1;Question 2
1;2025-01-01;Great service;Very good
2;2025-01-02;Good service;Could improve
3;2025-01-03;Excellent;Excellent
```

### 3. Select options

- Choose the column for analysis
- Adjust number of words (5-50)
- Select color palette
- Click "Generate Sankey Chart"

## Using the modules in your code

### Example 1: Extract Words

```python
from src.text_processing import extract_words

text = "This is a sample text for analysis"
words = extract_words(text)
print(words)
# Output: ['text', 'sample', 'analysis']
```

### Example 2: Calculate Frequency

```python
from src.text_processing import get_word_frequency

texts = [
    "Python is great",
    "Python is fast",
    "Programming in Python"
]

frequency = get_word_frequency(texts, n_words=10)
print(frequency)
# Output: {'python': 3, 'great': 1, 'fast': 1, ...}
```

### Example 3: Create Sankey Diagram

```python
from src.visualization import create_sankey_diagram
from src import get_color_palette

texts = ["Python is great", "Python is fast", "Programming in Python"]

# Get color palette
colorscale = get_color_palette("Viridis")

# Create chart
fig = create_sankey_diagram(
    texts,
    n_words=10,
    colorscale=colorscale,
    main_node_color="#1f77b4",
    opacity=0.8,
    height=600
)

# Save or display
fig.show()  # For Jupyter
# or
fig.write_html("output.html")  # Save as HTML
```

### Example 4: Parse Custom Stopwords

```python
from src.text_processing import parse_custom_stopwords

user_input = "python, java, javascript"
stopwords = parse_custom_stopwords(user_input)
print(stopwords)
# Output: {'python', 'java', 'javascript'}

# With line breaks
multiline = """
python
java
javascript
"""
stopwords = parse_custom_stopwords(multiline)
```

### Example 5: Normalize Text

```python
from src.text_processing import normalize_text

text = "São Paulo is incredible!"
normalized = normalize_text(text)
print(normalized)
# Output: "Sao Paulo is incredible!"
```

### Example 6: Frequency DataFrame

```python
from src.visualization import create_word_frequency_dataframe

texts = [
    "Python is great",
    "Python is fast",
    "Programming in Python"
]

df = create_word_frequency_dataframe(texts, n_words=5)
print(df)
#        Word  Frequency
# 0     python           3
# 1      great           1
# 2       fast           1
```

## Complete Example: Feedback Analysis

```python
import pandas as pd
from src import (
    create_sankey_diagram,
    create_word_frequency_dataframe,
    get_color_palette,
    parse_custom_stopwords
)

# Load data
df = pd.read_csv('feedbacks.csv', sep=';')

# Select feedback column
texts = df['feedback'].dropna().tolist()

# Custom words to ignore
custom_stops = parse_custom_stopwords("customer, company, service")

# Create chart
colorscale = get_color_palette("Plasma", invert=False)
fig = create_sankey_diagram(
    texts,
    n_words=20,
    colorscale=colorscale,
    custom_stop_words=custom_stops
)

# Display chart
fig.show()

# Get frequency table
freq_df = create_word_frequency_dataframe(
    texts,
    n_words=20,
    custom_stop_words=custom_stops
)

# Save results
freq_df.to_csv('frequencies.csv', index=False)
print("Analysis complete!")
print(freq_df.head(10))
```

## Unit Test Example

```python
# tests/test_text_processing.py
import pytest
from src.text_processing import (
    extract_words,
    parse_custom_stopwords,
    get_word_frequency,
    normalize_text
)

def test_extract_words():
    """Test word extraction"""
    result = extract_words("hello world test")
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(len(p) > 2 for p in result)

def test_normalize_text():
    """Test text normalization"""
    result = normalize_text("São Paulo")
    assert "~" not in result

def test_parse_custom_stopwords():
    """Test stopword parsing"""
    result = parse_custom_stopwords("python, java, javascript")
    assert "python" in result
    assert len(result) == 3

def test_get_word_frequency():
    """Test frequency calculation"""
    texts = ["python python", "java java java"]
    result = get_word_frequency(texts, n_words=2)
    assert "java" in result
    assert result["java"] >= result.get("python", 0)

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Using with Jupyter Notebook

```python
# Import modules
from src import create_sankey_diagram, get_color_palette
import pandas as pd

# Load data
df = pd.read_csv('data/exemplo_pesquisa.csv', sep=';')

# Select column
texts = df.iloc[:, 2].dropna().tolist()

# Create chart
colorscale = get_color_palette("Inferno")
fig = create_sankey_diagram(texts, colorscale=colorscale)

# Display in Jupyter
fig.show()
```

## Customize Configuration

Edit `config.py` to customize:

```python
# Reduce minimum word length
MIN_WORD_LENGTH = 2

# Add stopwords
ADDITIONAL_STOP_WORDS.add("my_word")

# Change default settings
DEFAULT_N_WORDS = 25
DEFAULT_CHART_HEIGHT = 800
DEFAULT_OPACITY = 0.9
```

## Performance - Processing Large Files

```python
import pandas as pd
from src import create_sankey_diagram

# Load in chunks if needed
df = pd.read_csv('large_file.csv', sep=';', nrows=10000)

# Use only sample for quick analysis
sample = df.iloc[:, 2].sample(n=1000, random_state=42)
texts = sample.dropna().tolist()

# Create chart
fig = create_sankey_diagram(texts, n_words=20)
fig.show()
```

## Export Results

```python
from src.visualization import create_word_frequency_dataframe
import json

texts = ["Python Python Java", "Python C++ Rust"]

# Get frequencies
freq_df = create_word_frequency_dataframe(texts, n_words=10)

# Save as CSV
freq_df.to_csv('frequencies.csv', index=False)

# Save as JSON
freq_json = freq_df.to_json(orient='records')
with open('frequencies.json', 'w') as f:
    f.write(freq_json)

# Save as Excel
freq_df.to_excel('frequencies.xlsx', index=False)
```

---

For more information, see documentation in `README.md` and `DEVELOPMENT.md`
