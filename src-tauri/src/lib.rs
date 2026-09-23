mod database;
mod models;
mod parser;
mod translation;

use models::*;
use rusqlite::Connection;
use std::collections::HashMap;
use std::sync::Mutex;
use tauri::Manager;

/// App state: holds the SQLite connection and cached library data
struct AppState {
    db: Mutex<Connection>,
    db_path: String,
    library: Mutex<Vec<(WorkMeta, Vec<String>)>>,
}

// === Tauri commands ===

// --- Settings & Data Paths ---

#[tauri::command]
fn get_data_paths(state: tauri::State<AppState>) -> DataPaths {
    let lib_path = state
        .library
        .lock()
        .unwrap()
        .first()
        .map(|(meta, _)| {
            // Derive library root from first file's path
            std::path::Path::new(&meta.file_path)
                .parent()
                .and_then(|p| p.parent())
                .and_then(|p| p.parent())
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default()
        })
        .unwrap_or_default();

    DataPaths {
        library_path: lib_path,
        db_path: state.db_path.clone(),
    }
}

#[tauri::command]
fn get_supported_languages() -> Vec<(String, String, String)> {
    translation::get_supported_languages()
}

// --- Library ---

#[tauri::command]
fn scan_library(path: String, state: tauri::State<AppState>) -> LibraryStats {
    let (works, scanned) = parser::scan_library(&path);
    let total_sentences: usize = works.iter().map(|(_, sents)| sents.len()).sum();
    let total_works = works.len();

    *state.library.lock().unwrap() = works;

    LibraryStats {
        total_works,
        total_sentences,
        scanned_files: scanned,
    }
}

#[tauri::command]
fn get_random_sentence(
    target_rels: Vec<String>,
    random_any: bool,
    state: tauri::State<AppState>,
) -> Result<Sentence, String> {
    let library = state.library.lock().unwrap();

    if library.is_empty() {
        return Err("文库为空，请先扫描文库".to_string());
    }

    // Filter by relationship if needed
    let eligible_indices = if random_any || target_rels.is_empty() {
        (0..library.len()).collect::<Vec<_>>()
    } else {
        parser::filter_by_relationship(&library, &target_rels)
    };

    if eligible_indices.is_empty() {
        return Err("当前筛选条件下无可用作品".to_string());
    }

    // Pick a random work (weighted by sentence count would be nice but keep it simple)
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let work_idx = eligible_indices[rng.gen_range(0..eligible_indices.len())];
    let (meta, sentences) = &library[work_idx];

    if sentences.is_empty() {
        return Err("这篇作品没有中文句子".to_string());
    }

    let sent_idx = rng.gen_range(0..sentences.len());

    Ok(Sentence {
        text: sentences[sent_idx].clone(),
        work_id: meta.work_id.clone(),
        work_title: meta.title.clone(),
        relationships: meta.relationships.clone(),
        published: meta.published.clone(),
        updated: meta.updated.clone(),
        series: meta.series.clone(),
    })
}

#[tauri::command]
fn get_library_stats(state: tauri::State<AppState>) -> LibraryStats {
    let library = state.library.lock().unwrap();
    let total_sentences: usize = library.iter().map(|(_, sents)| sents.len()).sum();
    LibraryStats {
        total_works: library.len(),
        total_sentences,
        scanned_files: library.len(),
    }
}

#[tauri::command]
fn get_library_relationships(state: tauri::State<AppState>) -> Vec<String> {
    let library = state.library.lock().unwrap();
    let mut rels: Vec<String> = library
        .iter()
        .flat_map(|(meta, _)| meta.relationships.clone())
        .collect();
    rels.sort();
    rels.dedup();
    rels
}
#[tauri::command]
fn get_eligible_count(
    target_rels: Vec<String>,
    random_any: bool,
    state: tauri::State<AppState>,
) -> (usize, usize) {
    let library = state.library.lock().unwrap();
    let total = library.len();
    let eligible = if random_any || target_rels.is_empty() {
        total
    } else {
        parser::filter_by_relationship(&library, &target_rels).len()
    };
    (eligible, total)
}



