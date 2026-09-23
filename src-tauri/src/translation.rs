use regex::Regex;
use std::collections::HashMap;

use crate::models::EngineTranslations;

/// Translate text using Google Cloud Translation API v2
pub fn google_translate(
    text: &str,
    source_lang: &str,
    target_lang: &str,
    api_key: &str,
) -> Result<String, String> {
    if api_key.is_empty() {
        return Err("Google 未配置密钥".to_string());
    }

    let client = reqwest::blocking::Client::new();
    let params = [
        ("q", text),
        ("source", source_lang),
        ("target", target_lang),
        ("key", api_key),
        ("format", "text"),
    ];

    let resp = client
        .post("https://translation.googleapis.com/language/translate/v2")
        .form(&params)
        .timeout(std::time::Duration::from_secs(20))
        .send()
        .map_err(|e| format!("Google 调用失败：{}", e))?;

    let json: serde_json::Value = resp
        .json()
        .map_err(|e| format!("Google 解析失败：{}", e))?;

    json["data"]["translations"][0]["translatedText"]
        .as_str()
        .map(|s| s.to_string())
        .ok_or_else(|| "Google 返回格式异常".to_string())
}

/// Translate text using DeepL API (free tier)
pub fn deepl_translate(
    text: &str,
    source_lang: &str,
    target_lang: &str,
    api_key: &str,
) -> Result<String, String> {
    if api_key.is_empty() {
        return Err("DeepL 未配置密钥".to_string());
    }

    let client = reqwest::blocking::Client::new();
    let params = [
        ("text", text),
        ("source_lang", &source_lang.to_uppercase()),
        ("target_lang", &target_lang.to_uppercase()),
    ];

    let resp = client
        .post("https://api-free.deepl.com/v2/translate")
        .header("Authorization", format!("DeepL-Auth-Key {}", api_key))
        .form(&params)
        .timeout(std::time::Duration::from_secs(20))
        .send()
        .map_err(|e| format!("DeepL 调用失败：{}", e))?;

    let json: serde_json::Value = resp
        .json()
        .map_err(|e| format!("DeepL 解析失败：{}", e))?;

    json["translations"][0]["text"]
        .as_str()
        .map(|s| s.to_string())
        .ok_or_else(|| "DeepL 返回格式异常".to_string())
}

/// Translate a Chinese sentence to English and target languages
/// Returns: { "en": { google, deepl }, "es": { google, deepl }, ... }
pub fn translate_sentence(
    sentence: &str,
    target_langs: &[String],
    google_key: &str,
    deepl_key: &str,
) -> HashMap<String, EngineTranslations> {
    let mut results = HashMap::new();

    // Step 1: Chinese -> English
    let google_en = google_translate(sentence, "zh-CN", "en", google_key)
        .unwrap_or_else(|e| format!("({})", e));
    let deepl_en = deepl_translate(sentence, "zh", "en", deepl_key)
        .unwrap_or_else(|e| format!("({})", e));

    results.insert(
        "en".to_string(),
        EngineTranslations {
            google: Some(google_en.clone()),
            deepl: Some(deepl_en.clone()),
        },
    );

    // Step 2: English -> each target language
    for lang in target_langs {
        let google_target = google_translate(&google_en, "en", lang, google_key)
            .unwrap_or_else(|e| format!("({})", e));
        let deepl_target = deepl_translate(&deepl_en, "en", lang, deepl_key)
            .unwrap_or_else(|e| format!("({})", e));

        results.insert(
            lang.clone(),
            EngineTranslations {
                google: Some(google_target),
                deepl: Some(deepl_target),
            },
        );
    }

    results
}

// === Dictionary and TTS link generation ===

/// Language-specific configuration
pub struct LangConfig {
    pub name: &'static str,
    pub name_en: &'static str,
    pub dict_url: &'static str,
    pub word_pattern: &'static str,
    pub tts_google_template: &'static str,
    pub tts_deepl_template: &'static str,
}

