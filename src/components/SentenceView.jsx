import React, { useState, useCallback, useEffect } from "react";
import { openUrl } from "@tauri-apps/plugin-opener";
import { t } from "../services/i18n";
import {
  getRandomSentence,
  translateSentence,
  getDictionaryLinks,
  getTtsLink,
  addWord,
  logSentenceViewed,
  getEligibleCount,
  getLibraryStats,
  logWordAdded,
  getApiUsage,
} from "../services/database";

export default function SentenceView({
  settings,
  lang,
  supportedLangs,
  onRefreshStats,
  showToast,
  sentence,
  setSentence,
  translations,
  setTranslations,
  dictLinks,
  setDictLinks,
}) {
  const [loading, setLoading] = useState(false);
  const [wordInputs, setWordInputs] = useState({});

  const { selectedLangs, showComparison, googleApiKey, deeplApiKey, targetRelationships } = settings;

  // Pool info: eligible / total works
  const [poolInfo, setPoolInfo] = useState(null);
  const [apiUsage, setApiUsage] = useState(null);

  useEffect(() => {
    const randomAny = !targetRelationships || targetRelationships.length === 0;
    Promise.all([
      getEligibleCount(targetRelationships || [], randomAny),
      getLibraryStats(),
    ])
      .then(([[eligible, total], stats]) =>
        setPoolInfo({ eligible, total, totalSentences: stats.total_sentences })
      )
      .catch(console.error);

    getApiUsage()
      .then(setApiUsage)
      .catch(console.error);
  }, [targetRelationships]);

  // Draw a random sentence
  const drawSentence = useCallback(async () => {
    setLoading(true);
    setTranslations(null);
    setDictLinks({});
    setWordInputs({});

    try {
      const sent = await getRandomSentence(
        targetRelationships || [],
        !targetRelationships || targetRelationships.length === 0
      );
      setSentence(sent);

      // Log activity for first selected lang
      if (selectedLangs.length > 0) {
        logSentenceViewed(selectedLangs[0]).catch(console.error);
      }

      // Translate
      const result = await translateSentence(
        sent.text,
        selectedLangs,
        googleApiKey || "",
        deeplApiKey || ""
      );
      setTranslations(result);

      // Get dictionary links for each target language
      const links = {};
      for (const langCode of selectedLangs) {
        if (result[langCode]) {
          try {
            const [gLinks, dLinks] = await getDictionaryLinks(
              result[langCode].google || "",
              result[langCode].deepl || "",
              langCode
            );
            links[langCode] = { google: gLinks, deepl: dLinks };
          } catch (e) {
            console.error("Dict links error:", e);
          }
        }
      }
      setDictLinks(links);
    } catch (e) {
      console.error("Draw sentence error:", e);
      showToast(t("error_api", lang) + String(e));
    } finally {
      setLoading(false);
      // Refresh API usage after translation
      getApiUsage().then(setApiUsage).catch(console.error);
    }
  }, [selectedLangs, showComparison, googleApiKey, deeplApiKey, targetRelationships, lang, showToast]);

  // Add word to vocabulary
  const handleAddWord = useCallback(
    async (langCode) => {
      const word = (wordInputs[langCode] || "").trim();
      if (!word || !sentence || !translations) return;

      const enTrans = translations["en"] || {};
      const tgtTrans = translations[langCode] || {};

      try {
        const result = await addWord(
          word,
          langCode,
          sentence.text,
          enTrans.google || "",
          enTrans.deepl || "",
          tgtTrans.google || "",
          tgtTrans.deepl || "",
          sentence.work_id || null,
          sentence.work_title || null,
          (sentence.relationships || []).join(", ") || null
        );
        showToast(result.message);
        logWordAdded(langCode).catch(console.error);
        setWordInputs((prev) => ({ ...prev, [langCode]: "" }));
        onRefreshStats();
      } catch (e) {
        showToast(t("error_api", lang) + String(e));
      }
    },
    [wordInputs, sentence, translations, lang, showToast, onRefreshStats]
  );

  // Open TTS link
  const openTts = useCallback(async (text, langCode, engine) => {
    try {
      const link = await getTtsLink(text, langCode, engine);
      if (link) {
        openUrl(link);
      }
    } catch (e) {
      console.error("TTS error:", e);
    }
  }, []);

  return (
    <div>
      <h1 className="page-title">{t("title_home", lang)}</h1>

      {/* Pool info */}
      {poolInfo && (
        <p className="form-hint" style={{ marginBottom: 8 }}>
          {t("pool_info", lang, poolInfo.eligible, poolInfo.total)}
          {poolInfo.totalSentences != null && (
            <span style={{ marginLeft: 8 }}>
              {t("pool_sentences", lang, poolInfo.totalSentences)}
            </span>
          )}
        </p>
      )}

      {/* API usage */}
      {apiUsage && (apiUsage.google_chars > 0 || apiUsage.deepl_chars > 0) && (
        <p className="form-hint" style={{ marginBottom: 8, fontSize: 11, opacity: 0.7 }}>
          {t("api_usage", lang,
            apiUsage.google_chars >= 1000
              ? Math.round(apiUsage.google_chars / 1000) + "k"
              : String(apiUsage.google_chars),
            apiUsage.deepl_chars >= 1000
              ? Math.round(apiUsage.deepl_chars / 1000) + "k"
              : String(apiUsage.deepl_chars)
          )}
        </p>
      )}

      {/* Draw Button */}
      <button
        className="btn btn-primary btn-lg"
        onClick={drawSentence}
        disabled={loading}
        style={{ marginBottom: 20 }}
      >
        {loading ? "..." : t("draw_sentence", lang)}
      </button>

      {sentence && (
        <>
          {/* Original Chinese sentence */}
          <div className="card">
            <div className="card-label">{t("original_sentence", lang)}</div>
            <div className="sentence-text zh">{sentence.text}</div>
          </div>

          {/* English translation (always shown as reference) */}
          {translations && translations["en"] && (
            <div className="card">
              <div className="card-label">{t("english_translation", lang)}</div>
              {renderTranslation(
                translations["en"],
                "en",
                showComparison,
                openTts,
                lang,
                null
              )}
            </div>
          )}

          {/* Target language translations */}
          {translations &&
            selectedLangs.map((langCode) => {
              if (langCode === "en") return null;
              const trans = translations[langCode];
              if (!trans) return null;

              const langName =
                supportedLangs.find(([code]) => code === langCode)?.[1] || langCode;
              const links = dictLinks[langCode];

              return (
                <div className="card" key={langCode}>
                  <div className="card-label">{langName}</div>

                  {renderTranslation(
                    trans,
                    langCode,
                    showComparison,
                    openTts,
                    lang,
                    links
                  )}

                  {/* Word input */}
                  <div style={{ marginTop: 12 }}>
                    <div className="card-label">
                      {t("add_to_vocab", lang, langName)}
                    </div>
                    <div className="word-input-row">
                      <input
                        type="text"
                        placeholder={t("word_input_placeholder", lang)}
                        value={wordInputs[langCode] || ""}
                        onChange={(e) =>
                          setWordInputs((prev) => ({
                            ...prev,
                            [langCode]: e.target.value,
                          }))
                        }
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleAddWord(langCode);
                        }}
                      />
                      <button
                        className="btn btn-primary"
                        onClick={() => handleAddWord(langCode)}
                      >
                        {t("add_button", lang)}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}

          {/* Work info */}
          {settings.enableAo3 && sentence.work_id && (
            <WorkInfo sentence={sentence} lang={lang} />
          )}
        </>
      )}
    </div>
  );
}

// --- Sub-components ---

function renderTranslation(trans, langCode, showComparison, openTts, uiLang, dictLinksForLang) {
  const showBoth = showComparison && trans.google && trans.deepl;

  return (
    <div>
      {showBoth ? (
        <>
          <TransBlock
            label={t("translation_google", uiLang)}
            text={trans.google}
            langCode={langCode}
            engine="google"
            openTts={openTts}
            uiLang={uiLang}
            dictLinks={dictLinksForLang?.google}
          />
          <TransBlock
            label={t("translation_deepl", uiLang)}
            text={trans.deepl}
            langCode={langCode}
            engine="deepl"
            openTts={openTts}
            uiLang={uiLang}
            dictLinks={dictLinksForLang?.deepl}
          />
        </>
      ) : (
        <TransBlock
          label={null}
          text={trans.google || trans.deepl || ""}
          langCode={langCode}
          engine={trans.google ? "google" : "deepl"}
          openTts={openTts}
          uiLang={uiLang}
          dictLinks={dictLinksForLang?.google || dictLinksForLang?.deepl}
        />
      )}
    </div>
  );
}

function TransBlock({ label, text, langCode, engine, openTts, uiLang, dictLinks }) {
  if (!text) return null;
  return (
    <div className="translation-section">
      {label && (
        <div className="translation-label">
          <span>{label}</span>
          <button
            className="tts-btn"
            onClick={() => openTts(text, langCode, engine)}
            title={t("play_audio_hint", uiLang, engine)}
          >
            {t("play_audio", uiLang)}
          </button>
        </div>
      )}
      <div className="translation-text">{text}</div>

      {dictLinks && dictLinks.length > 0 && (
        <>
          <div className="card-label" style={{ marginTop: 8, marginBottom: 4 }}>{t("dict_link", uiLang)}</div>
          <div className="dict-chips">
          {dictLinks.map(([word, url], i) => (
            <a
              key={i}
              className="dict-chip"
              href={url}
              onClick={(e) => { e.preventDefault(); openUrl(url); }}
            >
              {word}
            </a>
          ))}
        </div>
        </>
      )}
    </div>
  );
}

function WorkInfo({ sentence, lang }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card">
      <div
        className="collapsible-header"
        onClick={() => setOpen(!open)}
      >
        <span className={`vocab-chevron ${open ? "open" : ""}`}>▶</span>
        {t("work_info", lang)}
      </div>
      {open && (
        <div className="work-info">
          <div>
            {t("work_title", lang)} {sentence.work_title}
          </div>
          {sentence.work_id && (
            <div>
              {t("work_id_label", lang)} {sentence.work_id}
            </div>
          )}
          {sentence.published && (
            <div>
              {t("work_published", lang)} {sentence.published}
            </div>
          )}
          {sentence.updated && (
            <div>
              {t("work_updated", lang)} {sentence.updated}
            </div>
          )}
          {sentence.series && sentence.series.length > 0 && (
            <div>
              {t("work_series", lang)}{" "}
              {sentence.series.map((s) => s.title).join(", ")}
            </div>
          )}
          {sentence.work_id && (
            <div>
              <a
                href={`https://archiveofourown.org/works/${sentence.work_id}`}
                onClick={(e) => { e.preventDefault(); openUrl(`https://archiveofourown.org/works/${sentence.work_id}`); }}
              >
                {t("ao3_link", lang)}
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