// --- Translation ---

#[tauri::command]
fn translate_sentence(
    sentence: String,
    target_langs: Vec<String>,
    google_key: String,
    deepl_key: String,
) -> HashMap<String, EngineTranslations> {
    translation::translate_sentence(&sentence, &target_langs, &google_key, &deepl_key)
}

#[tauri::command]
fn get_dictionary_links(
    google_text: String,
    deepl_text: String,
    lang_code: String,
) -> (Vec<(String, String)>, Vec<(String, String)>) {
    translation::generate_dictionary_links(&google_text, &deepl_text, &lang_code)
}

#[tauri::command]
fn get_tts_link(text: String, lang_code: String, engine: String) -> Option<String> {
    translation::get_tts_link(&text, &lang_code, &engine)
}

// --- Vocabulary ---

#[tauri::command]
fn get_stats(state: tauri::State<AppState>) -> VocabStats {
    let conn = state.db.lock().unwrap();
    database::get_stats(&conn)
}

#[tauri::command]
fn add_word(
    word: String,
    lang: String,
    sentence_zh: String,
    en_google: String,
    en_deepl: String,
    target_google: String,
    target_deepl: String,
    source_id: Option<String>,
    source_title: Option<String>,
    source_detail: Option<String>,
    state: tauri::State<AppState>,
) -> AddWordResult {
    let conn = state.db.lock().unwrap();
    database::add_word(
        &conn,
        &word,
        &lang,
        &sentence_zh,
        &en_google,
        &en_deepl,
        &target_google,
        &target_deepl,
        source_id.as_deref(),
        source_title.as_deref(),
        source_detail.as_deref(),
    )
}

#[tauri::command]
fn add_word_manual(
    word: String,
    lang: String,
    note: Option<String>,
    state: tauri::State<AppState>,
) -> AddWordResult {
    let conn = state.db.lock().unwrap();
    database::add_word_manual(&conn, &word, &lang, note.as_deref())
}

#[tauri::command]
fn get_vocabulary_list(
    lang: Option<String>,
    limit: i64,
    sort_by: String,
    state: tauri::State<AppState>,
) -> Vec<VocabEntry> {
    let conn = state.db.lock().unwrap();
    database::get_vocabulary_list(&conn, lang.as_deref(), limit, &sort_by)
}

#[tauri::command]
fn get_word_encounters(vocab_id: i64, state: tauri::State<AppState>) -> Vec<Encounter> {
    let conn = state.db.lock().unwrap();
    database::get_word_encounters(&conn, vocab_id)
}

#[tauri::command]
fn get_word_by_id(vocab_id: i64, state: tauri::State<AppState>) -> Option<VocabEntry> {
    let conn = state.db.lock().unwrap();
    database::get_word_by_id(&conn, vocab_id)
}

#[tauri::command]
fn get_children(parent_id: i64, state: tauri::State<AppState>) -> Vec<VocabEntry> {
    let conn = state.db.lock().unwrap();
    database::get_children(&conn, parent_id)
}

#[tauri::command]
fn decrease_hp(vocab_id: i64, state: tauri::State<AppState>) -> HpChangeResult {
    let conn = state.db.lock().unwrap();
    database::decrease_hp(&conn, vocab_id)
}

#[tauri::command]
fn increase_hp(vocab_id: i64, state: tauri::State<AppState>) -> (bool, String) {
    let conn = state.db.lock().unwrap();
    database::increase_hp(&conn, vocab_id)
}

#[tauri::command]
fn delete_word(vocab_id: i64, state: tauri::State<AppState>) -> (bool, String) {
    let conn = state.db.lock().unwrap();
    database::delete_word(&conn, vocab_id)
}

#[tauri::command]
fn rename_word(vocab_id: i64, new_word: String, state: tauri::State<AppState>) -> (bool, String) {
    let conn = state.db.lock().unwrap();
    database::rename_word(&conn, vocab_id, &new_word)
}