/// Get language configuration
pub fn get_lang_config(code: &str) -> Option<LangConfig> {
    match code {
        "es" => Some(LangConfig {
            name: "西语",
            name_en: "Spanish",
            dict_url: "https://www.ingles.com/traductor/",
            word_pattern: r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+",
            tts_google_template: "https://translate.google.com/?sl=es&tl=en&text={}&op=translate",
            tts_deepl_template: "https://www.deepl.com/translator#es/en/{}",
        }),
        "fr" => Some(LangConfig {
            name: "法语",
            name_en: "French",
            dict_url: "https://dictionnaire.lerobert.com/definition/",
            word_pattern: r"[A-Za-zÀ-ÿÇçŒœ]+",
            tts_google_template: "https://translate.google.com/?sl=fr&tl=en&text={}&op=translate",
            tts_deepl_template: "https://www.deepl.com/translator#fr/en/{}",
        }),
        "it" => Some(LangConfig {
            name: "意大利语",
            name_en: "Italian",
            dict_url: "https://dizionari.corriere.it/dizionario_italiano/",
            word_pattern: r"[A-Za-zÀÈÉÌÒÙàèéìòù]+",
            tts_google_template: "https://translate.google.com/?sl=it&tl=en&text={}&op=translate",
            tts_deepl_template: "https://www.deepl.com/translator#it/en/{}",
        }),
        _ => None,
    }
}

/// Get all supported language codes and names
pub fn get_supported_languages() -> Vec<(String, String, String)> {
    vec![
        ("es".to_string(), "西语".to_string(), "Spanish".to_string()),
        ("fr".to_string(), "法语".to_string(), "French".to_string()),
        (
            "it".to_string(),
            "意大利语".to_string(),
            "Italian".to_string(),
        ),
    ]
}

/// Extract words from text using a language-specific pattern
pub fn extract_words(text: &str, pattern: &str) -> Vec<String> {
    let cleaned = text
        .replace('¿', "")
        .replace('¡', "")
        .replace('?', "")
        .replace('!', "");
    let re = Regex::new(pattern).unwrap_or_else(|_| Regex::new(r"[A-Za-z]+").unwrap());
    re.find_iter(&cleaned)
        .map(|m| m.as_str().to_string())
        .collect()
}

/// Generate dictionary links for words in translation
pub fn generate_dictionary_links(
    google_text: &str,
    deepl_text: &str,
    lang_code: &str,
) -> (Vec<(String, String)>, Vec<(String, String)>) {
    let config = match get_lang_config(lang_code) {
        Some(c) => c,
        None => return (Vec::new(), Vec::new()),
    };

    let google_words = extract_words(google_text, config.word_pattern);
    let google_words_lower: std::collections::HashSet<String> =
        google_words.iter().map(|w| w.to_lowercase()).collect();

    let google_chips: Vec<(String, String)> = google_words
        .iter()
        .map(|word| {
            let url = format!(
                "{}{}",
                config.dict_url,
                urlencoding::encode(&word.to_lowercase())
            );
            (word.clone(), url)
        })
        .collect();

    let deepl_words = extract_words(deepl_text, config.word_pattern);
    let deepl_extra: Vec<(String, String)> = deepl_words
        .iter()
        .filter(|w| !google_words_lower.contains(&w.to_lowercase()))
        .map(|word| {
            let url = format!(
                "{}{}",
                config.dict_url,
                urlencoding::encode(&word.to_lowercase())
            );
            (word.clone(), url)
        })
        .collect();

    (google_chips, deepl_extra)
}

/// Generate TTS link
pub fn get_tts_link(text: &str, lang_code: &str, engine: &str) -> Option<String> {
    let config = get_lang_config(lang_code)?;
    let encoded = urlencoding::encode(text);

    match engine {
        "google" => Some(config.tts_google_template.replace("{}", &encoded)),
        "deepl" => Some(config.tts_deepl_template.replace("{}", &encoded)),
        _ => None,
    }
}
