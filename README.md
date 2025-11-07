# lingo-text-of-own: Language Learning from User-Defined Literature Library 📚

A Streamlit-based vocabulary learning tool that helps you learn foreign languages through literature that you like to read. Extract sentences from your local library, compare machine translations, and build your personalized vocabulary notebook with a gamified tracking system.

---

**Licenses:**
- 💻 **Code**: [AGPL-3.0](LICENSE) - Ensures modifications stay open source
- 📖 **Documentation**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - Free to share and adapt with attribution

---

## ✨ Features

### 📖 Smart Sentence Extraction
- Random sentence selection from your local HTML library
- Support for filtering by specific topics (originally designed for AO3 fanfiction)
- Customizable content source

### 🌐 Multi-Language Translation
- **Currently Supported Languages**: Spanish, French, Italian (easily extensible)
- **Dual Translation Engines**: 
  - Google Translate (via `deep-translator`)
  - DeepL API
- Side-by-side comparison mode for translation quality assessment & easily locating/interpreting unfamiliar words
- Direct links to online dictionaries and text-to-speech

### 📝 Intelligent Vocabulary Notebook
- **Smart Tracking**: Automatically detects and consolidates word variations
- **Rich Context**: Stores up to 128 encounters per word with:
  - Original sentence from library work
  - English reference translations (Google + DeepL)
  - Target language translations (Google + DeepL)
  - Source work metadata
- **Encounter History**: 
  - Index 0: First encounter (permanently preserved)
  - Index 1-127: Recent encounters (circular buffer)
- **Parent-Child Relationships**: Link related word forms together, helps learning
- **Personal Notes**: Add custom annotations to any word, helps learning

### 🎮 Gamified Learning System
- **HP (Health Points) System**: 
  - Start with HP = 3
  - "Don't know well" (+2 HP)
  - "Seems familiar" (-1 HP)
  - HP = 0 → Promoted to Hall of Fame
- **Hall of Fame**: Showcase your mastered vocabulary
  - Track days since mastery
  - View first & final encounter details
  - Breakthrough system (kick back to Vocabulary Notebook when needed)
  - Special ✨ golden frame for 3+ breakthroughs
- **Future Stats**: ATK, DEF, RES, SPD (placeholder for future features)

### 📊 Progress Tracking
- Days since program start (customizable "birth date")
- Total vocabulary count by language
- Vocabulary management tools (rename, delete, set relationships, etc.)
- Sortable views (recent encounters/reviews, first seen, encounter count, etc.)

## 🚀 Installation

### Prerequisites
- Python 3.8+
- DeepL API key (free tier: 500,000 characters/month)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/language-learning-literature.git
cd language-learning-literature
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up your API key**

Choose one of the following methods:

**Option A: Environment Variable (Recommended)**
```bash
export DEEPL_API_KEY="your-api-key-here"
```

**Option B: Configuration File**

Create a `config.json` file (not tracked by git):
```json
{
  "deepl_api_key": "your-api-key-here"
}
```

**Option C: Streamlit Secrets** (for deployment)

Create `.streamlit/secrets.toml`:
```toml
DEEPL_API_KEY = "your-api-key-here"
```

4. **Prepare your own library of literature**

Place your HTML files in a directory (e.g., `library/`). The app expects HTML files with Chinese text content (supports for more languages planned). Update the `LOCAL_DIR` path in the code to point to your library directory.

## 📦 Usage

### Launch the App

```bash
streamlit run main.py
```

### Basic Workflow

1. **Configure Settings** (Sidebar):
   - Select target language(s)
   - Enable/disable translation comparison mode
   - Toggle AO3-specific features if needed

2. **Extract & Translate**:
   - Click "🎲 Draw a sentence & translate" to get a random sentence
   - View translations in English and your target language(s)
   - Listen to pronunciation via Google Translate or DeepL links

3. **Build Your Vocabulary**:
   - Copy unknown words/phrases
   - Click "📝 Add to {lang_name} vocabulary" to add to your vocabulary notebook
   - System automatically tracks context and metadata

