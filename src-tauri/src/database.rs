use chrono::{Datelike, NaiveDate};
use rusqlite::{params, Connection, Result as SqlResult};
use std::collections::HashMap;

use crate::models::*;

const BIRTH_DATE: &str = "2025-10-10";
const MAX_ENCOUNTERS: i64 = 128;

/// Initialize the database, creating tables if needed
pub fn init_db(conn: &Connection) -> SqlResult<()> {
    conn.execute_batch("PRAGMA journal_mode=WAL;")?;
    conn.execute_batch("PRAGMA foreign_keys=ON;")?;

    conn.execute_batch(
        "
        CREATE TABLE IF NOT EXISTS metadata (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS vocabulary (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            lang               TEXT NOT NULL,
            word               TEXT NOT NULL,
            word_lower         TEXT NOT NULL,
            first_seen_day     INTEGER NOT NULL,
            encounter_count    INTEGER DEFAULT 1,
            last_encounter_day INTEGER NOT NULL,
            stat_hp            INTEGER DEFAULT 30,
            stat_atk           REAL,
            stat_def           REAL,
            stat_res           REAL,
            stat_spd           REAL,
            breakthrough       INTEGER DEFAULT 0,
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            parent_id          INTEGER DEFAULT NULL,
            note               TEXT,
            last_reviewed_at   TIMESTAMP,
            UNIQUE(lang, word_lower)
        );

        CREATE TABLE IF NOT EXISTS encounters (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            vocab_id                INTEGER NOT NULL,
            encounter_index         INTEGER NOT NULL,
            day                     INTEGER,
            day_gap                 INTEGER,
            sentence_zh             TEXT,
            sentence_en_google      TEXT,
            sentence_en_deepl       TEXT,
            sentence_target_google  TEXT,
            sentence_target_deepl   TEXT,
            source_id               TEXT,
            source_title            TEXT,
            source_detail           TEXT,
            created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
            UNIQUE(vocab_id, encounter_index)
        );

        CREATE TABLE IF NOT EXISTS hall_of_fame (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            lang                 TEXT NOT NULL,
            word                 TEXT NOT NULL,
            word_lower           TEXT NOT NULL,
            first_encounter_day  INTEGER,
            first_encounter_data TEXT,
            last_encounter_day   INTEGER,
            last_encounter_data  TEXT,
            total_encounters     INTEGER,
            breakthrough_count   INTEGER,
            promoted_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lang, word_lower)
        );

        CREATE TABLE IF NOT EXISTS daily_activity (
            day              INTEGER PRIMARY KEY,
            sentences_viewed INTEGER DEFAULT 0,
            words_added      INTEGER DEFAULT 0,
            words_reviewed   INTEGER DEFAULT 0,
            words_graduated  INTEGER DEFAULT 0,
            langs_used       TEXT DEFAULT '',
            fillblanks_played INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_vocab_lang ON vocabulary(lang);
        CREATE INDEX IF NOT EXISTS idx_vocab_word ON vocabulary(lang, word_lower);
        CREATE INDEX IF NOT EXISTS idx_vocab_hp ON vocabulary(stat_hp);
        CREATE INDEX IF NOT EXISTS idx_encounters_vocab ON encounters(vocab_id);
        CREATE INDEX IF NOT EXISTS idx_hof_lang ON hall_of_fame(lang);
        ",
    )?;

    // Initialize metadata
    conn.execute(
        "INSERT OR IGNORE INTO metadata (key, value) VALUES ('birth_date', ?1), ('schema_version', '2.0')",
        params![BIRTH_DATE],
    )?;

    // --- Migration: rename stat_mdef → stat_res for databases from the Streamlit era ---
    let has_mdef: bool = conn
        .prepare("SELECT COUNT(*) FROM pragma_table_info('vocabulary') WHERE name='stat_mdef'")
        .and_then(|mut s| s.query_row([], |r| r.get(0)))
        .unwrap_or(false);

    if has_mdef {
        conn.execute_batch("ALTER TABLE vocabulary RENAME COLUMN stat_mdef TO stat_res;")?;
    }

    // --- v2.2 Migration: HP×10, crit_evasion column, encounter data cleanup ---
    let schema_version: String = conn
        .query_row(
            "SELECT value FROM metadata WHERE key = 'schema_version'",
            [],
            |row| row.get(0),
        )
        .unwrap_or_else(|_| "2.0".to_string());

    if schema_version.as_str() < "2.2" {
        // 1) HP×10: multiply all existing stat_hp values by 10
        conn.execute_batch("UPDATE vocabulary SET stat_hp = stat_hp * 10;")?;

        // 2) Add crit_evasion column
        let has_crit_evasion: bool = conn
            .prepare("SELECT COUNT(*) FROM pragma_table_info('vocabulary') WHERE name='crit_evasion'")
            .and_then(|mut s| s.query_row([], |r| r.get(0)))
            .unwrap_or(false);

        if !has_crit_evasion {
            conn.execute_batch("ALTER TABLE vocabulary ADD COLUMN crit_evasion REAL DEFAULT 0;")?;
        }

        // 3) Encounter data cleanup: NULL out translation pairs where the word doesn't appear
        {
            let mut enc_stmt = conn.prepare(
                "SELECT e.id, e.sentence_target_google, e.sentence_target_deepl, v.word_lower
                 FROM encounters e JOIN vocabulary v ON e.vocab_id = v.id"
            )?;

            let updates: Vec<(i64, bool, bool)> = enc_stmt
                .query_map([], |row| {
                    let enc_id: i64 = row.get(0)?;
                    let target_google: Option<String> = row.get(1)?;
                    let target_deepl: Option<String> = row.get(2)?;
                    let word_lower: String = row.get(3)?;

                    let google_has_word = target_google
                        .as_ref()
                        .map(|s| s.to_lowercase().contains(&word_lower))
                        .unwrap_or(false);
                    let deepl_has_word = target_deepl
                        .as_ref()
                        .map(|s| s.to_lowercase().contains(&word_lower))
                        .unwrap_or(false);

                    Ok((enc_id, google_has_word, deepl_has_word))
                })?
                .flatten()
                .collect();

            for (enc_id, google_ok, deepl_ok) in &updates {
                if !google_ok {
                    conn.execute(
                        "UPDATE encounters SET sentence_en_google = NULL, sentence_target_google = NULL WHERE id = ?1",
                        params![enc_id],
                    )?;
                }
                if !deepl_ok {
                    conn.execute(
                        "UPDATE encounters SET sentence_en_deepl = NULL, sentence_target_deepl = NULL WHERE id = ?1",
                        params![enc_id],
                    )?;
                }
            }
        }

        // 4) Update schema_version to 2.2
        conn.execute(
            "UPDATE metadata SET value = '2.2' WHERE key = 'schema_version'",
            [],
        )?;
    }


    // --- v2.3 Migration: fillblanks_played column ---
    let schema_version_2: String = conn
        .query_row(
            "SELECT value FROM metadata WHERE key = 'schema_version'",
            [],
            |row| row.get(0),
        )
        .unwrap_or_else(|_| "2.0".to_string());

    if schema_version_2.as_str() < "2.3" {
        let has_fillblanks: bool = conn
            .prepare("SELECT COUNT(*) FROM pragma_table_info('daily_activity') WHERE name='fillblanks_played'")
            .and_then(|mut s| s.query_row([], |r| r.get(0)))
            .unwrap_or(false);

        if !has_fillblanks {
            conn.execute_batch("ALTER TABLE daily_activity ADD COLUMN fillblanks_played INTEGER DEFAULT 0;")?;
        }

        conn.execute(
            "UPDATE metadata SET value = '2.3' WHERE key = 'schema_version'",
            [],
        )?;
    }

    Ok(())
}

/// Get current day number (from birth date)
pub fn get_current_day(conn: &Connection) -> i64 {
    let birth_str: String = conn
        .query_row(
            "SELECT value FROM metadata WHERE key='birth_date'",
            [],
            |row| row.get(0),
        )
        .unwrap_or_else(|_| BIRTH_DATE.to_string());

    let birth = NaiveDate::parse_from_str(&birth_str, "%Y-%m-%d")
        .unwrap_or_else(|_| NaiveDate::from_ymd_opt(2025, 10, 10).unwrap());
    let today = chrono::Local::now().date_naive();
    (today - birth).num_days()
}

/// Get vocabulary statistics
pub fn get_stats(conn: &Connection) -> VocabStats {
    let current_day = get_current_day(conn);

    let total_words: i64 = conn
        .query_row("SELECT COUNT(*) FROM vocabulary", [], |row| row.get(0))
        .unwrap_or(0);

    let hall_of_fame_count: i64 = conn
        .query_row("SELECT COUNT(*) FROM hall_of_fame", [], |row| row.get(0))
        .unwrap_or(0);

    let mut by_lang: HashMap<String, i64> = HashMap::new();
    if let Ok(mut stmt) = conn.prepare("SELECT lang, COUNT(*) FROM vocabulary GROUP BY lang") {
        if let Ok(rows) = stmt.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?))
        }) {
            for row in rows.flatten() {
                by_lang.insert(row.0, row.1);
            }
        }
    }

    VocabStats {
        current_day,
        total_words,
        by_lang,
        hall_of_fame_count,
    }
}

