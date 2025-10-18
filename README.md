# 📊 Sankey Word Frequency Analyzer

A Streamlit application for visual analysis of word frequency using Sankey diagrams. This application allows you to upload a CSV file containing questions and answers, and generate a Sankey diagram to visualize the frequency of the most common words in each column.

## ✨ Features

- 📤 CSV file upload with validation
- 🔄 Text processing with automatic stopword removal
- 📈 Interactive Sankey diagram generation with Plotly
- 🎨 16 customizable color palettes
- 🔧 Customizable word filters
- 📊 Word frequency tables
- 🌍 Support for multiple encodings (UTF-8, Latin1, ISO-8859-1, cp1252)

## 📋 Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`
- 🎨 16 customizable color palettes

## 🚀 How to Install

1. Clone or download this repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run app.py
```

## 📖 How to Use

1. After starting the application, upload a CSV file
2. The first two columns of the file will be ignored
3. Select the column (question) you want to analyze
4. Adjust the number of most frequent words to display
5. Click on "Generate Sankey Diagram"

## 📁 Project Structure

```
app_sankey/2. Install the dependencies:
├── app.py                    # Streamlit interface (entry point)
├── config.py                 # Centralized configuration
├── requirements.txt          # Python dependencies
├── runtime.txt              # Python version for deployment
├── README.md                # This file
├── src/                     # Main package
    ├── __init__.py
    ├── text_processing.py   # Text processing and word extraction
    └── visualization.py     # Sankey chart creation
```

## 🔧 Configuration

All centralized configurations are in `config.py`

- **Processing constants**: Minimum word size, stopwords
- **Color palettes**: Viridis, Plasma, Inferno, etc.
- **Default parameters**: Number of words, chart height, opacity



## 🛠️ Main Modules

### `src/text_processing.py`

Text processing functions:

- `extract_words()`: Extracts significant words with caching
- `get_word_frequency()`: Calculates word frequency
- `parse_custom_stopwords()`: Converts strings to stopword sets
- `normalize_text()`: Removes accents


### `src/visualization.py`

Visualization functions:

- `create_sankey_diagram()`: Creates interactive Sankey diagram
- `create_word_frequency_dataframe()`: Returns DataFrame with frequencies
- `get_color_palette()`: Returns color palettes by name


## 📋 CSV File Format

```
The CSV file must have at least 3 columns:

- **Columns 1 and 2**: Ignored (e.g., ID, Date)
- **Columns 3+**: Text to analyze (questions/answers)
```

**Example:**

```csv
id;date;What do you think?;How was the experience?
1;2025-01-01;Great service;Very good
2;2025-01-02;Good service;Could improve
```

### ⚠️ Important Tips

- Use semicolon (`;`) as the default delimiter
- Do not include the delimiter character within fields
- Verify that all rows have the same number of columns
- Very short words (< 3 characters) are automatically filtered out
- Portuguese stopwords are automatically removed

## 🎨 Available Color Palettes

**Sequential**: Viridis, Plasma, Inferno, Magma, Cividis, Rainbow, Jet, Turbo, Blues, Greens, Reds, YlOrRd, YlGnBu, PuRd, RdPu
**Divergent**: Spectral, RdYlBu


## 🐛 Troubleshooting

### Error "Expected X fields, saw Y"
- Check if the delimiter is correct
- Make sure no field contains the delimiter
- Check "Ignore problematic rows"
 
### Encoding Problems

- Try different encodings in the advanced options:
- UTF-8 (default)
- Latin1
- ISO-8859-1
- cp1252
 
### File Too Large

- Check "Ignore problematic rows"
- Reduce the number of rows
- Use a smaller file for testing
- Increase the memory limit (if possible)
- Optimize the code for better performance


## 📦 Dependencies

- **streamlit**: Web framework for creating data applications
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive visualizations
- **nltk**: Natural language processing
- **matplotlib**: Color utilities