4. **Review & Manage**:
   - Navigate to "📖 Vocabulary Notebook" to see all saved words
   - Click "好像认识" ("Seems familiar") to decrease HP (-1)
   - Click "不太认识" ("Don't know well") to increase HP (+2)
   - View detailed encounter history for each word
   - Manage personal Notes; check related words; etc.

5. **Track Progress**:
   - Check "🏆 Hall of Fame" for mastered vocabulary
   - Use management tools to organize (rename, delete, set parent-child relationships)

## 🗂️ Project Structure

```
.
├── main.py                 # Main Streamlit application
├── vocabulary_db.py        # SQLite database operations
├── vocabulary.db           # Database file (auto-generated)
├── requirements.txt        # Python dependencies
├── config.json            # Optional: API keys (not in git)
├── .gitignore             # Git ignore rules
└── library/               # Your HTML text files (not in git)
```

## 🛠️ Configuration

### Supported Languages

Currently supports Spanish, French, and Italian as target languages. To add more languages, update the `SUPPORTED_LANGUAGES` dictionary in `main.py`:

```python
SUPPORTED_LANGUAGES = {
    'de': {  # German
        'name': 'German',
        'tts_google': lambda text: f"https://translate.google.com/?sl=de&tl=en&text={quote_plus(text)}&op=translate",
        'tts_deepl': lambda text: f"https://www.deepl.com/translator#de/en/{quote(text, safe='')}",
        'word_pattern': r"[A-Za-zÄÖÜäöüß]+"
    },
    # Add more languages...
}
```

### Default Language

Change the `DEFAULT_LANG` variable in `main.py`:
```python
DEFAULT_LANG = 'es'  # Spanish (default)
```

## 💾 Data Management

### Database Schema

- **vocabulary**: Core vocabulary table with HP and stats
- **encounters**: Detailed encounter history (up to 128 per word)
- **hall_of_fame**: Mastered vocabulary archive
- **metadata**: System configuration

### Backup

```bash
# Manual backup
cp vocabulary.db vocabulary_backup_$(date +%Y%m%d).db

# View database
sqlite3 vocabulary.db "SELECT word, encounter_count FROM vocabulary ORDER BY encounter_count DESC LIMIT 10;"
```

### Export

```bash
# Export to CSV
sqlite3 vocabulary.db ".mode csv" ".output vocabulary.csv" "SELECT * FROM vocabulary;"
```

## 🎯 Future Features

- [ ] Review mode with spaced repetition
- [ ] Combat stats calculation (ATK/DEF/RES/SPD)
- [ ] Multiple source language (beyond Chinese) & target language support
- [ ] Import/export functionality
- [ ] Learning statistics dashboard
- [ ] Cloud deployment option

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project uses a **dual licensing** approach:

### Source Code: AGPL-3.0

The source code (all `.py` files) is licensed under the **GNU Affero General Public License v3.0**.

**What this means:**
- ✅ Free for personal use, learning, and modification
- ✅ You can use it commercially **if you open-source your modifications**
- ✅ Any web service using this code must provide source code to users
- ✅ You can contribute improvements back to the project

See the [LICENSE](LICENSE) file for full details.

### Documentation: CC BY 4.0

All documentation (including this README, guides, inline comments, and other text files) is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**.

**What this means:**
- ✅ You can freely use, modify, and share the documentation
- ✅ You can use it commercially without restrictions
- ✅ You just need to give appropriate credit
- ✅ You can adapt it for your own projects

See the [LICENSE-DOCS](LICENSE-DOCS) file for full details.

---

For questions about licensing, please contact: [okmijnqazwsx69@gmail.com]

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Translation powered by [DeepL API](https://www.deepl.com/docs-api) and [deep-translator](https://github.com/nidhaloff/deep-translator)
- Inspired by the challenge of learning languages through authentic literature
- Name inspired by the "archive of our own" spirit — this is the users' own textbook, for learning languages they way they love.

## 📧 Contact

- Developed by: xswzaqnjimko
- GitHub: [@xswzaqnjimko](https://github.com/xswzaqnjimko)
- Email: okmijnqazwsx69@gmail.com

---

**Note**: This tool was originally designed for learning from AO3 fanfiction archives but can be adapted for any HTML-based text library. The relationship filtering feature can be disabled if not needed.