/// Add a word or update encounter
pub fn add_word(
    conn: &Connection,
    word: &str,
    lang: &str,
    sentence_zh: &str,
    en_google: &str,
    en_deepl: &str,
    target_google: &str,
    target_deepl: &str,
    source_id: Option<&str>,
    source_title: Option<&str>,
    source_detail: Option<&str>,
) -> AddWordResult {
    let word = word.trim();
    let word_lower = word.to_lowercase();

    if word.is_empty() {
        return AddWordResult {
            is_new: false,
            message: "词不能为空".to_string(),
        };
    }

    let current_day = get_current_day(conn);

    // Check if exists in vocabulary
    let existing: Option<(i64, String, i64, i64)> = conn
        .query_row(
            "SELECT id, word, encounter_count, last_encounter_day FROM vocabulary WHERE lang = ?1 AND word_lower = ?2",
            params![lang, word_lower],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
        )
        .ok();

    // Check hall of fame
    if existing.is_none() {
        let in_hof: Option<String> = conn
            .query_row(
                "SELECT word FROM hall_of_fame WHERE lang = ?1 AND word_lower = ?2",
                params![lang, word_lower],
                |row| row.get(0),
            )
            .ok();
        if let Some(hof_word) = in_hof {
            return AddWordResult {
                is_new: false,
                message: format!("⚠️ 词条 '{}' 已在总选名人堂，无需重复添加", hof_word),
            };
        }
    }

    // Filter encounter translations: NULL out pairs where the word doesn't appear
    let google_has_word = !target_google.is_empty()
        && target_google.to_lowercase().contains(&word_lower);
    let deepl_has_word = !target_deepl.is_empty()
        && target_deepl.to_lowercase().contains(&word_lower);

    let en_google_val: Option<&str> = if google_has_word { Some(en_google) } else { None };
    let target_google_val: Option<&str> = if google_has_word { Some(target_google) } else { None };
    let en_deepl_val: Option<&str> = if deepl_has_word { Some(en_deepl) } else { None };
    let target_deepl_val: Option<&str> = if deepl_has_word { Some(target_deepl) } else { None };

    match existing {
        None => {
            // New word
            conn.execute(
                "INSERT INTO vocabulary (lang, word, word_lower, first_seen_day, encounter_count, last_encounter_day, stat_hp) VALUES (?1, ?2, ?3, ?4, 1, ?4, 30)",
                params![lang, word, word_lower, current_day],
            ).ok();

            let vocab_id = conn.last_insert_rowid();

            conn.execute(
                "INSERT INTO encounters (vocab_id, encounter_index, day, sentence_zh, sentence_en_google, sentence_en_deepl, sentence_target_google, sentence_target_deepl, source_id, source_title, source_detail) VALUES (?1, 0, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
                params![vocab_id, current_day, sentence_zh, en_google_val, en_deepl_val, target_google_val, target_deepl_val, source_id, source_title, source_detail],
            ).ok();

            AddWordResult {
                is_new: true,
                message: format!("✓ 新词 '{}' 已加入生词本！", word),
            }
        }
        Some((vocab_id, existing_word, count, last_day)) => {
            let day_gap = current_day - last_day;

            conn.execute(
                "UPDATE vocabulary SET encounter_count = encounter_count + 1, last_encounter_day = ?1, stat_hp = stat_hp + 20 WHERE id = ?2",
                params![current_day, vocab_id],
            ).ok();

            let next_index = ((count - 1) % (MAX_ENCOUNTERS - 1)) + 1;

            conn.execute(
                "INSERT OR REPLACE INTO encounters (vocab_id, encounter_index, day, day_gap, sentence_zh, sentence_en_google, sentence_en_deepl, sentence_target_google, sentence_target_deepl, source_id, source_title, source_detail) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
                params![vocab_id, next_index, current_day, day_gap, sentence_zh, en_google_val, en_deepl_val, target_google_val, target_deepl_val, source_id, source_title, source_detail],
            ).ok();

            AddWordResult {
                is_new: false,
                message: format!(
                    "✓ 已更新！这是第 {} 次遇到 '{}'",
                    count + 1,
                    existing_word
                ),
            }
        }
    }
}

