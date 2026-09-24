use serde::{Deserialize, Serialize};

/// Metadata parsed from an AO3 HTML file
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkMeta {
    pub work_id: Option<String>,
    pub title: String,
    pub relationships: Vec<String>,
    pub published: Option<String>,
    pub updated: Option<String>,
    pub series: Vec<SeriesInfo>,
    pub file_path: String,
    pub sentence_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeriesInfo {
    pub title: String,
    pub href: Option<String>,
}

/// A single sentence drawn from a work
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sentence {
    pub text: String,
    pub work_id: Option<String>,
    pub work_title: String,
    pub relationships: Vec<String>,
    pub published: Option<String>,
    pub updated: Option<String>,
    pub series: Vec<SeriesInfo>,
}

/// Translation results for a sentence
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranslationResult {
    pub en: EngineTranslations,
    pub targets: std::collections::HashMap<String, EngineTranslations>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineTranslations {
    pub google: Option<String>,
    pub deepl: Option<String>,
}

/// A vocabulary entry from the database
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VocabEntry {
    pub id: i64,
    pub lang: String,
    pub word: String,
    pub first_seen_day: i64,
    pub encounter_count: i64,
    pub last_encounter_day: i64,
    pub stat_hp: i64,
    pub stat_atk: Option<f64>,
    pub stat_def: Option<f64>,
    pub stat_res: Option<f64>,
    pub stat_spd: Option<f64>,
    pub breakthrough: i64,
    pub parent_id: Option<i64>,
    pub note: Option<String>,
    pub last_reviewed_at: Option<String>,
}

/// An encounter record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Encounter {
    pub id: i64,
    pub vocab_id: i64,
    pub encounter_index: i64,
    pub day: Option<i64>,
    pub day_gap: Option<i64>,
    pub sentence_zh: Option<String>,
    pub sentence_en_google: Option<String>,
    pub sentence_en_deepl: Option<String>,
    pub sentence_target_google: Option<String>,
    pub sentence_target_deepl: Option<String>,
    pub source_id: Option<String>,
    pub source_title: Option<String>,
    pub source_detail: Option<String>,
}

/// A hall of fame entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HallOfFameEntry {
    pub id: i64,
    pub lang: String,
    pub word: String,
    pub first_encounter_day: Option<i64>,
    pub last_encounter_day: Option<i64>,
    pub first_encounter_data: Option<String>,
    pub last_encounter_data: Option<String>,
    pub total_encounters: Option<i64>,
    pub breakthrough_count: Option<i64>,
    pub promoted_at: Option<String>,
}

/// Daily activity record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailyActivity {
    pub day: i64,
    pub sentences_viewed: i64,
    pub words_added: i64,
    pub words_reviewed: i64,
    pub words_graduated: i64,
    pub langs_used: String,
}

/// Activity summary over a period
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActivitySummary {
    pub total_days: i64,
    pub active_days: i64,
    pub sentences_viewed: i64,
    pub words_added: i64,
    pub words_reviewed: i64,
    pub words_graduated: i64,
}

/// Vocabulary stats for sidebar
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VocabStats {
    pub current_day: i64,
    pub total_words: i64,
    pub by_lang: std::collections::HashMap<String, i64>,
    pub hall_of_fame_count: i64,
}

/// Language configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub code: String,
    pub name: String,
    pub name_en: String,
    pub dict_url: String,
    pub word_pattern: String,
    pub tts_google_template: String,
    pub tts_deepl_template: String,
}

/// App settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub library_path: Option<String>,
    pub data_dir: Option<String>,
    pub google_api_key: Option<String>,
    pub deepl_api_key: Option<String>,
    pub default_lang: String,
    pub selected_langs: Vec<String>,
    pub ui_language: String,
    pub show_comparison: bool,
    pub enable_ao3: bool,
    pub target_relationships: Vec<String>,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            library_path: None,
            data_dir: None,
            google_api_key: None,
            deepl_api_key: None,
            default_lang: "es".to_string(),
            selected_langs: vec!["es".to_string()],
            ui_language: "zh".to_string(),
            show_comparison: true,
            enable_ao3: true,
            target_relationships: vec![
                "Yuris Leclair | Yuri Leclerc/Claude von Riegan".to_string(),
                "Yuris Leclair | Yuri Leclerc & Claude von Riegan".to_string(),
                "Kaminaga/Miyoshi (Joker Game)".to_string(),
            ],
        }
    }
}

/// Data paths info for the Settings UI
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataPaths {
    pub library_path: String,
    pub db_path: String,
}

/// Result of adding/updating a word
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AddWordResult {
    pub is_new: bool,
    pub message: String,
}

/// Result of HP change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HpChangeResult {
    pub success: bool,
    pub message: String,
    pub promoted: bool,
}

/// Library scan stats
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LibraryStats {
    pub total_works: usize,
    pub total_sentences: usize,
    pub scanned_files: usize,
}

/// API usage stats for current month
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiUsage {
    pub google_chars: i64,
    pub deepl_chars: i64,
    pub month_label: String,
}

/// Result of drawing a sentence from a specific work by ID
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrawFromWorkResult {
    #[serde(flatten)]
    pub sentence: Sentence,
    pub filter_note: Option<String>,
}
