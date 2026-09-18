# lingo-text-of-own: Language Learning from User-Defined Literature Library

A Streamlit-based vocabulary learning tool that helps you learn foreign languages with your favorite literature! Extract sentences from your local library, compare translation engines, and build a personalized vocabulary notebook with gamified tracking. Still in progress.

---

v1.2 (2026-09-18): Google Translate switched to official Cloud Translation API v2 (requires GOOGLE_API_KEY); added support for AO3 official download HTML format; navigation redesigned with st.radio; added daily activity tracking with learning record page.

---

## Project Structure
```
lingo-text-of-own/
└── contents/
    ├── main/
    │   ├── launcher.txt                 # Commands example for launching
    │   └── scripts/
    │       ├── main.py                  # Main Streamlit application
    │       ├── vocabulary_db.py         # SQLite database operations
    │       └── dependencies/
    │           ├── __init__.py
    │           ├── config.py            # Centralized paths, API keys, settings
    │           ├── ao3_parser.py        # HTML parsing & keyword matching
    │           ├── translation.py       # Google Cloud Translation, DeepL, dictionary links
    │           ├── ui_components.py     # Streamlit display functions
    │           └── i18n.py              # Internationalization (WIP)
    └── data/                            # Personal data (not on GitHub)
        ├── library/
        └── vocabulary_notebook/
            └── vocabulary.db            # SQLite database (auto-generated)
```

---

## Features

### Core Functionality

**Sentence Extraction**
- Random sentence selection from your local HTML library
- Optional filtering by keywords
- Customizable content source

**Multi-Language Translation**
- Currently supports: Spanish, French, Italian (extensible)
- Dual translation engines: Google Translate and DeepL API
- Side-by-side comparison mode for quality assessment
- Direct links to online dictionaries and text-to-speech

**Vocabulary Notebook**
- Rich context storage: up to 128 encounters per word (extensible) including original sentences, translations, and source metadata
- Parent-child word relationships for learning word families
- Personal notes for custom annotations

**Gamified Learning System**
- HP tracking: starts at 3, "Seems familiar" (-1), "Don't know well" (+2), HP=0 → Hall of Fame
- Breakthrough system: return mastered words to active study when needed
- Progress tracking and statistics

---

## Installation

### Prerequisites
- Python 3.8+
- Google Cloud Translation API key (free tier: 500,000 characters/month)
- DeepL API key (free tier: 500,000 characters/month)

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure
#    Edit scripts/dependencies/config.py, or directly edit in launcher.txt for fast deployment

# 3. Place AO3 official download HTML files in data/library/ao3/works/
```

---

## Usage

### Launch the App

From `contents/main/`:
```bash
streamlit run scripts/main.py
```
Or copy (and edit) the commands in `launcher.txt` into an Automator app for double-click launch.

### Learning Workflow

1. **Sidebar** — select target language(s), toggle comparison mode, configure filters
2. **Draw a sentence** — random extraction from your library with multi-engine translation
3. **Add words** — unknown words go to your vocabulary notebook with full context
4. **Review** — "Seems familiar" / "Don't know well" to track learning via HP system
5. **Hall of Fame** — mastered words (HP=0) graduate; bring them back if needed

---

## Configuration

All settings live in `scripts/dependencies/config.py`:

| Setting | What it does |
|---|---|
| `GOOGLE_API_KEY` | Google Cloud Translation API key; or set in launcher.txt |
| `DEEPL_API_KEY` | DeepL API key; or set in launcher.txt |
| `DEFAULT_LANG` | Default target language (`'es'`, `'fr'`, `'it'`) |
| `SUPPORTED_LANGUAGES` | Add new target languages here |
| `LANGUAGE_DICTIONARIES` | External dictionary URLs per language |

### Database

Auto-generated at `data/vocabulary_notebook/vocabulary.db`. Back up using:
```bash
cp vocabulary.db vocabulary_backup_$(date +%Y%m%d).db
```

---

## To-do (maybe)

- Other kinds of library input
- Spaced repetition review mode
- Multiple source language support (English first)
- i18n for English & other language UI
- Stats based on learning patterns & dashboard
- Import/export functionality
- and more :D

---

**License:** [MIT](LICENSE.txt)

---

## Acknowledgments

Built with [Streamlit](https://streamlit.io/), [Google Cloud Translation API](https://cloud.google.com/translate), and [DeepL API](https://www.deepl.com/docs-api). Name inspired by AO3 - thank you AO3 for everything; thanks to creator's friends & families, techs, chats, chazuke & sashimi.