/// Add a word manually (no sentence context)
pub fn add_word_manual(
    conn: &Connection,
    word: &str,
    lang: &str,
    note: Option<&str>,
) -> AddWordResult {
    let word = word.trim();
    let word_lower = word.to_lowercase();

    if word.is_empty() {
        return AddWordResult {
            is_new: false,
            message: "词不能为空".to_string(),
        };
    }

    let current_day = get_current_day(conn);

    // Check if already exists
    let exists: bool = conn
        .query_row(
            "SELECT COUNT(*) FROM vocabulary WHERE lang = ?1 AND word_lower = ?2",
            params![lang, word_lower],
            |row| row.get::<_, i64>(0),
        )
        .unwrap_or(0)
        > 0;

    if exists {
        return AddWordResult {
            is_new: false,
            message: format!("词条 '{}' 已存在于生词本", word),
        };
    }

    // Check hall of fame
    let in_hof: bool = conn
        .query_row(
            "SELECT COUNT(*) FROM hall_of_fame WHERE lang = ?1 AND word_lower = ?2",
            params![lang, word_lower],
            |row| row.get::<_, i64>(0),
        )
        .unwrap_or(0)
        > 0;

    if in_hof {
        return AddWordResult {
            is_new: false,
            message: format!("⚠️ 词条 '{}' 已在总选名人堂", word),
        };
    }

    conn.execute(
        "INSERT INTO vocabulary (lang, word, word_lower, first_seen_day, encounter_count, last_encounter_day, stat_hp, note) VALUES (?1, ?2, ?3, ?4, 0, ?4, 30, ?5)",
        params![lang, word, word_lower, current_day, note],
    )
    .ok();

    AddWordResult {
        is_new: true,
        message: format!("✓ 手动添加 '{}' 成功！", word),
    }
}

/// Get vocabulary list with sorting
pub fn get_vocabulary_list(
    conn: &Connection,
    lang: Option<&str>,
    limit: i64,
    sort_by: &str,
) -> Vec<VocabEntry> {
    let order_clause = match sort_by {
        "first_encounter" => "first_seen_day ASC",
        "encounter_count" => "encounter_count DESC",
        "last_reviewed" => "last_reviewed_at DESC NULLS LAST",
        "alphabetical" => "word_lower ASC",
        _ => "last_encounter_day DESC", // "last_encounter" default
    };

    let query = if let Some(_lang_code) = lang {
        format!(
            "SELECT id, lang, word, first_seen_day, encounter_count, last_encounter_day, stat_hp, stat_atk, stat_def, stat_res, stat_spd, breakthrough, parent_id, note, last_reviewed_at, crit_evasion FROM vocabulary WHERE lang = ?1 ORDER BY {} LIMIT ?2",
            order_clause
        )
    } else {
        format!(
            "SELECT id, lang, word, first_seen_day, encounter_count, last_encounter_day, stat_hp, stat_atk, stat_def, stat_res, stat_spd, breakthrough, parent_id, note, last_reviewed_at, crit_evasion FROM vocabulary ORDER BY {} LIMIT ?2",
            order_clause
        )
    };

    let mut entries = Vec::new();

    if let Some(lang_code) = lang {
        if let Ok(mut stmt) = conn.prepare(&query) {
            if let Ok(rows) = stmt.query_map(params![lang_code, limit], |row| {
                Ok(VocabEntry {
                    id: row.get(0)?,
                    lang: row.get(1)?,
                    word: row.get(2)?,
                    first_seen_day: row.get(3)?,
                    encounter_count: row.get(4)?,
                    last_encounter_day: row.get(5)?,
                    stat_hp: row.get(6)?,
                    stat_atk: row.get(7)?,
                    stat_def: row.get(8)?,
                    stat_res: row.get(9)?,
                    stat_spd: row.get(10)?,
                    breakthrough: row.get(11)?,
                    parent_id: row.get(12)?,
                    note: row.get(13)?,
                    last_reviewed_at: row.get(14)?,
                    crit_evasion: row.get(15)?,
                })
            }) {
                for row in rows.flatten() {
                    entries.push(row);
                }
            }
        }
    } else {
        // No language filter — use different param binding
        let query_no_lang = format!(
            "SELECT id, lang, word, first_seen_day, encounter_count, last_encounter_day, stat_hp, stat_atk, stat_def, stat_res, stat_spd, breakthrough, parent_id, note, last_reviewed_at, crit_evasion FROM vocabulary ORDER BY {} LIMIT ?1",
            order_clause
        );
        if let Ok(mut stmt) = conn.prepare(&query_no_lang) {
            if let Ok(rows) = stmt.query_map(params![limit], |row| {
                Ok(VocabEntry {
                    id: row.get(0)?,
                    lang: row.get(1)?,
                    word: row.get(2)?,
                    first_seen_day: row.get(3)?,
                    encounter_count: row.get(4)?,
                    last_encounter_day: row.get(5)?,
                    stat_hp: row.get(6)?,
                    stat_atk: row.get(7)?,
                    stat_def: row.get(8)?,
                    stat_res: row.get(9)?,
                    stat_spd: row.get(10)?,
                    breakthrough: row.get(11)?,
                    parent_id: row.get(12)?,
                    note: row.get(13)?,
                    last_reviewed_at: row.get(14)?,
                    crit_evasion: row.get(15)?,
                })
            }) {
                for row in rows.flatten() {
                    entries.push(row);
                }
            }
        }
    }

    entries
}

