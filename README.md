# lingo-text: Language Learning from Your Own Literature

A desktop vocabulary learning app that picks random sentences from your local literature library, machine-translates them to target languages, and helps you build a personalized vocabulary notebook with gamified tracking. A personal language learning tool only - no content is hosted or distributed; what you put in your library is your own responsibility, please respect the rights of original creators.

---

v2.0.0 (2026-09): Rewritten as a native desktop app with Tauri v2 (React + Rust), replacing the v1.x Streamlit web app. Faster startup, offline-capable UI, persistent settings, and the same learning workflow.

---

## Project Structure

```
lingo-text-of-own/
├── app/                                # Tauri v2 desktop app
│   ├── src/                            # React frontend
│   │   ├── main.jsx                    # Entry point
│   │   ├── index.css                   # Global styles
│   │   ├── components/
│   │   │   ├── App.jsx                 # Root component, settings, routing
│   │   │   ├── SentenceView.jsx        # Home page: draw & translate sentences
│   │   │   ├── VocabList.jsx           # Vocabulary notebook
│   │   │   ├── HallOfFame.jsx          # Mastered words
│   │   │   ├── Activity.jsx            # Learning activity chart
│   │   │   └── Settings.jsx            # App configuration
│   │   └── services/
│   │       ├── database.js             # Tauri command wrappers
│   │       └── i18n.js                 # UI text (Chinese / English)
│   ├── src-tauri/                      # Rust backend
│   │   ├── src/
│   │   │   ├── lib.rs                  # Tauri commands
│   │   │   ├── database.rs             # SQLite operations
│   │   │   ├── parser.rs               # HTML parsing & relationship filtering
│   │   │   ├── models.rs               # Data structures
│   │   │   └── translation.rs          # Google & DeepL API clients
│   │   ├── icons/                      # App icons
│   │   └── tauri.conf.json             # Tauri configuration
│   └── package.json
└── LICENSE.txt
```

---

## Features

**Sentence Extraction**
- Random sentence selection from your local HTML library
- Optional filtering by keywords
- Pool summary showing eligible vs. total works

**Multi-Language Translation**
- Currently supports: Spanish, French, Italian (extensible)
- Dual translation engines: Google Cloud Translation API and DeepL API
- Side-by-side comparison mode
- Direct links to online dictionaries and text-to-speech

**Vocabulary Notebook**
- Rich context storage: up to 128 encounters per word including original sentences, translations, and source metadata
- Parent-child word relationships for learning word families
- Personal notes, search, sorting, and per-language filtering

**Gamified Learning System**
- HP tracking: starts at 3, "Seems familiar" (-1), "Don't know well" (+2), HP=0 graduates to Hall of Fame
- Breakthrough system: return mastered words to active study when needed
- Daily activity tracking with visual chart (7-day, 30-day, yearly views)
- Learning record stored locally in SQLite

**Desktop App**
- Native macOS app via Tauri v2
- Bilingual UI (Chinese / English)
- Persistent settings (API keys, language preferences, relationship filters)
- SQLite database stored in app support directory

---

## Installation

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Rust](https://www.rust-lang.org/tools/install) (latest stable)
- Google Cloud Translation API key (free tier: 500,000 characters/month)
- DeepL API key (free tier: 500,000 characters/month)

### Setup

```bash
# Clone the repo
git clone https://github.com/xswzaqnjimko/lingo-text-of-own
cd lingo-text-of-own/app

# Install frontend dependencies
npm install

# Run in development mode
npm run tauri:dev
```

On first launch, go to Settings to configure your API keys and library path, etc., and save the settings.

### Build

```bash
cd app
npm run tauri:build
```

The built app will be in `app/src-tauri/target/release/bundle/`.

---

## Usage

### Learning Workflow

1. **Configure** - set API keys, library path, target languages, and relationship filters in Settings
2. **Draw a sentence** - random extraction from your library with multi-engine translation
3. **Add words** - unknown words go to your vocabulary notebook with full context
4. **Review** - "Seems familiar" / "Don't know well" to track learning via HP system
5. **Hall of Fame** - mastered words (HP=0) graduate; bring them back if needed
6. **Activity** - track your daily learning streaks and progress

### Library Setup

Place HTML files (currently mainly designed for AO3 HTML downloads) in a folder on your computer, then set the path in Settings. The app scans the folder on startup and extracts sentences from all HTML files found.

### Database

The vocabulary database is stored at:
```
~/Library/Application Support/com.lingo-text/vocabulary.db
```

Back up using:
```bash
cp ~/Library/Application\ Support/com.lingo-text/vocabulary.db vocabulary_backup_$(date +%Y%m%d).db
```

---

## To-do (maybe)

- Other kinds of library input
- Spaced repetition review mode
- Multiple source language support (English first)
- Import/export functionality
- Cross-platform builds (Windows, Linux)
- and more :D

---

**License:** [MIT](app/LICENSE.txt)

---

## Acknowledgments

Built with [Tauri](https://tauri.app/), [React](https://react.dev/), [Google Cloud Translation API](https://cloud.google.com/translate), and [DeepL API](https://www.deepl.com/docs-api). Name inspired by AO3 - thank you AO3 for everything; thanks to creator's friends & family, teachers, chats, chazuke & sashimi.
