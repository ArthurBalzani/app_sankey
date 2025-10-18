# 📑 Documentation Index

## 🚀 Start Here

1. **[QUICK_START.md](QUICK_START.md)** - Quick start guide in 5 minutes
2. **[README.md](README.md)** - Complete application documentation

## 📚 Detailed Documentation

### For Users
- **[README.md](README.md)**
  - How to use the application
  - Expected CSV format
  - Troubleshooting
  - Available features

### For Developers
- **[DEVELOPMENT.md](DEVELOPMENT.md)**
  - Project architecture
  - How to extend the code
  - Development patterns
  - Adding new features

- **[EXAMPLES.md](EXAMPLES.md)**
  - Code examples
  - Module usage examples
  - Unit tests
  - Real-world use cases

- **[INDEX.md](INDEX.md)**
  - Documentation index
  - Quick reference guide

## 📊 File Structure

```
app_sankey/
├── 📝 DOCUMENTATION
│   ├── README.md
│   ├── QUICK_START.md
│   ├── DEVELOPMENT.md
│   ├── EXAMPLES.md
│   └── INDEX.md (this file)
│
├── 🚀 APPLICATION
│   ├── app.py                    (Streamlit)
│   ├── config.py                 (Configuration)
│   └── requirements.txt           (Dependencies)
│
├── 📦 MODULARIZED CODE
│   └── src/
│       ├── __init__.py
│       ├── text_processing.py
│       └── visualization.py
│
└── 🧪 TESTS
    └── tests/
        └── __init__.py
```

## 🎯 Guide by Profile

### 👤 End User
1. Read **[QUICK_START.md](QUICK_START.md)** - 5 minutes
2. Read **[README.md](README.md)** - 10 minutes
3. Run `streamlit run app.py`

### 👨‍💻 Python Developer
1. Read **[QUICK_START.md](QUICK_START.md)** - 5 minutes
2. Explore **[DEVELOPMENT.md](DEVELOPMENT.md)** - 15 minutes
3. See **[EXAMPLES.md](EXAMPLES.md)** - 20 minutes
4. Start using/extending modules

### 👔 Software Architect
1. Read **[README.md](README.md)** - 10 minutes
2. Study **[DEVELOPMENT.md](DEVELOPMENT.md)** - 20 minutes
3. Review modules in `src/` - 15 minutes

### 🎓 Python Beginner
1. **[README.md](README.md)** - Basic concepts
2. **[EXAMPLES.md](EXAMPLES.md)** - See working examples
3. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Learn patterns

## 🔍 Find Information Quickly

| Question                | Answer                                  |
| ----------------------- | --------------------------------------- |
| How to use the app?     | See **README.md**                       |
| Error when running?     | See **README.md** "Troubleshooting"     |
| Add a feature?          | See **DEVELOPMENT.md**                  |
| Code examples?          | See **EXAMPLES.md**                     |
| Use in another project? | See **EXAMPLES.md** "Import modules"    |
| CSV format?             | See **README.md** "CSV File Format"     |
| Write tests?            | See **EXAMPLES.md** "Unit Test Example" |
| Deploy?                 | See **README.md** or **DEVELOPMENT.md** |

## 🚀 Useful Commands

```bash
# Run application
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Check types
mypy src/

# Format code
black src/ app.py config.py
```

## 📞 Quick FAQ

**Q: How to add new stopword?**
A: Edit `config.py` → `ADDITIONAL_STOP_WORDS`

**Q: How to change colors?**
A: Edit `config.py` → `COLOR_PALETTES`

**Q: How to use in another Python project?**
A: `from src import create_sankey_diagram`

**Q: Where to add tests?**
A: In `tests/` → create `test_your_file.py`

**Q: How to deploy?**
A: See **DEVELOPMENT.md** → "Deployment" section

## 📊 Recommended Reading Structure

```
START
  ↓
[QUICK_START.md] - 5 min
  ↓
[README.md] - 15 min
  ↓
┌─────────────────────────────┐
│    Choose your path:        │
├─────────────────────────────┤
│                             │
├→ [DEVELOPMENT.md] (dev)    │
├→ [EXAMPLES.md] (examples)  │
└→ [INDEX.md] (reference)    │
  ↓
START DEVELOPING!
```

## ✨ Next Actions

1. Read this file (you're here!)
2. Go to [QUICK_START.md](QUICK_START.md)
3. Run: `streamlit run app.py`
4. Explore documentation as needed
5. Start developing!

---

**Professionally developed with ❤️**