/// Get encounters for a word
pub fn get_word_encounters(conn: &Connection, vocab_id: i64) -> Vec<Encounter> {
    let mut encounters = Vec::new();

    if let Ok(mut stmt) = conn.prepare(
        "SELECT id, vocab_id, encounter_index, day, day_gap, sentence_zh, sentence_en_google, sentence_en_deepl, sentence_target_google, sentence_target_deepl, source_id, source_title, source_detail FROM encounters WHERE vocab_id = ?1 ORDER BY encounter_index",
    ) {
        if let Ok(rows) = stmt.query_map(params![vocab_id], |row| {
            Ok(Encounter {
                id: row.get(0)?,
                vocab_id: row.get(1)?,
                encounter_index: row.get(2)?,
                day: row.get(3)?,
                day_gap: row.get(4)?,
                sentence_zh: row.get(5)?,
                sentence_en_google: row.get(6)?,
                sentence_en_deepl: row.get(7)?,
                sentence_target_google: row.get(8)?,
                sentence_target_deepl: row.get(9)?,
                source_id: row.get(10)?,
                source_title: row.get(11)?,
                source_detail: row.get(12)?,
            })
        }) {
            for row in rows.flatten() {
                encounters.push(row);
            }
        }
    }

    encounters
}

/// Get a word by ID
pub fn get_word_by_id(conn: &Connection, vocab_id: i64) -> Option<VocabEntry> {
    conn.query_row(
        "SELECT id, lang, word, first_seen_day, encounter_count, last_encounter_day, stat_hp, stat_atk, stat_def, stat_res, stat_spd, breakthrough, parent_id, note, last_reviewed_at, crit_evasion FROM vocabulary WHERE id = ?1",
        params![vocab_id],
        |row| {
            Ok(VocabEntry {
                id: row.get(0)?,
                lang: row.get(1)?,
                word: row.get(2)?,
                first_seen_day: row.get(3)?,
                encounter_count: row.get(4)?,
                last_encounter_day: row.get(5)?,
                stat_hp: row.get(6)?,
                stat_atk: row.get(7)?,
                stat_def: row.get(8)?,
                stat_res: row.get(9)?,
                stat_spd: row.get(10)?,
                breakthrough: row.get(11)?,
                parent_id: row.get(12)?,
                note: row.get(13)?,
                last_reviewed_at: row.get(14)?,
                crit_evasion: row.get(15)?,
            })
        },
    )
    .ok()
}

/// Get children of a parent word
pub fn get_children(conn: &Connection, parent_id: i64) -> Vec<VocabEntry> {
    let mut children = Vec::new();
    if let Ok(mut stmt) = conn.prepare(
        "SELECT id, lang, word, first_seen_day, encounter_count, last_encounter_day, stat_hp, stat_atk, stat_def, stat_res, stat_spd, breakthrough, parent_id, note, last_reviewed_at, crit_evasion FROM vocabulary WHERE parent_id = ?1",
    ) {
        if let Ok(rows) = stmt.query_map(params![parent_id], |row| {
            Ok(VocabEntry {
                id: row.get(0)?,
                lang: row.get(1)?,
                word: row.get(2)?,
                first_seen_day: row.get(3)?,
                encounter_count: row.get(4)?,
                last_encounter_day: row.get(5)?,
                stat_hp: row.get(6)?,
                stat_atk: row.get(7)?,
                stat_def: row.get(8)?,
                stat_res: row.get(9)?,
                stat_spd: row.get(10)?,
                breakthrough: row.get(11)?,
                parent_id: row.get(12)?,
                note: row.get(13)?,
                last_reviewed_at: row.get(14)?,
                crit_evasion: row.get(15)?,
            })
        }) {
            for row in rows.flatten() {
                children.push(row);
            }
        }
    }
    children
}

/// Decrease HP (好像认识). Returns result with crit info.
pub fn decrease_hp(conn: &Connection, vocab_id: i64) -> HpChangeResult {
    let word = match get_word_by_id(conn, vocab_id) {
        Some(w) => w,
        None => {
            return HpChangeResult {
                success: false,
                message: "词条不存在".to_string(),
                promoted: false,
                crit_rate: 0.0,
                was_crit: false,
                hp_change: 0,
            }
        }
    };

    // Calculate 暴击率 (your crit rate when attacking the word)
    let crit_rate = (0.5 - word.crit_evasion / 100.0).clamp(0.0, 1.0);

    // Roll for crit
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let was_crit = rng.gen::<f64>() < crit_rate;

    // Base -10, crit -15 (×1.5)
    let hp_change: i64 = if was_crit { -15 } else { -10 };
    let new_hp = word.stat_hp + hp_change;

    if new_hp <= 0 {
        // Promote to hall of fame
        match promote_to_hall_of_fame(conn, vocab_id) {
            Ok(()) => HpChangeResult {
                success: true,
                message: format!("🎉 '{}' 总选出道！", word.word),
                promoted: true,
                crit_rate,
                was_crit,
                hp_change,
            },
            Err(e) => HpChangeResult {
                success: false,
                message: format!("出道失败: {}", e),
                promoted: false,
                crit_rate,
                was_crit,
                hp_change: 0,
            },
        }
    } else {
        conn.execute(
            "UPDATE vocabulary SET stat_hp = ?1, last_reviewed_at = CURRENT_TIMESTAMP WHERE id = ?2",
            params![new_hp, vocab_id],
        )
        .ok();

        HpChangeResult {
            success: true,
            message: format!("HP: {} → {} ({})", word.stat_hp, new_hp, hp_change),
            promoted: false,
            crit_rate,
            was_crit,
            hp_change,
        }
    }
}

