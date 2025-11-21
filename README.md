# lingo-text-of-own: Language Learning from User-Defined Literature Library

A Streamlit-based vocabulary learning tool that helps you learn foreign languages with your favorite literature! Extract sentences from your local library, compare translation engines, and build a personalized vocabulary notebook with gamified tracking.

This project was born from the need to learn languages through fanfiction and other engaging content, rather than textbooks. Updating.

---

**Licenses:**
- Code: [AGPL-3.0](LICENSE) - Ensures modifications stay open source
- Documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - Free to share and adapt with attribution

---

## Features

### Core Functionality

**Smart Sentence Extraction**
- Random sentence selection from your local HTML library
- Optional filtering by specific topics (originally designed for AO3 fanfiction)
- Customizable content source

**Multi-Language Translation**
- Currently supports: Spanish, French, Italian (easily extensible)
- Dual translation engines: Google Translate and DeepL API
- Side-by-side comparison mode for quality assessment
- Direct links to online dictionaries and text-to-speech

**Intelligent Vocabulary Notebook**
- Automatic detection and consolidation of word variations
- Rich context storage: up to 128 encounters per word
- Stores original sentences, translations (both engines), and source metadata
- Parent-child word relationships for learning word families
- Personal notes for custom annotations

**Gamified Learning System**
- HP (Health Points) tracking system
  - Start with HP = 3
  - "Don't know well" increases HP (+2)
  - "Seems familiar" decreases HP (-1)
  - HP = 0 promotes word to Hall of Fame
- Hall of Fame for mastered vocabulary
- Breakthrough system: return words to active study when needed
- Progress tracking and statistics

### AI-Powered Features

**Agentic AI Enhancements**
- ReAct-style vocabulary analysis: automatically suggests parent-child word relationships
- Hierarchical learning difficulty diagnosis using LATS-inspired architecture
- Multi-agent translation quality evaluation
- Smart review suggestions based on learning patterns
- Semantic-based related word recommendations (ideal for small datasets)

### Internationalization
- UI language switching (Chinese/English)
- Easy to extend to additional languages
- Centralized translation management


---

## Installation

### Prerequisites
- Python 3.8 or higher
- DeepL API key (free tier: 500,000 characters/month)
- Optional: Anthropic API key for AI features (free tier: $5 credit)

### Setup

