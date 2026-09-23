import React, { useState, useEffect, useCallback } from "react";
import { t } from "../services/i18n";
import {
  getVocabularyList,
  getWordEncounters,
  getWordById,
  getChildren,
  decreaseHp,
  increaseHp,
  deleteWord,
  renameWord,
  searchWord,
  updateNote,
  setParent,
  addWordManual,
  logWordReviewed,
} from "../services/database";

const SORT_OPTIONS = [
  "sort_last_encounter",
  "sort_first_encounter",
  "sort_encounter_count",
  "sort_last_reviewed",
  "sort_alphabetical",
];

const SORT_KEYS = [
  "last_encounter",
  "first_encounter",
  "encounter_count",
  "last_reviewed",
  "alphabetical",
];

export default function VocabList({ lang, supportedLangs, onRefreshStats, showToast }) {
  const [words, setWords] = useState([]);
  const [filterLang, setFilterLang] = useState(null);
  const [sortBy, setSortBy] = useState("last_encounter");
  const [expandedId, setExpandedId] = useState(null);
  const [showManagement, setShowManagement] = useState(false);

  // Load word list
  const loadWords = useCallback(async () => {
    try {
      const list = await getVocabularyList(filterLang, 500, sortBy);
      setWords(list);
    } catch (e) {
      console.error("Failed to load vocabulary:", e);
    }
  }, [filterLang, sortBy]);

  useEffect(() => {
    loadWords();
  }, [loadWords]);

  // Toggle expand
  const toggleExpand = useCallback((id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  }, []);

  // Unique languages in the list
  const availLangs = [...new Set(words.map((w) => w.lang))];

  return (
    <div>
      <h1 className="page-title">{t("title_vocab", lang)}</h1>

      {/* Toolbar */}
      <div className="vocab-toolbar">
        <select
          value={filterLang || ""}
          onChange={(e) => setFilterLang(e.target.value || null)}
        >
          <option value="">{t("all_languages", lang)}</option>
          {availLangs.map((code) => (
            <option key={code} value={code}>
              {supportedLangs.find(([c]) => c === code)?.[1] || code}
            </option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          {SORT_OPTIONS.map((key, i) => (
            <option key={key} value={SORT_KEYS[i]}>
              {t(key, lang)}
            </option>
          ))}
        </select>

        <span className="vocab-count">
          {t("total_words", lang, words.length)}
        </span>
      </div>

      {/* Word list */}
      {words.length === 0 ? (
        <div className="empty-state">{t("no_words", lang)}</div>
      ) : (
        words.map((word) => (
          <WordItem
            key={word.id}
            word={word}
            expanded={expandedId === word.id}
            onToggle={() => toggleExpand(word.id)}
            lang={lang}
            supportedLangs={supportedLangs}
            onRefresh={() => { loadWords(); onRefreshStats(); }}
            showToast={showToast}
          />
        ))
      )}

      {/* Management Tools */}
      <div style={{ marginTop: 24 }}>
        <div
          className="collapsible-header"
          onClick={() => setShowManagement(!showManagement)}
        >
          <span className={`vocab-chevron ${showManagement ? "open" : ""}`}>
            ▶
          </span>
          {t("management_tools", lang)}
        </div>
        {showManagement && (
          <ManagementTools
            lang={lang}
            supportedLangs={supportedLangs}
            words={words}
            onRefresh={() => { loadWords(); onRefreshStats(); }}
            showToast={showToast}
          />
        )}
      </div>
    </div>
  );
}

// --- Word Item ---
function WordItem({ word, expanded, onToggle, lang, supportedLangs, onRefresh, showToast }) {
  const [encounters, setEncounters] = useState([]);
  const [children, setChildren] = useState([]);
  const [parentWord, setParentWord] = useState(null);
  const [editNote, setEditNote] = useState(false);
  const [noteText, setNoteText] = useState(word.note || "");
  const [showEncounters, setShowEncounters] = useState(false);

  // Load details when expanded
  useEffect(() => {
    if (!expanded) return;
    getWordEncounters(word.id).then(setEncounters).catch(console.error);
    getChildren(word.id).then(setChildren).catch(console.error);
    if (word.parent_id) {
      getWordById(word.parent_id).then(setParentWord).catch(console.error);
    }
  }, [expanded, word.id, word.parent_id]);

  const handleDecrease = async () => {
    try {
      const result = await decreaseHp(word.id);
      showToast(result.message);
      if (result.promoted) {
        showToast(t("promoted_toast", lang));
      }
      logWordReviewed(word.lang).catch(console.error);
      onRefresh();
    } catch (e) {
      showToast(String(e));
    }
  };

  const handleIncrease = async () => {
    try {
      const [ok, msg] = await increaseHp(word.id);
      showToast(msg);
      logWordReviewed(word.lang).catch(console.error);
      onRefresh();
    } catch (e) {
      showToast(String(e));
    }
  };

  const handleSaveNote = async () => {
    try {
      const [ok, msg] = await updateNote(word.id, noteText);
      showToast(t("note_saved", lang));
      setEditNote(false);
      onRefresh();
    } catch (e) {
      showToast(String(e));
    }
  };

  const langName = supportedLangs.find(([c]) => c === word.lang)?.[1] || word.lang;

  return (
    <div className="vocab-item">
      <div className="vocab-item-header" onClick={onToggle}>
        <span className={`vocab-chevron ${expanded ? "open" : ""}`}>▶</span>
        <span className="vocab-word">{word.word}</span>
        <span className="vocab-lang-badge">{langName}</span>
        <span className="vocab-hp">HP:{word.stat_hp}</span>
      </div>

      {expanded && (
        <div className="vocab-detail">
          {/* Meta info */}
          <dl className="vocab-meta">
            <dt>{t("word_entry", lang)}</dt>
            <dd>{word.word}</dd>
            <dt>{t("language_label", lang)}</dt>
            <dd>{langName}</dd>
            <dt>{t("first_seen", lang)}</dt>
            <dd>Day {word.first_seen_day}</dd>
            <dt>{t("last_seen", lang)}</dt>
            <dd>Day {word.last_encounter_day}</dd>
            <dt>{t("encounter_count", lang)}</dt>
            <dd>{word.encounter_count}</dd>
            <dt>{t("stats_hp", lang)}</dt>
            <dd>
              HP={word.stat_hp}
              {word.breakthrough > 0 && (
                <span style={{ marginLeft: 8 }}>
                  {t("breakthrough", lang)} ×{word.breakthrough}
                </span>
              )}
            </dd>
          </dl>

          {/* Parent/child links */}
          {parentWord && (
            <div style={{ marginBottom: 8, fontSize: 12 }}>
              {t("parent_word", lang)}{" "}
              <span className="parent-link">{parentWord.word}</span>
            </div>
          )}
          {children.length > 0 && (
            <div style={{ marginBottom: 8, fontSize: 12 }}>
              {t("child_words", lang)}{" "}
              {children.map((c) => (
                <span key={c.id} className="child-link" style={{ marginRight: 4 }}>
                  {c.word}
                </span>
              ))}
            </div>
          )}

          {/* HP Feedback */}
          <div className="hp-feedback">
            <button className="hp-btn familiar" onClick={handleDecrease}>
              {t("seems_familiar", lang)}
            </button>
            <button className="hp-btn unknown" onClick={handleIncrease}>
              {t("dont_know", lang)}
            </button>
          </div>

          {/* Note */}
          <div className="note-section">
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>
                {t("personal_note", lang)}
              </span>
              {!editNote && (
                <button className="btn btn-sm" onClick={() => setEditNote(true)}>
                  {t("edit_note", lang)}
                </button>
              )}
            </div>
            {editNote ? (
              <div style={{ marginTop: 6 }}>
                <textarea
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  rows={3}
                />
                <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                  <button className="btn btn-sm btn-primary" onClick={handleSaveNote}>
                    {t("save_note", lang)}
                  </button>
                  <button className="btn btn-sm" onClick={() => setEditNote(false)}>
                    {t("cancel", lang)}
                  </button>
                </div>
              </div>
            ) : (
              word.note && (
                <div style={{ fontSize: 12, marginTop: 4, color: "var(--text-secondary)" }}>
                  {word.note}
                </div>
              )
            )}
          </div>

          {/* Encounters */}
          <div style={{ marginTop: 12 }}>
            <div
              className="collapsible-header"
              onClick={() => setShowEncounters(!showEncounters)}
            >
              <span className={`vocab-chevron ${showEncounters ? "open" : ""}`}>
                ▶
              </span>
              {t("encounter_history", lang)}
            </div>
            {showEncounters && (
              <div>
                {encounters.length === 0 ? (
                  <div style={{ fontSize: 12, color: "var(--text-muted)", padding: 8 }}>
                    —
                  </div>
                ) : (
                  encounters.map((enc, i) => (
                    <div key={enc.id} className="encounter-item">
                      <div className="enc-label">
                        {t("encounter_index", lang, enc.encounter_index)}
                        {enc.day != null && ` (Day ${enc.day})`}
                      </div>
                      {enc.sentence_zh && (
                        <div>
                          {t("sentence_zh", lang)} {enc.sentence_zh}
                        </div>
                      )}
                      {enc.sentence_en_google && (
                        <div>
                          {t("translation_en", lang)} {enc.sentence_en_google}
                        </div>
                      )}
                      {enc.sentence_target_google && (
                        <div>
                          {t("translation_target", lang, word.lang)}{" "}
                          {enc.sentence_target_google}
                        </div>
                      )}
                      {enc.source_title && (
                        <div>
                          {t("source_work", lang)} {enc.source_title}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// --- Management Tools ---
function ManagementTools({ lang, supportedLangs, words, onRefresh, showToast }) {
  // Quick add
  const [qaWord, setQaWord] = useState("");
  const [qaLang, setQaLang] = useState("es");

  // Rename
  const [rnId, setRnId] = useState("");
  const [rnNew, setRnNew] = useState("");

  // Set parent
  const [spChild, setSpChild] = useState("");
  const [spParent, setSpParent] = useState("");

  // Delete
  const [delId, setDelId] = useState("");
  const [delConfirm, setDelConfirm] = useState(false);

  const handleQuickAdd = async () => {
    if (!qaWord.trim()) return;
    try {
      const result = await addWordManual(qaWord.trim(), qaLang, null);
      showToast(result.message);
      setQaWord("");
      onRefresh();
    } catch (e) {
      showToast(String(e));
    }
  };

  const handleRename = async () => {
    if (!rnId || !rnNew.trim()) return;
    try {
      const [ok, msg] = await renameWord(parseInt(rnId), rnNew.trim());
      showToast(msg);
      setRnNew("");
      onRefresh();
    } catch (e) {
      showToast(String(e));
    }
  };

  const handleSetParent = async () => {
    if (!spChild) return;
    try {
      const [ok, msg] = await setParent(
        parseInt(spChild),
        spParent ? parseInt(spParent) : null
      );
      showToast(msg);
      onRefresh();
    } catch (e) {
      showToast(String(e));
    }
  };

  const handleDelete = async () => {
    if (!delId || !delConfirm) return;
    try {
      const [ok, msg] = await deleteWord(parseInt(delId));
      showToast(msg);
      setDelId("");
      setDelConfirm(false);
      onRefresh();
    } catch (e) {
      showToast(String(e));
    }
  };

  return (
    <div>
      {/* Quick Add */}
      <div className="mgmt-section">
        <h4>{t("quick_add", lang)}</h4>
        <div className="form-row">
          <input
            type="text"
            placeholder={t("quick_add_word", lang)}
            value={qaWord}
            onChange={(e) => setQaWord(e.target.value)}
            style={{ flex: 1 }}
          />
          <select
            value={qaLang}
            onChange={(e) => setQaLang(e.target.value)}
            style={{ width: 100 }}
          >
            {supportedLangs.map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
          <button className="btn btn-primary" onClick={handleQuickAdd}>
            {t("quick_add_button", lang)}
          </button>
        </div>
      </div>

      {/* Rename */}
      <div className="mgmt-section">
        <h4>{t("rename_word", lang)}</h4>
        <div className="form-row">
          <select
            value={rnId}
            onChange={(e) => setRnId(e.target.value)}
            style={{ flex: 1 }}
          >
            <option value="">{t("old_word", lang)}</option>
            {words.map((w) => (
              <option key={w.id} value={w.id}>
                {w.word} ({w.lang})
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder={t("new_word", lang)}
            value={rnNew}
            onChange={(e) => setRnNew(e.target.value)}
            style={{ flex: 1 }}
          />
          <button className="btn" onClick={handleRename}>
            {t("rename_button", lang)}
          </button>
        </div>
      </div>

      {/* Set Parent */}
      <div className="mgmt-section">
        <h4>{t("set_parent_label", lang)}</h4>
        <div className="form-row">
          <select
            value={spChild}
            onChange={(e) => setSpChild(e.target.value)}
            style={{ flex: 1 }}
          >
            <option value="">{t("child_word", lang)}</option>
            {words.map((w) => (
              <option key={w.id} value={w.id}>
                {w.word} ({w.lang})
              </option>
            ))}
          </select>
          <select
            value={spParent}
            onChange={(e) => setSpParent(e.target.value)}
            style={{ flex: 1 }}
          >
            <option value="">{t("parent_word_select", lang)}</option>
            {words
              .filter((w) => String(w.id) !== spChild)
              .map((w) => (
                <option key={w.id} value={w.id}>
                  {w.word} ({w.lang})
                </option>
              ))}
          </select>
          <button className="btn" onClick={handleSetParent}>
            {t("set_button", lang)}
          </button>
        </div>
      </div>

      {/* Delete */}
      <div className="mgmt-section">
        <h4>{t("delete_word_label", lang)}</h4>
        <div className="form-row">
          <select
            value={delId}
            onChange={(e) => {
              setDelId(e.target.value);
              setDelConfirm(false);
            }}
            style={{ flex: 1 }}
          >
            <option value="">{t("delete_word_select", lang)}</option>
            {words.map((w) => (
              <option key={w.id} value={w.id}>
                {w.word} ({w.lang})
              </option>
            ))}
          </select>
          {delId && (
            <label className="lang-checkbox">
              <input
                type="checkbox"
                checked={delConfirm}
                onChange={(e) => setDelConfirm(e.target.checked)}
              />
              {t("confirm_delete", lang)}
            </label>
          )}
          <button
            className="btn btn-danger"
            onClick={handleDelete}
            disabled={!delId || !delConfirm}
          >
            {t("delete_button", lang)}
          </button>
        </div>
      </div>
    </div>
  );
}