/// Increase HP (不太认识). Returns result with crit info.
pub fn increase_hp(conn: &Connection, vocab_id: i64) -> HpChangeResult {
    let word = match get_word_by_id(conn, vocab_id) {
        Some(w) => w,
        None => {
            return HpChangeResult {
                success: false,
                message: "词条不存在".to_string(),
                promoted: false,
                crit_rate: 0.0,
                was_crit: false,
                hp_change: 0,
            }
        }
    };

    // Calculate 被暴击率 (word's crit rate when counterattacking)
    let crit_rate = (0.5 + word.crit_evasion / 100.0).clamp(0.0, 1.0);

    // Roll for crit (被暴击)
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let was_crit = rng.gen::<f64>() < crit_rate;

    // Base +20, crit +30 (×1.5)
    let hp_change: i64 = if was_crit { 30 } else { 20 };
    let new_hp = word.stat_hp + hp_change;

    conn.execute(
        "UPDATE vocabulary SET stat_hp = ?1, last_reviewed_at = CURRENT_TIMESTAMP WHERE id = ?2",
        params![new_hp, vocab_id],
    )
    .ok();

    HpChangeResult {
        success: true,
        message: format!("HP: {} → {} (+{})", word.stat_hp, new_hp, hp_change),
        promoted: false,
        crit_rate,
        was_crit,
        hp_change,
    }
}

/// Promote a word to hall of fame
fn promote_to_hall_of_fame(conn: &Connection, vocab_id: i64) -> Result<(), String> {
    let word = get_word_by_id(conn, vocab_id).ok_or("词条不存在")?;

    let encounters = get_word_encounters(conn, vocab_id);

    // Get first encounter data (index 0)
    let first_enc_data = encounters
        .iter()
        .find(|e| e.encounter_index == 0)
        .map(|e| serde_json::to_string(e).unwrap_or_default());

    // Get last encounter data
    let last_enc_data = encounters
        .last()
        .map(|e| serde_json::to_string(e).unwrap_or_default());

    // Insert into hall of fame
    conn.execute(
        "INSERT OR REPLACE INTO hall_of_fame (lang, word, word_lower, first_encounter_day, first_encounter_data, last_encounter_day, last_encounter_data, total_encounters, breakthrough_count) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
        params![
            word.lang,
            word.word,
            word.word.to_lowercase(),
            word.first_seen_day,
            first_enc_data,
            word.last_encounter_day,
            last_enc_data,
            word.encounter_count,
            word.breakthrough,
        ],
    )
    .map_err(|e| e.to_string())?;

    // Delete from vocabulary (cascade deletes encounters)
    conn.execute("DELETE FROM vocabulary WHERE id = ?1", params![vocab_id])
        .map_err(|e| e.to_string())?;

    Ok(())
}

/// Demote from hall of fame back to vocabulary
pub fn demote_from_hall_of_fame(conn: &Connection, hof_id: i64) -> (bool, String) {
    let hof: Option<HallOfFameEntry> = conn
        .query_row(
            "SELECT id, lang, word, first_encounter_day, last_encounter_day, first_encounter_data, last_encounter_data, total_encounters, breakthrough_count, promoted_at FROM hall_of_fame WHERE id = ?1",
            params![hof_id],
            |row| {
                Ok(HallOfFameEntry {
                    id: row.get(0)?,
                    lang: row.get(1)?,
                    word: row.get(2)?,
                    first_encounter_day: row.get(3)?,
                    last_encounter_day: row.get(4)?,
                    first_encounter_data: row.get(5)?,
                    last_encounter_data: row.get(6)?,
                    total_encounters: row.get(7)?,
                    breakthrough_count: row.get(8)?,
                    promoted_at: row.get(9)?,
                })
            },
        )
        .ok();

    match hof {
        None => (false, "名人堂词条不存在".to_string()),
        Some(entry) => {
            let current_day = get_current_day(conn);
            let breakthrough = entry.breakthrough_count.unwrap_or(0) + 1;

            // Re-insert into vocabulary with HP=30 and breakthrough+1
            conn.execute(
                "INSERT OR REPLACE INTO vocabulary (lang, word, word_lower, first_seen_day, encounter_count, last_encounter_day, stat_hp, breakthrough) VALUES (?1, ?2, ?3, ?4, ?5, ?6, 30, ?7)",
                params![
                    entry.lang,
                    entry.word,
                    entry.word.to_lowercase(),
                    entry.first_encounter_day.unwrap_or(current_day),
                    entry.total_encounters.unwrap_or(0),
                    current_day,
                    breakthrough,
                ],
            )
            .ok();

            // Remove from hall of fame
            conn.execute(
                "DELETE FROM hall_of_fame WHERE id = ?1",
                params![hof_id],
            )
            .ok();

            (
                true,
                format!("'{}' 已回归生词本 (突破 {})", entry.word, breakthrough),
            )
        }
    }
}

/// Get hall of fame list
pub fn get_hall_of_fame_list(
    conn: &Connection,
    lang: Option<&str>,
    limit: i64,
) -> Vec<HallOfFameEntry> {
    let mut entries = Vec::new();

    let query = match lang {
        Some(_) => "SELECT id, lang, word, first_encounter_day, last_encounter_day, first_encounter_data, last_encounter_data, total_encounters, breakthrough_count, promoted_at FROM hall_of_fame WHERE lang = ?1 ORDER BY promoted_at DESC LIMIT ?2",
        None => "SELECT id, lang, word, first_encounter_day, last_encounter_day, first_encounter_data, last_encounter_data, total_encounters, breakthrough_count, promoted_at FROM hall_of_fame ORDER BY promoted_at DESC LIMIT ?1",
    };

    let map_row = |row: &rusqlite::Row| {
        Ok(HallOfFameEntry {
            id: row.get(0)?,
            lang: row.get(1)?,
            word: row.get(2)?,
            first_encounter_day: row.get(3)?,
            last_encounter_day: row.get(4)?,
            first_encounter_data: row.get(5)?,
            last_encounter_data: row.get(6)?,
            total_encounters: row.get(7)?,
            breakthrough_count: row.get(8)?,
            promoted_at: row.get(9)?,
        })
    };

    if let Some(lang_code) = lang {
        if let Ok(mut stmt) = conn.prepare(query) {
            if let Ok(rows) = stmt.query_map(params![lang_code, limit], map_row) {
                for row in rows.flatten() {
                    entries.push(row);
                }
            }
        }
    } else {
        if let Ok(mut stmt) = conn.prepare(query) {
            if let Ok(rows) = stmt.query_map(params![limit], map_row) {
                for row in rows.flatten() {
                    entries.push(row);
                }
            }
        }
    }

    entries
}

