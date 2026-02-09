# lingo-text-of-own: Language Learning from User-Defined Literature Library

A Streamlit-based vocabulary learning tool that helps you learn foreign languages with your favorite literature! Extract sentences from your local library, compare translation engines, and build a personalized vocabulary notebook with gamified tracking. Still in progress.

---

## Project Structure
```
lingo-text-of-own/
└── v1.1/
    └── main/
        ├── launcher.txt                 # Commands for launching
        ├── scripts/
        │   ├── main.py                  # Main Streamlit application
        │   ├── vocabulary_db.py         # SQLite database operations
        │   ├── ao3_collect_urls.py      # URL collection
        │   ├── ao3_download.py          # Batch downloader
        │   └── dependencies/
        │       ├── __init__.py
        │       ├── config.py            # Centralized paths, API keys, settings
        │       ├── ao3_parser.py        # HTML parsing & keyword matching
        │       ├── translation.py       # DeepL, Google, dictionary links
        │       ├── ui_components.py     # Streamlit display functions
        │       └── i18n.py              # Internationalization (WIP)
        └── data/
            ├── library/ao3/
            │   ├── ao3_downloads/       # Downloaded HTML files
            │   └── urls_all.txt         # Collected work URLs for download
            └── vocabulary_notebook/
                └── vocabulary.db        # SQLite database (auto-generated)
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
- DeepL API key (free tier: 500,000 characters/month)
- [FanFicFare](https://github.com/JimmXinu/FanFicFare) (for template html downloads)

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install FanFicFare

# 2. Configure
#    Edit scripts/dependencies/config.py, or directly edit in launcher.txt for fast deployment

# 3. Place HTML files in data/library/library_group
#    Or use the built-in scripts to collect & download (see below)
```

---

## Usage

### Launch the App

From `v1.1/main/`:
```bash
streamlit run scripts/main.py
```
Or copy (and edit) the commands in `launcher.txt` into an Automator app for double-click launch.

### Build Your Library

Both scripts are PyCharm-runnable with zero arguments (defaults from `config.py`):

```bash
# Collect work URLs (auto-resumes on failure, auto-retries up to 5x)
python scripts/ao3_collect_urls.py

# Download all works as HTML (auto-retries on failure)
python scripts/ao3_download.py
```

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

## To-do

- Spaced repetition review mode
- Multiple source language support (English first)
- i18n for English & other language UI
- Stats based on learning patterns & dashboard
- Import/export functionality
- and more :D

---

**Licenses:**
- Code: [AGPL-3.0](LICENSE)
- Documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---

## Acknowledgments

Built with [Streamlit](https://streamlit.io/), [DeepL API](https://www.deepl.com/docs-api), [deep-translator](https://github.com/nidhaloff/deep-translator), and [FanFicFare](https://github.com/JimmXinu/FanFicFare). Thanks to creator's personalized needs & interests, friends & families, techs, chats, chazuke & sashimi.


