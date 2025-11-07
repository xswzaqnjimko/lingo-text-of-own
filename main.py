# lingo-text-of-own: Language Learning from User-Defined Literature Library
# Learn foreign languages through authentic literary works
# 
# Copyright (C) 2025 xswzaqnjimko
#
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Documentation and comments in this file are licensed under CC BY 4.0.
# See LICENSE-DOCS for details.
# 
# Original development aided by AI assistants (GPT-5, Claude Sonnet 4.5)

import os
import re
import sys
import random
import unicodedata
import urllib.parse as up
from pathlib import Path
from html import unescape
import time
import json

import streamlit as st
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# Vocabulary database module
import vocabulary_db as vdb


# ============ Configuration ============

# Default language (change to 'fr' for French, 'it' for Italian, etc.)
DEFAULT_LANG = 'es'  # Spanish

# Supported languages with dictionaries and TTS links
LANGUAGE_DICTIONARIES = {
    'es': 'https://www.ingles.com/traductor/',
    'fr': 'https://dictionnaire.lerobert.com/definition/',
    'it': 'https://dizionari.corriere.it/dizionario_italiano/'
}

SUPPORTED_LANGUAGES = {
    'es': {
        'name': 'Spanish',
        'tts_google': lambda text: f"https://translate.google.com/?sl=es&tl=en&text={up.quote_plus(text)}&op=translate",
        'tts_deepl': lambda text: f"https://www.deepl.com/translator#es/en/{up.quote(text, safe='')}",
        'word_pattern': r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"
    },
    'fr': {
        'name': 'French',
        'tts_google': lambda text: f"https://translate.google.com/?sl=fr&tl=en&text={up.quote_plus(text)}&op=translate",
        'tts_deepl': lambda text: f"https://www.deepl.com/translator#fr/en/{up.quote(text, safe='')}",
        'word_pattern': r"[A-Za-zÀ-ÿÇçŒœ]+"
    },
    'it': {
        'name': 'Italian',
        'tts_google': lambda text: f"https://translate.google.com/?sl=it&tl=en&text={up.quote_plus(text)}&op=translate",
        'tts_deepl': lambda text: f"https://www.deepl.com/translator#it/en/{up.quote(text, safe='')}",
        'word_pattern': r"[A-Za-zÀÈÉÌÒÙàèéìòù]+"
    },
}

# Relationship filters (for AO3 fanfiction, optional)
# Leave empty [] to disable filtering
TARGET_RELATIONSHIPS = [
    # Add your preferred relationships here, e.g.:
    # "Character A/Character B",
]