#[tauri::command]
fn search_word(word: String, lang: String, state: tauri::State<AppState>) -> Vec<VocabEntry> {
    let conn = state.db.lock().unwrap();
    database::search_word(&conn, &word, &lang)
}

#[tauri::command]
fn update_note(vocab_id: i64, note: String, state: tauri::State<AppState>) -> (bool, String) {
    let conn = state.db.lock().unwrap();
    database::update_note(&conn, vocab_id, &note)
}

#[tauri::command]
fn set_parent(
    child_id: i64,
    parent_id: Option<i64>,
    state: tauri::State<AppState>,
) -> (bool, String) {
    let conn = state.db.lock().unwrap();
    database::set_parent(&conn, child_id, parent_id)
}

// --- Hall of Fame ---

#[tauri::command]
fn get_hall_of_fame_list(
    lang: Option<String>,
    limit: i64,
    state: tauri::State<AppState>,
) -> Vec<HallOfFameEntry> {
    let conn = state.db.lock().unwrap();
    database::get_hall_of_fame_list(&conn, lang.as_deref(), limit)
}

#[tauri::command]
fn demote_from_hall_of_fame(hof_id: i64, state: tauri::State<AppState>) -> (bool, String) {
    let conn = state.db.lock().unwrap();
    database::demote_from_hall_of_fame(&conn, hof_id)
}

// --- Activity ---

#[tauri::command]
fn log_sentence_viewed(lang: String, state: tauri::State<AppState>) {
    let conn = state.db.lock().unwrap();
    database::log_sentence_viewed(&conn, &lang);
}

#[tauri::command]
fn log_word_added(lang: String, state: tauri::State<AppState>) {
    let conn = state.db.lock().unwrap();
    database::log_word_added(&conn, &lang);
}

#[tauri::command]
fn log_word_reviewed(lang: String, state: tauri::State<AppState>) {
    let conn = state.db.lock().unwrap();
    database::log_word_reviewed(&conn, &lang);
}

#[tauri::command]
fn log_word_graduated(lang: String, state: tauri::State<AppState>) {
    let conn = state.db.lock().unwrap();
    database::log_word_graduated(&conn, &lang);
}

#[tauri::command]
fn get_activity_history(days: i64, state: tauri::State<AppState>) -> Vec<DailyActivity> {
    let conn = state.db.lock().unwrap();
    database::get_activity_history(&conn, days)
}

#[tauri::command]
fn get_activity_summary(days: i64, state: tauri::State<AppState>) -> ActivitySummary {
    let conn = state.db.lock().unwrap();
    database::get_activity_summary(&conn, days)
}

// === App setup ===

fn get_db_path(app: &tauri::App) -> String {
    // Default: ~/Library/Application Support/com.lingo-text.app/vocabulary.db
    let app_dir = app
        .path()
        .app_data_dir()
        .expect("Failed to get app data directory");
    std::fs::create_dir_all(&app_dir).ok();
    app_dir
        .join("vocabulary.db")
        .to_string_lossy()
        .to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let db_path = get_db_path(app);
            let conn = Connection::open(&db_path).expect("Failed to open database");
            database::init_db(&conn).expect("Failed to initialize database");

            app.manage(AppState {
                db: Mutex::new(conn),
                db_path,
                library: Mutex::new(Vec::new()),
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Settings & paths
            get_data_paths,
            get_supported_languages,
            // Library
            scan_library,
            get_random_sentence,
            get_library_stats,
            get_library_relationships,
            get_eligible_count,
            // Translation
            translate_sentence,
            get_dictionary_links,
            get_tts_link,
            // Vocabulary
            get_stats,
            add_word,
            add_word_manual,
            get_vocabulary_list,
            get_word_encounters,
            get_word_by_id,
            get_children,
            decrease_hp,
            increase_hp,
            delete_word,
            rename_word,
            search_word,
            update_note,
            set_parent,
            // Hall of Fame
            get_hall_of_fame_list,
            demote_from_hall_of_fame,
            // Activity
            log_sentence_viewed,
            log_word_added,
            log_word_reviewed,
            log_word_graduated,
            get_activity_history,
            get_activity_summary,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
