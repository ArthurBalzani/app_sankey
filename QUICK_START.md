# ✅ Quick Start Guide

## 🚀 How to Get Started

### 1️⃣ Install Dependencies (if you haven't already)

```bash
pip install -r requirements.txt
```

### 2️⃣ Run the Application

```bash
streamlit run app.py
```

Your application will open at `http://localhost:8501`

### 3️⃣ Use a CSV File

- Click "Upload CSV file"
- Load your data
- Select desired options
- Generate the Sankey chart!

## 📚 Documentation

| Document           | Content                                           |
| ------------------ | ------------------------------------------------- |
| **README.md**      | 📖 How to use the app, CSV format, troubleshooting |
| **DEVELOPMENT.md** | 🛠️ How to extend and maintain the code             |
| **EXAMPLES.md**    | 💡 Code examples for each module                   |
| **INDEX.md**       | 📑 Documentation index                             |

## 🎯 Key Improvements

✅ **Modularization**: Code separated into reusable modules  
✅ **Centralized Configuration**: All constants in `config.py`  
✅ **Documentation**: Docstrings in all functions  
✅ **Type Hints**: Type annotations for better safety  
✅ **Performance**: Optimized caching with Streamlit  
✅ **Organization**: Well-structured folders  
✅ **Reusability**: Functions importable in other projects  

## 🔧 Use in Another Project

```python
# Import functions from src module
from src.text_processing import extract_words, get_word_frequency
from src.visualization import create_sankey_diagram

# Use normally
words = extract_words("your text here")
frequency = get_word_frequency([...])
fig = create_sankey_diagram([...])
```

## 🧪 Tests

Create tests in `tests/test_your_file.py`:

```python
from src.text_processing import extract_words

def test_extract_words():
    result = extract_words("test")
    assert isinstance(result, list)
```

Run tests:
```bash
pytest tests/
```

## 🔗 Useful Links

- 📖 [Streamlit Docs](https://docs.streamlit.io)
- 📊 [Plotly Docs](https://plotly.com/python)
- 🐼 [Pandas Docs](https://pandas.pydata.org/docs)
- 🔤 [NLTK Docs](https://www.nltk.org)

## ❓ Frequently Asked Questions

### Q: How to add a new stopword?
**A:** Edit `config.py` and add to `ADDITIONAL_STOP_WORDS`

### Q: How to change the default color palette?
**A:** Edit `config.py`, variable `DEFAULT_COLOR_PALETTE`

### Q: How to use the modules in Jupyter?
**A:** See `EXAMPLES.md` section "Using with Jupyter Notebook"

### Q: Where to report bugs?
**A:** Create an issue on GitHub or contact support

## 🚢 Deployment

Your application is ready for:

- **Streamlit Cloud**: Connect GitHub repo → Automatic deployment
- **Heroku**: `git push heroku main`
- **Docker**: Create `Dockerfile` based on `runtime.txt`
- **AWS, Google Cloud**: Follow standard Python guides

## 🆘 Support

If you have issues:

1. **Check Requirements**: `pip install -r requirements.txt`
2. **Python Version**: Should be 3.8+
3. **Valid CSV**: Check format
4. **Logs**: `streamlit logs` for debugging

## 📞 Contact

For questions about project organization, see:
- `README.md` - Usage guide
- `DEVELOPMENT.md` - Development guide
- Code docstrings - Detailed descriptions

---

✨ **Happy coding!** ✨
