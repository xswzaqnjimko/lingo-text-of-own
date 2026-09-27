import React, { useState, useEffect } from "react";
import { t } from "../services/i18n";
import {
  getFillBlankEligibleLangs,
  getFillBlankQuestion,
  submitFillBlankAnswer,
} from "../services/database";

export default function FillBlank({ lang, supportedLangs, showToast, onJumpToWord }) {
  const [eligibleLangs, setEligibleLangs] = useState([]);
  const [selectedLang, setSelectedLang] = useState("");
  const [question, setQuestion] = useState(null);
  const [answered, setAnswered] = useState(false);
  const [result, setResult] = useState(null);
  const [noHelper, setNoHelper] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load eligible languages on mount
  useEffect(() => {
    getFillBlankEligibleLangs()
      .then((langs) => {
        setEligibleLangs(langs);
        if (langs.length > 0 && !selectedLang) {
          setSelectedLang(langs[0][0]);
        }
      })
      .catch(console.error);
  }, []);

  const getLangName = (code) => {
    const found = supportedLangs.find(([c]) => c === code);
    return found ? found[1] : code;
  };

  const handleDraw = async () => {
    if (!selectedLang) return;
    setLoading(true);
    setQuestion(null);
    setAnswered(false);
    setResult(null);
    try {
      const q = await getFillBlankQuestion(selectedLang);
      setQuestion(q);
    } catch (e) {
      const errStr = String(e);
      if (errStr.includes("no_suitable_sentence")) {
        showToast(t("fillblank_no_sentence", lang));
      } else {
        showToast(errStr);
      }
    }
    setLoading(false);
  };

  const handleChoice = async (chosenId, chosenWord) => {
    if (answered) return;
    setAnswered(true);
    try {
      const allIds = question.choices.map(([id]) => id);
      const res = await submitFillBlankAnswer(
        question.correct_word_id,
        chosenId,
        allIds,
        noHelper
      );
      setResult(res);
      if (res.correct) {
        showToast(t("fillblank_correct", lang));
      } else {
        showToast(t("fillblank_wrong", lang, res.correct_word));
      }
    } catch (e) {
      showToast(String(e));
    }
  };

  return (
    <div style={{ padding: "16px 0" }}>
      <h2 style={{ marginBottom: 16 }}>{t("fillblank_title", lang)}</h2>

      {/* Controls row */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        {/* Language selector */}
        <select
          value={selectedLang}
          onChange={(e) => {
            setSelectedLang(e.target.value);
            setQuestion(null);
            setAnswered(false);
            setResult(null);
          }}
          style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid var(--border)", background: "var(--bg-card)", color: "var(--text)" }}
        >
          <option value="" disabled>
            {t("fillblank_select_lang", lang)}
          </option>
          {supportedLangs.map(([code, name]) => {
            const eligible = eligibleLangs.find(([c]) => c === code);
            return (
              <option key={code} value={code} disabled={!eligible}>
                {name} {eligible ? `(${eligible[1]})` : `— ${t("fillblank_lang_not_eligible", lang)}`}
              </option>
            );
          })}
        </select>

        {/* Draw button */}
        <button
          className="btn-primary"
          onClick={handleDraw}
          disabled={!selectedLang || loading || !eligibleLangs.find(([c]) => c === selectedLang)}
          style={{ padding: "6px 16px", borderRadius: 6, fontWeight: 600 }}
        >
          {t("fillblank_draw", lang)}
        </button>

        {/* Mode toggle */}
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={noHelper}
            onChange={(e) => setNoHelper(e.target.checked)}
          />
          <span style={{ color: noHelper ? "var(--accent)" : "var(--text-muted)" }}>
            {t("fillblank_mode_hint", lang)}
          </span>
        </label>
      </div>

      {/* Question card */}
      {question && (
        <div className="fillblank-card">
          {/* Context (only in 有提示 mode) */}
          {!noHelper && (
            <div className="fillblank-context">
              {question.sentence_zh && (
                <div style={{ marginBottom: 6 }}>
                  <span className="fillblank-label">{t("sentence_zh", lang)}</span> {question.sentence_zh}
                </div>
              )}
              {question.sentence_en && (
                <div style={{ marginBottom: 6 }}>
                  <span className="fillblank-label">{t("translation_en", lang)}</span> {question.sentence_en}
                </div>
              )}
            </div>
          )}

          {/* Target sentence with blank */}
          <div className="fillblank-sentence">
            {question.sentence_target_with_blank}
          </div>

          {/* Source (only in 有提示 mode) */}
          {!noHelper && question.source_title && (
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
              {t("fillblank_source", lang)} {question.source_title}
            </div>
          )}

          {/* Choices */}
          <div className="fillblank-choices">
            {question.choices.map(([id, word]) => {
              let btnClass = "fillblank-choice";
              if (answered) {
                if (id === question.correct_word_id) {
                  btnClass += " correct";
                } else if (result && id === result.chosen_word_id) {
                  btnClass += " wrong";
                }
              }
              return (
                <span key={id} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <button
                    className={btnClass}
                    onClick={() => handleChoice(id, word)}
                    disabled={answered}
                  >
                    {word}
                  </button>
                  {answered && onJumpToWord && (
                    <button
                      className="fillblank-jump-btn"
                      onClick={() => onJumpToWord(id)}
                      title={word}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        fontSize: 14,
                        padding: "2px 4px",
                        opacity: 0.7,
                      }}
                    >
                      {t("fillblank_check_word", lang)}
                    </button>
                  )}
                </span>
              );
            })}
          </div>

          {/* Result */}
          {result && (
            <div className="fillblank-result" style={{ marginTop: 12 }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>
                {result.correct ? t("fillblank_correct", lang) : t("fillblank_wrong", lang, result.correct_word)}
              </div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                <span>{t("fillblank_evasion_title", lang)}</span>
                {result.evasion_changes.map(([id, word, delta]) => (
                  <span key={id} style={{ marginLeft: 8, color: delta < 0 ? "var(--success)" : "var(--danger)" }}>
                    {word} {delta > 0 ? "+" : ""}{delta}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