# API Keys configuration (Priority: environment variable > config.json > st.secrets)
def load_deepl_key():
    """Load DeepL API key from multiple sources"""
    # 1. Environment variable
    key = os.getenv("DEEPL_API_KEY")
    if key:
        return key
    
    # 2. config.json file
    config_path = Path("config.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                key = config.get("deepl_api_key")
                if key:
                    return key
        except:
            pass
    
    # 3. Streamlit secrets
    try:
        return st.secrets.get("DEEPL_API_KEY", None)
    except:
        return None

DEEPL_API_KEY = load_deepl_key()
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

# Local library path - CHANGE THIS to your library directory
LOCAL_DIR = Path("library")  # Your HTML files directory


# ============ Helper Functions ============

# Chinese sentence segmentation
SENT_RE = re.compile(r'.+?(?:[。！？]|……)(?:[」』"〉》）\)\]]+)?')

def clean_text(t: str) -> str:
    """Clean HTML entities and whitespace"""
    t = unescape(t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\u3000', ' ', t)
    t = re.sub(r'\s*\n\s*', '\n', t)
    return t.strip()

def extract_sentences_from_html(path: Path):
    """Extract Chinese sentences from HTML file"""
    try:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract text
        text_blocks = []
        for block in soup.find_all(['p', 'div']):
            text_blocks.append(block.get_text("\n", strip=True))
        
        if not text_blocks:
            text_blocks.append(soup.get_text("\n", strip=True))
        
        full_text = clean_text("\n".join(text_blocks))
        sentences = [s.strip() for s in SENT_RE.findall(full_text) if s.strip()]
        
        # Extract basic metadata
        title = soup.title.get_text(strip=True) if soup.title else path.stem
        
        return {
            "path": str(path),
            "title": title,
            "sentences": sentences,
        }
    except Exception as e:
        st.error(f"Error reading {path.name}: {e}")
        return None


# ============ Translation Functions ============

def google_translate(text, target_lang):
    """Translate using Google Translate"""
    try:
        translator = GoogleTranslator(source='zh-CN', target=target_lang)
        return translator.translate(text)
    except Exception as e:
        return f"(Translation error: {e})"

def deepl_translate(text, source_lang, target_lang):
    """Translate using DeepL API"""
    if not DEEPL_API_KEY:
        return "(DeepL API key not configured)"
    
    try:
        response = requests.post(
            DEEPL_API_URL,
            headers={"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"},
            data={
                "text": text,
                "source_lang": source_lang.upper(),
                "target_lang": target_lang.upper()
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()["translations"][0]["text"]
        else:
            return f"(DeepL error: {response.status_code})"
    except Exception as e:
        return f"(DeepL error: {e})"

def translate_sentence(sentence, target_langs):
    """Translate a sentence to multiple languages"""
    translations = {}
    
    # English (as intermediate reference)
    translations['en'] = {
        'google': google_translate(sentence, 'en'),
        'deepl': deepl_translate(sentence, 'ZH', 'EN')
    }
    
    # Target languages
    for lang in target_langs:
        translations[lang] = {
            'google': google_translate(sentence, lang),
            'deepl': deepl_translate(sentence, 'ZH', lang.upper())
        }
    
    return translations


# ============ Streamlit UI ============

st.set_page_config(
    page_title="Language Learning from User-Defined Literature Library",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home'

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Language selection
    available_langs = list(SUPPORTED_LANGUAGES.keys())
    lang_names = [f"{code} - {SUPPORTED_LANGUAGES[code]['name']}" for code in available_langs]
    
    default_index = available_langs.index(DEFAULT_LANG) if DEFAULT_LANG in available_langs else 0
    
    selected_langs = st.multiselect(
        "Select target language(s)",
        options=available_langs,
        default=[DEFAULT_LANG],
        format_func=lambda x: f"{x} - {SUPPORTED_LANGUAGES[x]['name']}"
    )
    
    # Translation options
    show_comparison = st.checkbox("Show dual translation comparison", value=True)
    
    # Navigation
    st.divider()
    st.markdown("### 📖 Navigation")
    
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.current_view = 'home'
        st.rerun()
    
    if st.button("📝 Vocabulary", use_container_width=True):
        st.session_state.current_view = 'vocabulary'
        st.rerun()
    
    if st.button("🏆 Hall of Fame", use_container_width=True):
        st.session_state.current_view = 'hall_of_fame'
        st.rerun()
    
    # Statistics
    st.divider()
    st.markdown("### 📊 Statistics")
    
    current_day = vdb.get_current_day()
    st.caption(f"📅 Day {current_day}")
    
    # Vocabulary stats
    try:
        all_vocab = vdb.get_vocabulary_list()
        st.caption(f"📝 Total words: {len(all_vocab)}")
        
        # By language
        lang_counts = {}
        for word in all_vocab:
            lang = word.get('lang', 'unknown')
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        
        for lang, count in sorted(lang_counts.items()):
            lang_name = SUPPORTED_LANGUAGES.get(lang, {}).get('name', lang)
            st.caption(f"  {lang_name}: {count}")
    except:
        pass
    
    # Hall of Fame stats
    try:
        hof_list = vdb.get_hall_of_fame_list()
        st.caption(f"🏆 Mastered: {len(hof_list)}")
    except:
        pass


# Main content area
if st.session_state.current_view == 'vocabulary':
    st.title("📖 Vocabulary Notebook")
    st.markdown("View and manage your saved words")
    
    # Language filter
    filter_lang = st.selectbox(
        "Filter by language",
        options=['All'] + available_langs,
        format_func=lambda x: "All Languages" if x == 'All' else f"{x} - {SUPPORTED_LANGUAGES[x]['name']}"
    )
    
    # Get vocabulary
    try:
        if filter_lang == 'All':
            vocab_list = vdb.get_vocabulary_list()
        else:
            vocab_list = vdb.get_vocabulary_list(lang=filter_lang)
        
        if not vocab_list:
            st.info("No words saved yet. Start reading and add some words!")
        else:
            for word_data in vocab_list:
                lang_code = word_data['lang']
                lang_name = SUPPORTED_LANGUAGES.get(lang_code, {}).get('name', lang_code)
                
                # Word header
                with st.expander(f"**{lang_name}** | {word_data['word']} (×{word_data['encounter_count']})"):
                    # Stats
                    st.write(f"**HP:** {word_data.get('stat_hp', 3)}")
                    st.write(f"**First seen:** Day {word_data['first_seen_day']}")
                    st.write(f"**Last seen:** Day {word_data['last_encounter_day']}")
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("👍 Seems familiar", key=f"know_{word_data['id']}"):
                            success, msg = vdb.decrease_hp(word_data['id'])
                            if success:
                                st.success(msg)
                                st.rerun()
                    with col2:
                        if st.button("👎 Don't know well", key=f"dontknow_{word_data['id']}"):
                            success, msg = vdb.increase_hp(word_data['id'])
                            if success:
                                st.success(msg)
                                st.rerun()
    except Exception as e:
        st.error(f"Error loading vocabulary: {e}")

elif st.session_state.current_view == 'hall_of_fame':
    st.title("🏆 Hall of Fame")
    st.markdown("Words you've mastered (HP = 0)")
    
    try:
        hof_list = vdb.get_hall_of_fame_list()
        
        if not hof_list:
            st.info("No words in Hall of Fame yet. Keep learning!")
        else:
            for hof_data in hof_list:
                lang_code = hof_data['lang']
                lang_name = SUPPORTED_LANGUAGES.get(lang_code, {}).get('name', lang_code)
                
                current_day = vdb.get_current_day()
                days_mastered = current_day - hof_data.get('last_encounter_day', 0)
                
                with st.expander(f"**{lang_name}** | {hof_data['word']} | Mastered {days_mastered} days ago"):
                    st.write(f"**Total encounters:** {hof_data['total_encounters']}")
                    st.write(f"**Breakthrough count:** {hof_data.get('breakthrough_count', 0)}")
                    
                    if st.button("↩️ Return to vocabulary", key=f"demote_{hof_data['id']}"):
                        success, msg = vdb.demote_from_hall_of_fame(hof_data['id'])
                        if success:
                            st.success(msg)
                            st.rerun()
    except Exception as e:
        st.error(f"Error loading Hall of Fame: {e}")

else:  # Home view - main learning interface
    st.title("📚 Language Learning from Literature")
    st.markdown("Learn languages through authentic texts")
    
    # Check if library exists
    if not LOCAL_DIR.exists():
        st.error(f"⚠️ Library directory not found: `{LOCAL_DIR}`")
        st.info("Please create a `library/` directory and add your HTML files, or update the LOCAL_DIR path in the code.")
        st.stop()
    
    # Load and cache HTML files
    @st.cache_data
    def load_library():
        """Load all HTML files from library directory"""
        records = []
        for html_file in LOCAL_DIR.glob("*.html"):
            record = extract_sentences_from_html(html_file)
            if record and record['sentences']:
                records.append(record)
        return records
    
    try:
        records = load_library()
        
        if not records:
            st.warning("No valid HTML files found in library directory.")
            st.info("Add HTML files with Chinese text to your library directory.")
            st.stop()
        
        total_sentences = sum(len(r['sentences']) for r in records)
        st.caption(f"📦 Library: {len(records)} documents, {total_sentences} sentences")
        
        # Draw sentence button
        if st.button("🎲 Draw a sentence & translate", type="primary"):
            # Pick random document and sentence
            rec = random.choice(records)
            sent = random.choice(rec['sentences'])
            
            # Translate
            with st.spinner("Translating..."):
                translations = translate_sentence(sent, selected_langs)
            
            # Save to session state
            st.session_state['current_sentence'] = sent
            st.session_state['current_translations'] = translations
            st.session_state['current_record'] = rec
            st.session_state['current_langs'] = selected_langs
        
        # Display saved sentence
        if 'current_sentence' in st.session_state:
            sent = st.session_state['current_sentence']
            translations = st.session_state['current_translations']
            rec = st.session_state['current_record']
            display_langs = st.session_state['current_langs']
            
            st.divider()
            
            # Original sentence
            st.markdown("### 📄 Original (Chinese)")
            st.write(sent)
            
            # English reference
            st.markdown("### 🇬🇧 English")
            if show_comparison:
                st.write(f"**Google:** {translations['en']['google']}")
                st.write(f"**DeepL:** {translations['en']['deepl']}")
            else:
                st.write(translations['en']['google'])
            
            # Target languages
            for lang_code in display_langs:
                lang_name = SUPPORTED_LANGUAGES[lang_code]['name']
                st.markdown(f"### {lang_name}")
                
                if show_comparison:
                    st.write(f"**Google:** {translations[lang_code]['google']}")
                    st.write(f"**DeepL:** {translations[lang_code]['deepl']}")
                else:
                    st.write(translations[lang_code]['google'])
                
                # Add to vocabulary
                st.markdown(f"**📝 Add to {lang_name} vocabulary:**")
                word_input = st.text_input(
                    "Enter word/phrase:",
                    key=f"word_input_{lang_code}",
                    placeholder="Copy unfamiliar word here"
                )
                
                if st.button(f"➕ Add to {lang_name} vocabulary", key=f"add_{lang_code}"):
                    if word_input and word_input.strip():
                        success, message = vdb.add_word(
                            word=word_input.strip(),
                            lang=lang_code,
                            sentence_zh=sent,
                            translations=translations,
                            source_info={'title': rec['title'], 'work_id': ''}
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter a word first")
                
                # Dictionary & TTS links
                if lang_code in LANGUAGE_DICTIONARIES:
                    dict_url = LANGUAGE_DICTIONARIES[lang_code]
                    st.markdown(f"[📖 Dictionary]({dict_url})")
                
                tts_google = SUPPORTED_LANGUAGES[lang_code]['tts_google'](sent)
                tts_deepl = SUPPORTED_LANGUAGES[lang_code]['tts_deepl'](sent)
                st.markdown(f"[🔊 Google TTS]({tts_google}) | [🔊 DeepL TTS]({tts_deepl})")
            
            st.divider()
            st.markdown("**Source:**")
            st.caption(f"Document: {rec['title']}")
    
    except Exception as e:
        st.error(f"Error loading library: {e}")
        st.exception(e)