/// Delete a word
pub fn delete_word(conn: &Connection, vocab_id: i64) -> (bool, String) {
    let word = match get_word_by_id(conn, vocab_id) {
        Some(w) => w,
        None => return (false, "词条不存在".to_string()),
    };

    // Delete encounters first (or rely on CASCADE)
    conn.execute(
        "DELETE FROM encounters WHERE vocab_id = ?1",
        params![vocab_id],
    )
    .ok();
    conn.execute("DELETE FROM vocabulary WHERE id = ?1", params![vocab_id])
        .ok();

    (true, format!("已删除 '{}'", word.word))
}

/// Rename a word
pub fn rename_word(conn: &Connection, vocab_id: i64, new_word: &str) -> (bool, String) {
    let new_word = new_word.trim();
    if new_word.is_empty() {
        return (false, "新名字不能为空".to_string());
    }

    let word = match get_word_by_id(conn, vocab_id) {
        Some(w) => w,
        None => return (false, "词条不存在".to_string()),
    };

    conn.execute(
        "UPDATE vocabulary SET word = ?1, word_lower = ?2 WHERE id = ?3",
        params![new_word, new_word.to_lowercase(), vocab_id],
    )
    .ok();

    (
        true,
        format!("'{}' → '{}'", word.word, new_word),
    )
}

/// Search for a word
pub fn search_word(conn: &Connection, word: &str, lang: &str) -> Vec<VocabEntry> {
    let word_lower = word.trim().to_lowercase();
    let mut results = Vec::new();

    if let Ok(mut stmt) = conn.prepare(
        "SELECT id, lang, word, first_seen_day, encounter_count, last_encounter_day, stat_hp, stat_atk, stat_def, stat_res, stat_spd, breakthrough, parent_id, note, last_reviewed_at, crit_evasion FROM vocabulary WHERE lang = ?1 AND word_lower = ?2",
    ) {
        if let Ok(rows) = stmt.query_map(params![lang, word_lower], |row| {
            Ok(VocabEntry {
                id: row.get(0)?,
                lang: row.get(1)?,
                word: row.get(2)?,
                first_seen_day: row.get(3)?,
                encounter_count: row.get(4)?,
                last_encounter_day: row.get(5)?,
                stat_hp: row.get(6)?,
                stat_atk: row.get(7)?,
                stat_def: row.get(8)?,
                stat_res: row.get(9)?,
                stat_spd: row.get(10)?,
                breakthrough: row.get(11)?,
                parent_id: row.get(12)?,
                note: row.get(13)?,
                last_reviewed_at: row.get(14)?,
                crit_evasion: row.get(15)?,
            })
        }) {
            for row in rows.flatten() {
                results.push(row);
            }
        }
    }

    results
}

/// Update personal note
pub fn update_note(conn: &Connection, vocab_id: i64, note: &str) -> (bool, String) {
    match conn.execute(
        "UPDATE vocabulary SET note = ?1 WHERE id = ?2",
        params![note, vocab_id],
    ) {
        Ok(_) => (true, "注释已保存".to_string()),
        Err(e) => (false, format!("保存失败: {}", e)),
    }
}

/// Set parent-child relationship
pub fn set_parent(conn: &Connection, child_id: i64, parent_id: Option<i64>) -> (bool, String) {
    match conn.execute(
        "UPDATE vocabulary SET parent_id = ?1 WHERE id = ?2",
        params![parent_id, child_id],
    ) {
        Ok(_) => {
            if parent_id.is_some() {
                (true, "母子关系已设置".to_string())
            } else {
                (true, "已取消关联".to_string())
            }
        }
        Err(e) => (false, format!("设置失败: {}", e)),
    }
}

// === Fill-in-the-blank (填空) ===

/// Get languages eligible for fill-in-the-blank (≥ 4 vocab words AND has encounters with target sentences)
pub fn get_fill_blank_eligible_langs(conn: &Connection) -> Vec<(String, i64)> {
    let mut results = Vec::new();

    // Find languages that have at least one encounter with a non-null target sentence
    // AND have at least 4 vocabulary words total
    if let Ok(mut stmt) = conn.prepare(
        "SELECT v.lang, COUNT(*) as word_count
         FROM vocabulary v
         WHERE v.lang IN (
             SELECT DISTINCT v2.lang FROM vocabulary v2
             JOIN encounters e ON e.vocab_id = v2.id
             WHERE e.sentence_target_google IS NOT NULL OR e.sentence_target_deepl IS NOT NULL
         )
         GROUP BY v.lang
         HAVING COUNT(*) >= 4
         ORDER BY v.lang"
    ) {
        if let Ok(rows) = stmt.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?))
        }) {
            for row in rows.flatten() {
                results.push(row);
            }
        }
    }

    results
}