1. Clone the repository
```bash
git clone https://github.com/xswzaqnjimko/lingo-text-of-own.git
cd lingo-text-of-own
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure API keys

Choose one of the following methods:

**Option A: Environment Variables (Recommended)**
```bash
export DEEPL_API_KEY="your-deepl-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # optional, for AI features
```

**Option B: Configuration File**

Create a `config.json` file (not tracked by git):
```json
{
  "deepl_api_key": "your-deepl-key",
  "anthropic_api_key": "your-anthropic-key"
}
```

See `config_example.json` for a template.

4. Prepare your text library

Place your HTML files in a directory (e.g., `library/`). The app currently expects Chinese source text with plans to support more languages. Update the `LOCAL_DIR` path in the code if needed.

---

## Usage

### Launch the App

```bash
streamlit run main.py
```

### Basic Workflow

1. **Configure Settings** (Sidebar):
   - Select target language(s)
   - Choose UI language (Chinese/English)
   - Enable/disable translation comparison mode
   - Toggle AO3-specific features if applicable

2. **Extract and Translate**:
   - Click to draw a random sentence from your library
   - View translations in English and your target language(s)
   - Access pronunciation via Google Translate or DeepL links

3. **Build Your Vocabulary**:
   - Add unknown words/phrases to your notebook
   - System automatically tracks context and metadata
   - Use AI features to analyze word relationships

4. **Review and Manage**:
   - Navigate to Vocabulary Notebook to see all saved words
   - Use "Seems familiar" / "Don't know well" buttons to track learning
   - View detailed encounter history for each word
   - Add personal notes and set parent-child relationships
   - Get AI-powered recommendations for related words to review

5. **Track Progress**:
   - Check Hall of Fame for mastered vocabulary
   - Use management tools to organize your notebook
   - View learning statistics and patterns

---

## Project Structure

```
.
├── main.py                      # Main Streamlit application
├── vocabulary_db.py             # SQLite database operations
├── agentic_features.py          # AI agent implementations
├── i18n.py                      # Internationalization support
├── vocabulary.db                # Database (auto-generated)
├── requirements.txt             # Python dependencies
├── config.json                  # API keys (not in git, see config_example.json)
├── .gitignore                   # Git ignore rules
├── library/                     # Your HTML text files (not in git)
└── LICENSE, LICENSE-DOCS        # License files
```

---

## Configuration

### Supported Languages

Currently supports Spanish, French, and Italian as target languages. To add more languages, update the `SUPPORTED_LANGUAGES` dictionary in `main.py`. See the code comments for details.

### Database Schema

- `vocabulary`: Core vocabulary table with HP and stats
- `encounters`: Detailed encounter history (up to 128 per word)
- `hall_of_fame`: Mastered vocabulary archive
- `hp_history`: HP change tracking for learning analysis (optional, for AI features)
- `metadata`: System configuration

### Data Management

Backup your database regularly:
```bash
cp vocabulary.db vocabulary_backup_$(date +%Y%m%d).db
```

Export to CSV:
```bash
sqlite3 vocabulary.db ".mode csv" ".output vocabulary.csv" "SELECT * FROM vocabulary;"
```

---

## AI Features (Optional)

The AI features are optional enhancements that require an Anthropic API key. They implement concepts from recent research in agentic AI:

- **ReAct Framework** (Yao et al., ICLR 2023): Reasoning-action cycles for vocabulary analysis
- **LATS Architecture** (Zhou et al., ICML 2024): Hierarchical learning difficulty diagnosis
- **Multi-Agent Refinement** (Yuksel et al., REALM 2025): Translation quality evaluation
- **Semantic Analysis**: Related word recommendations without requiring user history

These features are designed to work well even with small datasets, making them suitable for language learners at any stage.

For implementation details and usage, see [docs/AI_FEATURES.md](docs/AI_FEATURES.md).

---

## Roadmap

Planned features:
- Review mode update with spaced repetition algorithms
- Combat stats calculation (ATK/DEF/RES/SPD) based on learning patterns
- Multiple source language support (beyond Chinese)
- Import/export functionality
- Enhanced learning statistics dashboard
- Deployment guides for cloud hosting

---

## Contributing

Contributions are welcome. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Make your changes with clear commit messages
4. Push to your branch: `git push origin feature/YourFeature`
5. Open a Pull Request

Please maintain code quality and add tests where appropriate.

---

## License

This project uses dual licensing:

### Source Code: AGPL-3.0

All `.py` files are licensed under the GNU Affero General Public License v3.0. This means:
- Free for personal use, learning, and modification
- Commercial use is allowed if modifications are open-sourced
- Web services using this code must provide source code to users

See [LICENSE](LICENSE) for details.

### Documentation: CC BY 4.0

Documentation (README, guides, comments) is licensed under Creative Commons Attribution 4.0 International. This means:
- Free to use, modify, and share
- Commercial use allowed without restrictions
- Attribution required

See [LICENSE-DOCS](LICENSE-DOCS) for details.

For licensing questions: okmijnqazwsx69@gmail.com

---

## Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) for the web interface
- [DeepL API](https://www.deepl.com/docs-api) and [deep-translator](https://github.com/nidhaloff/deep-translator) for translations
- [Anthropic Claude API](https://www.anthropic.com/) for AI features

Motivated by the creator's need of learning languages through fun text.
Facilitated by the creator's friend(s) during development.
Name inspired by the "archive of our own" spirit - this is the users' own textbook, for learning languages the way they love.

---

## Contact

- Developer: xswzaqnjimko
- GitHub: [@xswzaqnjimko](https://github.com/xswzaqnjimko)
- Email: okmijnqazwsx69@gmail.com

---

**Note**: This tool was originally designed for learning from AO3 fanfiction but can be adapted for any HTML-based text library. Features like relationship filtering and AO3-specific can be disabled if not needed.
