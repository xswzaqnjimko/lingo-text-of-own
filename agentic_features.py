# lingo-text-of-own: Agentic AI Features Module
# AI-powered vocabulary analysis and learning optimization
#
# Copyright (C) 2025 xswzaqnjimko
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.

import os
import json
import re
from typing import Dict, List, Optional, Tuple
import anthropic

# ============ Configuration ============

def load_anthropic_key():
    """Load Anthropic API key from multiple sources"""
    # 1. Environment variable
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    
    # 2. config.json file
    try:
        with open("config.json") as f:
            config = json.load(f)
            key = config.get("anthropic_api_key")
            if key:
                return key
    except:
        pass
    
    # 3. Streamlit secrets
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")
    except:
        pass
    
    return None


# ============ ReAct-style Vocabulary Agent (Feature 1️⃣) ============

def analyze_word_relationships(
    target_word: str,
    lang: str,
    existing_vocab: List[Dict],
    encounter_contexts: List[str]
) -> Dict:
    """
    Uses ReAct reasoning to suggest parent-child relationships and generate notes.
    
    Args:
        target_word: The word to analyze
        lang: Language code (es, fr, it)
        existing_vocab: List of existing vocabulary entries
        encounter_contexts: List of sentences where this word appeared
    
    Returns:
        Dict with 'parent_suggestions', 'child_suggestions', 'generated_note'
    """
    api_key = load_anthropic_key()
    if not api_key:
        return {
            'error': 'API key not configured',
            'parent_suggestions': [],
            'child_suggestions': [],
            'generated_note': None
        }
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Prepare context
    vocab_words = [v['word'] for v in existing_vocab[:50]]  # Limit for token efficiency
    context_sample = encounter_contexts[:3]  # First 3 encounters
    
    prompt = f"""You are a language learning assistant using ReAct (Reasoning + Acting) framework.

Task: Analyze the word "{target_word}" in {lang} and suggest vocabulary relationships.

Existing vocabulary (sample): {', '.join(vocab_words)}

Contexts where "{target_word}" appeared:
{chr(10).join(f"- {ctx}" for ctx in context_sample)}

Use ReAct framework:

**Thought 1**: Analyze the word's linguistic features (root, prefix, suffix, verb conjugation, etc.)

**Action 1**: Identify potential parent words (base forms, infinitives, root words)

**Observation 1**: [List potential parent words with reasoning]

**Thought 2**: Consider derived forms and variations

**Action 2**: Identify potential child words (conjugations, derivatives, related forms)

**Observation 2**: [List potential child words from existing vocabulary]

**Thought 3**: Synthesize learning insights from contexts

**Action 3**: Generate a personalized learning note

**Observation 3**: [Learning note]

**Final Output** (JSON format):
{{
  "parent_suggestions": [
    {{"word": "parent_word", "reason": "explanation"}},
    ...
  ],
  "child_suggestions": [
    {{"word": "child_word", "reason": "explanation"}},
    ...
  ],
  "generated_note": "A concise, helpful note about this word's usage pattern"
}}

Respond ONLY with the JSON object, no other text."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {
                'error': 'Failed to parse response',
                'parent_suggestions': [],
                'child_suggestions': [],
                'generated_note': None
            }
    
    except Exception as e:
        return {
            'error': str(e),
            'parent_suggestions': [],
            'child_suggestions': [],
            'generated_note': None
        }


# ============ Hierarchical Learning Path Agent (Feature 2️⃣) ============

def analyze_learning_difficulties(
    vocab_data: Dict,
    hp_history: List[Tuple[int, int]]  # [(day, hp_value), ...]
) -> Dict:
    """
    Uses hierarchical agent architecture to diagnose learning problems.
    
    Args:
        vocab_data: Complete vocabulary entry data
        hp_history: HP change history for this word
    
    Returns:
        Dict with 'diagnosis', 'suggestions', 'priority_level'
    """
    api_key = load_anthropic_key()
    if not api_key:
        return {
            'error': 'API key not configured',
            'diagnosis': 'Cannot analyze without API key',
            'suggestions': [],
            'priority_level': 'unknown'
        }
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Analyze HP trend
    hp_changes = [hp for _, hp in hp_history]
    hp_increasing = sum(1 for i in range(1, len(hp_changes)) if hp_changes[i] > hp_changes[i-1])
    
    prompt = f"""You are a hierarchical learning optimization agent using LATS (Language Agent Tree Search) principles.

**Level 1: Data Analysis**
Word: "{vocab_data['word']}" ({vocab_data['lang']})
Encounter count: {vocab_data['encounter_count']}
Current HP: {vocab_data['stat_hp']}
HP history: {hp_history}
HP increasing events: {hp_increasing}/{len(hp_changes)-1}

**Level 2: Pattern Detection**
Task: Identify if this word shows signs of learning difficulty.
Consider: repeated HP increases, long time between encounters, lack of progress

**Level 3: Root Cause Analysis**
Possible issues:
- Word too similar to others (confusion)
- Word used in varied contexts (complexity)
- Insufficient review frequency
- Need different learning approach

**Level 4: Strategy Formulation**
Based on diagnosis, suggest concrete actions.