/// Get a fill-in-the-blank question for a given language
pub fn get_fill_blank_question(conn: &Connection, lang: &str) -> Result<FillBlankQuestion, String> {
    use rand::seq::SliceRandom;

    // Fetch candidate encounters: those with a target sentence where the word appears
    let mut candidates: Vec<(i64, String, Option<String>, Option<String>, Option<String>,
                             Option<String>, Option<String>, Option<String>, Option<String>)> = Vec::new();

    if let Ok(mut stmt) = conn.prepare(
        "SELECT v.id, v.word, e.sentence_zh, e.sentence_en_google, e.sentence_en_deepl,
                e.sentence_target_google, e.sentence_target_deepl, e.source_id, e.source_title
         FROM encounters e
         JOIN vocabulary v ON e.vocab_id = v.id
         WHERE v.lang = ?1
         AND (e.sentence_target_google IS NOT NULL OR e.sentence_target_deepl IS NOT NULL)
         ORDER BY RANDOM()
         LIMIT 50"
    ) {
        if let Ok(rows) = stmt.query_map(params![lang], |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, Option<String>>(2)?,
                row.get::<_, Option<String>>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, Option<String>>(6)?,
                row.get::<_, Option<String>>(7)?,
                row.get::<_, Option<String>>(8)?,
            ))
        }) {
            for row in rows.flatten() {
                candidates.push(row);
            }
        }
    }

    // Try candidates until we find one where the word appears in the target sentence
    for (word_id, word, sentence_zh, en_google, en_deepl, target_google, target_deepl, source_id, source_title) in &candidates {
        let word_lower = word.to_lowercase();

        // Try google first, then deepl
        let (target_sentence, engine) = if let Some(tg) = target_google {
            if tg.to_lowercase().contains(&word_lower) {
                (tg.clone(), "Google".to_string())
            } else if let Some(td) = target_deepl {
                if td.to_lowercase().contains(&word_lower) {
                    (td.clone(), "DeepL".to_string())
                } else {
                    continue;
                }
            } else {
                continue;
            }
        } else if let Some(td) = target_deepl {
            if td.to_lowercase().contains(&word_lower) {
                (td.clone(), "DeepL".to_string())
            } else {
                continue;
            }
        } else {
            continue;
        };

        // Create the blank: replace first case-insensitive occurrence with ____
        let sentence_with_blank = replace_first_case_insensitive(&target_sentence, word, "____");

        if sentence_with_blank == target_sentence {
            // Word not found (shouldn't happen after the contains check, but safety)
            continue;
        }

        // Pick the English sentence to show (prefer whichever engine matched)
        let sentence_en = if engine == "Google" {
            en_google.clone()
        } else {
            en_deepl.clone().or_else(|| en_google.clone())
        };

        // Get 3 distractor words from same language
        let mut distractors: Vec<(i64, String)> = Vec::new();
        if let Ok(mut stmt) = conn.prepare(
            "SELECT id, word FROM vocabulary WHERE lang = ?1 AND id != ?2 ORDER BY RANDOM() LIMIT 3"
        ) {
            if let Ok(rows) = stmt.query_map(params![lang, word_id], |row| {
                Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?))
            }) {
                for row in rows.flatten() {
                    distractors.push(row);
                }
            }
        }

        if distractors.len() < 3 {
            return Err("该语言词汇量不足".to_string());
        }

        // Build choices: correct word + 3 distractors, shuffled
        let mut choices: Vec<(i64, String)> = vec![(*word_id, word.clone())];
        choices.extend(distractors);

        let mut rng = rand::thread_rng();
        choices.shuffle(&mut rng);

        return Ok(FillBlankQuestion {
            sentence_zh: sentence_zh.clone(),
            sentence_en,
            sentence_target_with_blank: sentence_with_blank,
            source_title: source_title.clone(),
            source_id: source_id.clone(),
            correct_word_id: *word_id,
            correct_word: word.clone(),
            choices,
            engine,
        });
    }

    Err("no_suitable_sentence".to_string())
}

/// Replace first case-insensitive occurrence of `needle` in `haystack` with `replacement`.
/// Uses regex to correctly handle Unicode characters whose byte length changes under lowercasing.
fn replace_first_case_insensitive(haystack: &str, needle: &str, replacement: &str) -> String {
    let pattern = regex::escape(needle);
    if let Ok(re) = regex::RegexBuilder::new(&pattern)
        .case_insensitive(true)
        .build()
    {
        if let Some(m) = re.find(haystack) {
            let mut result = String::with_capacity(haystack.len());
            result.push_str(&haystack[..m.start()]);
            result.push_str(replacement);
            result.push_str(&haystack[m.end()..]);
            return result;
        }
    }
    haystack.to_string()
}

/// Submit a fill-in-the-blank answer and adjust crit_evasion for all choice words
pub fn submit_fill_blank_answer(
    conn: &Connection,
    correct_word_id: i64,
    chosen_word_id: i64,
    all_choice_ids: Vec<i64>,
    no_helper: bool,
) -> FillBlankAnswer {
    let is_correct = correct_word_id == chosen_word_id;

    let mut evasion_changes: Vec<(i64, String, f64)> = Vec::new();

    if is_correct {
        // Correct answer
        let correct_delta = if no_helper { -10.0 } else { -5.0 };
        let distractor_delta = if no_helper { -6.0 } else { -3.0 };

        for &wid in &all_choice_ids {
            let delta = if wid == correct_word_id { correct_delta } else { distractor_delta };
            let word_name = update_crit_evasion(conn, wid, delta);
            evasion_changes.push((wid, word_name, delta));
        }
    } else {
        // Wrong answer
        for &wid in &all_choice_ids {
            let delta = if wid == chosen_word_id || wid == correct_word_id {
                5.0 // wrongly chosen or missed correct
            } else {
                -3.0 // correctly not chosen
            };
            let word_name = update_crit_evasion(conn, wid, delta);
            evasion_changes.push((wid, word_name, delta));
        }
    }

    // Log fill-blank play to activity
    let fb_lang: String = conn
        .query_row("SELECT lang FROM vocabulary WHERE id = ?1", params![correct_word_id], |row| row.get(0))
        .unwrap_or_default();
    if !fb_lang.is_empty() {
        log_fillblank_played(conn, &fb_lang);
    }

    let correct_word = get_word_name(conn, correct_word_id);
    let chosen_word = get_word_name(conn, chosen_word_id);

    FillBlankAnswer {
        correct: is_correct,
        correct_word,
        chosen_word,
        chosen_word_id,
        evasion_changes,
    }
}

/// Update a word's crit_evasion by delta, return the word's name
fn update_crit_evasion(conn: &Connection, vocab_id: i64, delta: f64) -> String {
    conn.execute(
        "UPDATE vocabulary SET crit_evasion = crit_evasion + ?1 WHERE id = ?2",
        params![delta, vocab_id],
    )
    .ok();

    get_word_name(conn, vocab_id)
}

/// Get a word's display name by id
fn get_word_name(conn: &Connection, vocab_id: i64) -> String {
    conn.query_row(
        "SELECT word FROM vocabulary WHERE id = ?1",
        params![vocab_id],
        |row| row.get(0),
    )
    .unwrap_or_else(|_| "?".to_string())
}

// === Activity logging ===

fn ensure_activity_row(conn: &Connection, day: i64) {
    conn.execute(
        "INSERT OR IGNORE INTO daily_activity (day) VALUES (?1)",
        params![day],
    )
    .ok();
}

