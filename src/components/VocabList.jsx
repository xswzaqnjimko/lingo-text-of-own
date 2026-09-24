import React, { useState, useEffect, useCallback, useRef, useMemo } from "react";
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

const ITEMS_PER_PAGE = 50;
const ENC_PER_PAGE = 5;
const SEARCH_MAX_DROPDOWN = 8;

// --- Pagination Component ---
function Pagination({ currentPage, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  const getPageNumbers = () => {
    const pages = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push("...");
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (currentPage < totalPages - 2) pages.push("...");
      pages.push(totalPages);
    }
    return pages;
  };

  return (
    <div className="pagination">
      <button
        className="page-btn"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        ‹
      </button>
      {getPageNumbers().map((p, i) =>
        p === "..." ? (
          <span key={`dots-${i}`} className="page-btn dots">…</span>
        ) : (
          <button
            key={p}
            className={`page-btn${p === currentPage ? " active" : ""}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        )
      )}
      <button
        className="page-btn"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        ›
      </button>
    </div>
  );
}

// --- Scroll Buttons ---
function ScrollButtons() {
  const scrollTo = (position) => {
    const el = document.querySelector(".main-content");
    if (el) {
      if (position === "top") el.scrollTo({ top: 0, behavior: "smooth" });
      else el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  };
  return (
    <div className="scroll-buttons">
      <button className="scroll-btn" onClick={() => scrollTo("top")} title="Top">↑</button>
      <button className="scroll-btn" onClick={() => scrollTo("bottom")} title="Bottom">↓</button>
    </div>
  );
}

export default function VocabList({ lang, supportedLangs, onRefreshStats, showToast }) {
  const [words, setWords] = useState([]);
  const [filterLang, setFilterLang] = useState(null);
  const [sortBy, setSortBy] = useState("last_encounter");
  const [expandedId, setExpandedId] = useState(null);
  const [showManagement, setShowManagement] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);

  // Search
  const [searchText, setSearchText] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const searchRef = useRef(null);
  const dropdownRef = useRef(null);

  // Highlighted word (from search click)
  const [highlightedId, setHighlightedId] = useState(null);

  // Load word list
  const loadWords = useCallback(async () => {
    try {
      const list = await getVocabularyList(filterLang, 10000, sortBy);
      setWords(list);
      setCurrentPage(1);
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

  // Pagination calculations
  const totalPages = Math.max(1, Math.ceil(words.length / ITEMS_PER_PAGE));
  const pagedWords = words.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Ensure currentPage stays valid
  useEffect(() => {
    if (currentPage > totalPages) setCurrentPage(totalPages);
  }, [totalPages, currentPage]);

  // Search: filter words that start with searchText
  const searchResults = useMemo(() => {
    if (!searchText.trim()) return [];
    const q = searchText.trim().toLowerCase();
    return words.filter((w) => w.word.toLowerCase().startsWith(q));
  }, [searchText, words]);

  // Jump to word's page and highlight it
  const jumpToWord = useCallback(
    (wordId) => {
      const idx = words.findIndex((w) => w.id === wordId);
      if (idx < 0) return;
      const page = Math.floor(idx / ITEMS_PER_PAGE) + 1;
      setCurrentPage(page);
      setExpandedId(wordId);
      setSearchText("");
      setSearchFocused(false);
      setHighlightedId(wordId);
      // Scroll to element after render
      setTimeout(() => {
        const el = document.getElementById(`vocab-item-${wordId}`);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 50);
      // Clear highlight after animation
      setTimeout(() => setHighlightedId(null), 1500);
    },
    [words]
  );

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (
        searchRef.current &&
        !searchRef.current.contains(e.target) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target)
      ) {
        setSearchFocused(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

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

        {/* Search box */}
        <div className="search-container" style={{ position: "relative" }}>
          <input
            ref={searchRef}
            type="text"
            className="search-input"
            placeholder={t("search_placeholder", lang)}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onFocus={() => setSearchFocused(true)}
          />
          {searchFocused && searchText.trim() && (
            <div className="search-dropdown" ref={dropdownRef}>
              {searchResults.length === 0 ? (
                <div className="search-result-item no-results">
                  {t("search_no_results", lang)}
                </div>
              ) : (
                <>
                  {searchResults.slice(0, SEARCH_MAX_DROPDOWN).map((w) => (
                    <div
                      key={w.id}
                      className="search-result-item"
                      onMouseDown={() => jumpToWord(w.id)}
                    >
                      <span className="search-result-word">{w.word}</span>
                      <span className="search-result-lang">{w.lang}</span>
                    </div>
                  ))}
                  {searchResults.length > SEARCH_MAX_DROPDOWN && (
                    <div className="search-result-item no-results">
                      {t("search_more", lang, searchResults.length - SEARCH_MAX_DROPDOWN)}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Word list */}
      {words.length === 0 ? (
        <div className="empty-state">{t("no_words", lang)}</div>
      ) : (
        <>
          {pagedWords.map((word) => (
            <WordItem
              key={word.id}
              word={word}
              expanded={expandedId === word.id}
              highlighted={highlightedId === word.id}
              onToggle={() => toggleExpand(word.id)}
              lang={lang}
              supportedLangs={supportedLangs}
              onRefresh={() => { loadWords(); onRefreshStats(); }}
              showToast={showToast}
            />
          ))}
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </>
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

      <ScrollButtons />
    </div>
  );
}

// --- Word Item ---
function WordItem({ word, expanded, highlighted, onToggle, lang, supportedLangs, onRefresh, showToast }) {
  const [encounters, setEncounters] = useState([]);
  const [children, setChildren] = useState([]);
  const [parentWord, setParentWord] = useState(null);
  const [editNote, setEditNote] = useState(false);
  const [noteText, setNoteText] = useState(word.note || "");
  const [showEncounters, setShowEncounters] = useState(false);

  // Encounter pagination
  const [encPage, setEncPage] = useState(1);

  // Load details when expanded
  useEffect(() => {
    if (!expanded) return;
    getWordEncounters(word.id).then(setEncounters).catch(console.error);
    getChildren(word.id).then(setChildren).catch(console.error);
    if (word.parent_id) {
      getWordById(word.parent_id).then(setParentWord).catch(console.error);
    }
  }, [expanded, word.id, word.parent_id]);

  // Reset encounter page when encounters change
  useEffect(() => {
    setEncPage(1);
  }, [encounters]);

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

  // Encounter pagination calculations
  const encTotalPages = Math.max(1, Math.ceil(encounters.length / ENC_PER_PAGE));
  const pagedEncounters = encounters.slice(
    (encPage - 1) * ENC_PER_PAGE,
    encPage * ENC_PER_PAGE
  );

  return (
    <div
      id={`vocab-item-${word.id}`}
      className={`vocab-item${highlighted ? " highlighted" : ""}`}
    >
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
              {encounters.length > 0 && (
                <span style={{ marginLeft: 6, fontWeight: 400, color: "var(--text-muted)" }}>
                  ({encounters.length})
                </span>
              )}
            </div>
            {showEncounters && (
              <div>
                {encounters.length === 0 ? (
                  <div style={{ fontSize: 12, color: "var(--text-muted)", padding: 8 }}>
                    —
                  </div>
                ) : (
                  <>
                    {pagedEncounters.map((enc) => (
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
                    ))}
                    <Pagination
                      currentPage={encPage}
                      totalPages={encTotalPages}
                      onPageChange={setEncPage}
                    />
                  </>
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