**Output Format** (JSON):
{{
  "diagnosis": "Brief explanation of learning pattern",
  "priority_level": "high|medium|low",
  "suggestions": [
    "Specific actionable suggestion 1",
    "Specific actionable suggestion 2",
    ...
  ],
  "recommended_review_frequency": "daily|every_2_days|weekly"
}}

Respond ONLY with JSON."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                'error': 'Failed to parse response',
                'diagnosis': 'Could not analyze',
                'suggestions': [],
                'priority_level': 'unknown'
            }
    
    except Exception as e:
        return {
            'error': str(e),
            'diagnosis': f'Error: {str(e)}',
            'suggestions': [],
            'priority_level': 'unknown'
        }


# ============ Translation Quality Agent (Feature 3️⃣) ============

def evaluate_translation_quality(
    original_text: str,
    google_translation: str,
    deepl_translation: str,
    target_lang: str
) -> Dict:
    """
    Multi-agent refinement: evaluate and select best translation.
    
    Args:
        original_text: Original Chinese text
        google_translation: Google Translate result
        deepl_translation: DeepL result
        target_lang: Target language code
    
    Returns:
        Dict with 'best_translation', 'quality_scores', 'reasoning'
    """
    api_key = load_anthropic_key()
    if not api_key:
        return {
            'best_translation': deepl_translation,  # Default to DeepL
            'quality_scores': {'google': 0.5, 'deepl': 0.5},
            'reasoning': 'API key not configured, defaulting to DeepL',
            'error': 'No API key'
        }
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are a translation quality evaluation agent using multi-agent refinement principles.

**Task**: Compare two translations and determine which is better for language learning.

Original (Chinese): "{original_text}"

Translation A (Google): "{google_translation}"
Translation B (DeepL): "{deepl_translation}"

Target language: {target_lang}

**Evaluation Criteria**:
1. Accuracy: Does it preserve the original meaning?
2. Naturalness: Is it natural in the target language?
3. Learning value: Is it helpful for learners to see this phrasing?
4. Grammar: Is it grammatically correct?

**Process**:
1. Score each translation (0-10) on each criterion
2. Identify any critical errors
3. Select the better translation
4. If both are poor, suggest why

**Output Format** (JSON):
{{
  "google_scores": {{"accuracy": X, "naturalness": X, "learning_value": X, "grammar": X}},
  "deepl_scores": {{"accuracy": X, "naturalness": X, "learning_value": X, "grammar": X}},
  "best_translation": "google|deepl|both_poor",
  "reasoning": "Brief explanation of choice",
  "critical_issues": ["List any serious errors found"]
}}

Respond ONLY with JSON."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {
                'best_translation': deepl_translation,
                'reasoning': 'Failed to parse evaluation',
                'error': 'Parse error'
            }
    
    except Exception as e:
        return {
            'best_translation': deepl_translation,
            'reasoning': f'Error during evaluation: {str(e)}',
            'error': str(e)
        }


# ============ Smart Learning Suggestion (for "随便学学" button) ============

def suggest_words_to_review(
    all_vocab: List[Dict],
    hp_histories: Dict[int, List[Tuple[int, int]]],  # {vocab_id: [(day, hp), ...]}
    count: int = 5
) -> List[Dict]:
    """
    Suggests words that need review based on HP trends and time since last encounter.
    
    Returns:
        List of vocab entries with 'suggestion_reason' added
    """
    api_key = load_anthropic_key()
    if not api_key:
        # Fallback: simple heuristic
        struggling_words = [v for v in all_vocab if v.get('stat_hp', 0) > 5]
        return struggling_words[:count]
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Prepare summary data
    vocab_summary = []
    for v in all_vocab[:30]:  # Analyze top 30 for efficiency
        vocab_id = v['id']
        hp_hist = hp_histories.get(vocab_id, [])
        vocab_summary.append({
            'word': v['word'],
            'hp': v.get('stat_hp', 0),
            'encounters': v.get('encounter_count', 0),
            'last_seen_day': v.get('last_encounter_day', 0),
            'hp_trend': 'increasing' if len(hp_hist) > 1 and hp_hist[-1][1] > hp_hist[0][1] else 'stable'
        })
    
    prompt = f"""You are a personalized learning recommendation agent.

**Current vocabulary status** (sample):
{json.dumps(vocab_summary, indent=2)}

**Task**: Select {count} words that the user should review now, prioritizing:
1. Words with increasing HP (struggling to learn)
2. Words not seen recently
3. Words with high HP but low encounter count (early stage difficulty)

**Output Format** (JSON):
{{
  "recommended_words": [
    {{"word": "word1", "reason": "Why review this now"}},
    {{"word": "word2", "reason": "Why review this now"}},
    ...
  ]
}}

Respond ONLY with JSON."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
            recommended = result.get('recommended_words', [])
            
            # Match back to full vocab entries
            suggestions = []
            for rec in recommended:
                matching = [v for v in all_vocab if v['word'] == rec['word']]
                if matching:
                    entry = matching[0].copy()
                    entry['suggestion_reason'] = rec['reason']
                    suggestions.append(entry)
            
            return suggestions[:count]
        else:
            return all_vocab[:count]
    
    except Exception as e:
        print(f"Error in suggest_words_to_review: {e}")
        return all_vocab[:count]
