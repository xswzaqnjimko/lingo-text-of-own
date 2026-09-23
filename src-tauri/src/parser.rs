use regex::Regex;
use scraper::{Html, Selector};
use std::path::Path;
use unicode_normalization::UnicodeNormalization;

use crate::models::{SeriesInfo, WorkMeta};

/// Regex for Chinese sentence splitting
/// Matches: content + sentence-ending punctuation + optional closing quotes/brackets
fn split_chinese_sentences(text: &str) -> Vec<String> {
    let re = Regex::new(r#".+?(?:[。！？]|……)(?:[」』"\u{3009}》）\)\]]+)?"#).unwrap();
    re.find_iter(text)
        .map(|m| m.as_str().trim().to_string())
        .filter(|s| !s.is_empty())
        .collect()
}

/// Check if a filename matches AO3 official download format: {id}.html
fn is_ao3_official(filename: &str) -> bool {
    let re = Regex::new(r"^\d+\.html$").unwrap();
    re.is_match(filename)
}

/// Extract work ID from filename (e.g., "12345.html" -> "12345")
fn extract_work_id(filename: &str) -> Option<String> {
    let re = Regex::new(r"^(\d+)\.html$").unwrap();
    re.captures(filename).map(|c| c[1].to_string())
}

/// Clean text: normalize whitespace, remove excess
fn clean_text(text: &str) -> String {
    let text = html_escape::decode_html_entities(text);
    // Collapse horizontal whitespace
    let re_spaces = Regex::new(r"[ \t]+").unwrap();
    let text = re_spaces.replace_all(&text, " ");
    // Replace fullwidth space
    let text = text.replace('\u{3000}', " ");
    // Collapse whitespace around newlines
    let re_newlines = Regex::new(r"\s*\n\s*").unwrap();
    let text = re_newlines.replace_all(&text, "\n");
    text.trim().to_string()
}

/// Names/dirs to skip during scanning
const SKIP_NAMES: &[&str] = &["navigate.html"];
const SKIP_DIRS: &[&str] = &["index_raw", "series", "assets"];

/// Parse an AO3 official HTML file and extract metadata + sentences
pub fn parse_ao3_html(path: &Path) -> Option<(WorkMeta, Vec<String>)> {
    let filename = path.file_name()?.to_str()?;

    // Only accept {id}.html format
    if !is_ao3_official(filename) {
        return None;
    }

    // Skip helper files
    if SKIP_NAMES.contains(&filename) {
        return None;
    }

    // Skip certain directories
    for component in path.components() {
        if let std::path::Component::Normal(os_str) = component {
            if let Some(name) = os_str.to_str() {
                if SKIP_DIRS.contains(&name) {
                    return None;
                }
            }
        }
    }

    let html_content = std::fs::read_to_string(path).ok()?;
    let document = Html::parse_document(&html_content);

    let work_id = extract_work_id(filename);

    // Extract title from <h1> or <title>
    let title = extract_title(&document).unwrap_or_else(|| {
        path.file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("untitled")
            .to_string()
    });

    // Extract metadata from <dl class="tags">
    let (relationships, published, updated, series) = extract_meta_from_dl(&document);

    // Extract body text and split into sentences
    let body_text = extract_body_text(&document);
    let cleaned = clean_text(&body_text);
    let sentences = split_chinese_sentences(&cleaned);

    let meta = WorkMeta {
        work_id,
        title,
        relationships,
        published,
        updated,
        series,
        file_path: path.to_string_lossy().to_string(),
        sentence_count: sentences.len(),
    };

    Some((meta, sentences))
}

/// Extract title from HTML
fn extract_title(doc: &Html) -> Option<String> {
    // Try <h1> first
    let h1_sel = Selector::parse("h1").ok()?;
    if let Some(h1) = doc.select(&h1_sel).next() {
        let text = h1.text().collect::<String>().trim().to_string();
        if !text.is_empty() {
            return Some(text);
        }
    }

    // Fall back to <title>
    let title_sel = Selector::parse("title").ok()?;
    if let Some(title_el) = doc.select(&title_sel).next() {
        let text = title_el.text().collect::<String>();
        // <title> format: "标题 - 作者 - 原作"
        let first_part = text.split(" - ").next().unwrap_or("").trim().to_string();
        if !first_part.is_empty() {
            return Some(first_part);
        }
    }

    None
}

/// Extract metadata from <dl class="tags">
fn extract_meta_from_dl(doc: &Html) -> (Vec<String>, Option<String>, Option<String>, Vec<SeriesInfo>) {
    let mut relationships = Vec::new();
    let mut published = None;
    let mut updated = None;
    let mut series = Vec::new();

    let dl_sel = Selector::parse("dl.tags").unwrap();
    let dt_sel = Selector::parse("dt").unwrap();
    let dd_sel = Selector::parse("dd").unwrap();
    let a_sel = Selector::parse("a").unwrap();

    if let Some(dl) = doc.select(&dl_sel).next() {
        let dts: Vec<_> = dl.select(&dt_sel).collect();
        let dds: Vec<_> = dl.select(&dd_sel).collect();

        for (dt, dd) in dts.iter().zip(dds.iter()) {
            let label = dt
                .text()
                .collect::<String>()
                .trim()
                .to_lowercase()
                .trim_end_matches(':')
                .to_string();

            match label.as_str() {
                "relationships" | "relationship" => {
                    let links: Vec<String> = dd
                        .select(&a_sel)
                        .map(|a| a.text().collect::<String>().trim().to_string())
                        .filter(|s| !s.is_empty())
                        .collect();
                    if links.is_empty() {
                        // Fallback: comma-separated text
                        let raw = dd.text().collect::<String>();
                        relationships = raw
                            .split(',')
                            .map(|s| s.trim().to_string())
                            .filter(|s| !s.is_empty())
                            .collect();
                    } else {
                        relationships = links;
                    }
                }
                "series" => {
                    for a in dd.select(&a_sel) {
                        let title = a.text().collect::<String>().trim().to_string();
                        let href = a.value().attr("href").map(|s| s.to_string());
                        if !title.is_empty() {
                            series.push(SeriesInfo { title, href });
                        }
                    }
                }
                "stats" => {
                    let stats_text = dd.text().collect::<String>();
                    let pub_re = Regex::new(r"Published:\s*(\d{4}-\d{2}-\d{2})").unwrap();
                    let upd_re =
                        Regex::new(r"(?:Updated|Completed):\s*(\d{4}-\d{2}-\d{2})").unwrap();
                    if let Some(cap) = pub_re.captures(&stats_text) {
                        published = Some(cap[1].to_string());
                    }
                    if let Some(cap) = upd_re.captures(&stats_text) {
                        updated = Some(cap[1].to_string());
                    }
                }
                _ => {}
            }
        }
    }

    (relationships, published, updated, series)
}

/// Extract body text from HTML (chapters or userstuff divs)
fn extract_body_text(doc: &Html) -> String {
    // Try <div id="chapters"> first
    let chapters_sel = Selector::parse("div#chapters").unwrap();
    if let Some(chapters) = doc.select(&chapters_sel).next() {
        return chapters.text().collect::<Vec<_>>().join("\n");
    }

    // Fall back to <div class="userstuff">
    let userstuff_sel = Selector::parse("div.userstuff").unwrap();
    let blocks: Vec<String> = doc
        .select(&userstuff_sel)
        .map(|el| el.text().collect::<Vec<_>>().join("\n"))
        .collect();

    if !blocks.is_empty() {
        return blocks.join("\n");
    }

    // Last resort: full document text
    doc.root_element().text().collect::<Vec<_>>().join("\n")
}

/// Scan a directory for AO3 HTML files
pub fn scan_library(root_dir: &str) -> (Vec<(WorkMeta, Vec<String>)>, usize) {
    let root = Path::new(root_dir);
    if !root.exists() {
        return (Vec::new(), 0);
    }

    let mut results = Vec::new();
    let mut scanned = 0;

    fn walk_dir(dir: &Path, results: &mut Vec<(WorkMeta, Vec<String>)>, scanned: &mut usize) {
        let entries = match std::fs::read_dir(dir) {
            Ok(e) => e,
            Err(_) => return,
        };

        for entry in entries.flatten() {
            let path = entry.path();

            if path.is_dir() {
                // Check if this directory should be skipped
                let dir_name = path
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("");
                if !SKIP_DIRS.contains(&dir_name) {
                    walk_dir(&path, results, scanned);
                }
            } else if path.extension().and_then(|e| e.to_str()) == Some("html") {
                *scanned += 1;
                if let Some(parsed) = parse_ao3_html(&path) {
                    results.push(parsed);
                }
            }
        }
    }

    walk_dir(root, &mut results, &mut scanned);
    (results, scanned)
}

// === Relationship filtering (port of ao3_parser.py's filter logic) ===

/// Normalize a string for matching: NFKC + casefold + collapse whitespace
pub fn norm_for_match(s: &str) -> String {
    let normalized: String = s.nfkc().collect();
    // Remove zero-width characters and BOM
    let cleaned = normalized
        .replace('\u{200b}', "")
        .replace('\u{200c}', "")
        .replace('\u{200d}', "")
        .replace('\u{feff}', "")
        .replace('\u{00a0}', " ")
        .replace('\u{202f}', " ");
    let lowered = cleaned.to_lowercase();
    // Collapse whitespace
    let re = Regex::new(r"\s+").unwrap();
    re.replace_all(&lowered, " ").trim().to_string()
}

/// Strip "implied" prefixes/suffixes from relationship tags
fn strip_implied(rel: &str) -> String {
    let re_prefix = Regex::new(r"^(implied|suggested|background)\s*[:\-–—]?\s*").unwrap();
    let re_suffix = Regex::new(r"\s*\((implied|suggested|background)\)\s*$").unwrap();
    let cleaned = re_prefix.replace(rel, "");
    re_suffix.replace(&cleaned, "").trim().to_string()
}

/// Filter works by relationship matching
pub fn filter_by_relationship(
    works: &[(WorkMeta, Vec<String>)],
    target_rels: &[String],
) -> Vec<usize> {
    if target_rels.is_empty() {
        return (0..works.len()).collect();
    }

    let target_norms: Vec<String> = target_rels.iter().map(|t| norm_for_match(t)).collect();
    let target_patterns: Vec<String> = target_rels.iter().map(|t| t.to_lowercase()).collect();

    let mut matched_indices = Vec::new();

    for (i, (meta, _sentences)) in works.iter().enumerate() {
        // 1) Check relationships list
        let rels_norm: Vec<String> = meta
            .relationships
            .iter()
            .map(|r| strip_implied(&norm_for_match(r)))
            .collect();

        if rels_norm.iter().any(|r| target_norms.contains(r)) {
            matched_indices.push(i);
            continue;
        }

        // 2) Fallback: full-text substring match
        let file_text = meta.file_path.to_lowercase();
        let title_text = meta.title.to_lowercase();
        let blob = format!("{} {}", title_text, file_text);
        let blob_norm = norm_for_match(&blob);

        if target_patterns.iter().any(|p| blob_norm.contains(p)) {
            matched_indices.push(i);
        }
    }

    matched_indices
}