fn update_langs_used(conn: &Connection, day: i64, lang: &str) {
    let current: String = conn
        .query_row(
            "SELECT langs_used FROM daily_activity WHERE day = ?1",
            params![day],
            |row| row.get(0),
        )
        .unwrap_or_default();

    let langs: Vec<&str> = current.split(',').filter(|s| !s.is_empty()).collect();
    if !langs.contains(&lang) {
        let new_langs = if current.is_empty() {
            lang.to_string()
        } else {
            format!("{},{}", current, lang)
        };
        conn.execute(
            "UPDATE daily_activity SET langs_used = ?1 WHERE day = ?2",
            params![new_langs, day],
        )
        .ok();
    }
}

pub fn log_sentence_viewed(conn: &Connection, lang: &str) {
    let day = get_current_day(conn);
    ensure_activity_row(conn, day);
    conn.execute(
        "UPDATE daily_activity SET sentences_viewed = sentences_viewed + 1 WHERE day = ?1",
        params![day],
    )
    .ok();
    update_langs_used(conn, day, lang);
}

pub fn log_word_added(conn: &Connection, lang: &str) {
    let day = get_current_day(conn);
    ensure_activity_row(conn, day);
    conn.execute(
        "UPDATE daily_activity SET words_added = words_added + 1 WHERE day = ?1",
        params![day],
    )
    .ok();
    update_langs_used(conn, day, lang);
}

pub fn log_word_reviewed(conn: &Connection, lang: &str) {
    let day = get_current_day(conn);
    ensure_activity_row(conn, day);
    conn.execute(
        "UPDATE daily_activity SET words_reviewed = words_reviewed + 1 WHERE day = ?1",
        params![day],
    )
    .ok();
    update_langs_used(conn, day, lang);
}

pub fn log_word_graduated(conn: &Connection, lang: &str) {
    let day = get_current_day(conn);
    ensure_activity_row(conn, day);
    conn.execute(
        "UPDATE daily_activity SET words_graduated = words_graduated + 1 WHERE day = ?1",
        params![day],
    )
    .ok();
    update_langs_used(conn, day, lang);
}


pub fn log_fillblank_played(conn: &Connection, lang: &str) {
    let day = get_current_day(conn);
    ensure_activity_row(conn, day);
    conn.execute(
        "UPDATE daily_activity SET fillblanks_played = fillblanks_played + 1 WHERE day = ?1",
        params![day],
    )
    .ok();
    update_langs_used(conn, day, lang);
}

/// Get activity history for the last N days
pub fn get_activity_history(conn: &Connection, days: i64) -> Vec<DailyActivity> {
    let current_day = get_current_day(conn);
    let start_day = current_day - days;
    let mut activities = Vec::new();

    if let Ok(mut stmt) = conn.prepare(
        "SELECT day, sentences_viewed, words_added, words_reviewed, words_graduated, langs_used, fillblanks_played FROM daily_activity WHERE day >= ?1 AND day <= ?2 ORDER BY day",
    ) {
        if let Ok(rows) = stmt.query_map(params![start_day, current_day], |row| {
            Ok(DailyActivity {
                day: row.get(0)?,
                sentences_viewed: row.get(1)?,
                words_added: row.get(2)?,
                words_reviewed: row.get(3)?,
                words_graduated: row.get(4)?,
                langs_used: row.get(5)?,
                fillblanks_played: row.get(6)?,
            })
        }) {
            for row in rows.flatten() {
                activities.push(row);
            }
        }
    }

    activities
}

/// Get activity summary for the last N days
pub fn get_activity_summary(conn: &Connection, days: i64) -> ActivitySummary {
    let current_day = get_current_day(conn);
    let start_day = current_day - days;

    let result = conn.query_row(
        "SELECT COUNT(*), COALESCE(SUM(sentences_viewed), 0), COALESCE(SUM(words_added), 0), COALESCE(SUM(words_reviewed), 0), COALESCE(SUM(words_graduated), 0), COALESCE(SUM(fillblanks_played), 0) FROM daily_activity WHERE day >= ?1 AND day <= ?2 AND (sentences_viewed > 0 OR words_added > 0 OR words_reviewed > 0 OR words_graduated > 0 OR fillblanks_played > 0)",
        params![start_day, current_day],
        |row| {
            Ok(ActivitySummary {
                total_days: days,
                active_days: row.get(0)?,
                sentences_viewed: row.get(1)?,
                words_added: row.get(2)?,
                words_reviewed: row.get(3)?,
                words_graduated: row.get(4)?,
                fillblanks_played: row.get(5)?,
            })
        },
    );

    result.unwrap_or(ActivitySummary {
        total_days: days,
        active_days: 0,
        sentences_viewed: 0,
        words_added: 0,
        words_reviewed: 0,
        words_graduated: 0,
        fillblanks_played: 0,
    })
}

// === API usage tracking ===

/// Get the current month key (e.g. "2026_09")
fn current_month_key() -> String {
    let now = chrono::Local::now();
    format!("{:04}_{:02}", now.year(), now.month())
}

/// Log API characters used for an engine this month
pub fn log_api_chars(conn: &Connection, engine: &str, chars: usize) {
    if chars == 0 {
        return;
    }
    let month = current_month_key();
    let key = format!("api_chars_{}_{}", engine, month);

    // Get current value
    let current: i64 = conn
        .query_row(
            "SELECT CAST(value AS INTEGER) FROM metadata WHERE key = ?1",
            params![key],
            |row| row.get(0),
        )
        .unwrap_or(0);

    let new_val = current + chars as i64;
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?1, ?2)",
        params![key, new_val.to_string()],
    )
    .ok();
}

/// Get API usage for current month
pub fn get_api_usage(conn: &Connection) -> crate::models::ApiUsage {
    let month = current_month_key();

    let google_key = format!("api_chars_google_{}", month);
    let deepl_key = format!("api_chars_deepl_{}", month);

    let google_chars: i64 = conn
        .query_row(
            "SELECT CAST(value AS INTEGER) FROM metadata WHERE key = ?1",
            params![google_key],
            |row| row.get(0),
        )
        .unwrap_or(0);

    let deepl_chars: i64 = conn
        .query_row(
            "SELECT CAST(value AS INTEGER) FROM metadata WHERE key = ?1",
            params![deepl_key],
            |row| row.get(0),
        )
        .unwrap_or(0);

    // Format month label like "2026-09"
    let now = chrono::Local::now();
    let month_label = format!("{:04}-{:02}", now.year(), now.month());

    crate::models::ApiUsage {
        google_chars,
        deepl_chars,
        month_label,
    }
}
