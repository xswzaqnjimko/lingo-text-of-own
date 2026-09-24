import React, { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { t } from "../services/i18n";
import {
  getHallOfFameList,
  demoteFromHallOfFame,
  logWordReviewed,
} from "../services/database";

const ITEMS_PER_PAGE = 50;
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

export default function HallOfFame({ lang, supportedLangs, onRefreshStats, showToast }) {
  const [entries, setEntries] = useState([]);
  const [filterLang, setFilterLang] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);

  // Search
  const [searchText, setSearchText] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const searchRef = useRef(null);
  const dropdownRef = useRef(null);

  // Highlighted entry (from search click)
  const [highlightedId, setHighlightedId] = useState(null);

  const loadEntries = useCallback(async () => {
    try {
      const list = await getHallOfFameList(filterLang, 10000);
      setEntries(list);
      setCurrentPage(1);
    } catch (e) {
      console.error("Failed to load hall of fame:", e);
    }
  }, [filterLang]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  const handleDemote = async (hofId, entryLang) => {
    try {
      const [ok, msg] = await demoteFromHallOfFame(hofId);
      showToast(msg);
      logWordReviewed(entryLang).catch(console.error);
      loadEntries();
      onRefreshStats();
    } catch (e) {
      showToast(String(e));
    }
  };

  const availLangs = [...new Set(entries.map((e) => e.lang))];

  // Pagination calculations
  const totalPages = Math.max(1, Math.ceil(entries.length / ITEMS_PER_PAGE));
  const pagedEntries = entries.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  useEffect(() => {
    if (currentPage > totalPages) setCurrentPage(totalPages);
  }, [totalPages, currentPage]);

  // Search
  const searchResults = useMemo(() => {
    if (!searchText.trim()) return [];
    const q = searchText.trim().toLowerCase();
    return entries.filter((e) => e.word.toLowerCase().startsWith(q));
  }, [searchText, entries]);

  const jumpToEntry = useCallback(
    (entryId) => {
      const idx = entries.findIndex((e) => e.id === entryId);
      if (idx < 0) return;
      const page = Math.floor(idx / ITEMS_PER_PAGE) + 1;
      setCurrentPage(page);
      setExpandedId(entryId);
      setSearchText("");
      setSearchFocused(false);
      setHighlightedId(entryId);
      setTimeout(() => {
        const el = document.getElementById(`hof-item-${entryId}`);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 50);
      setTimeout(() => setHighlightedId(null), 1500);
    },
    [entries]
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
      <h1 className="page-title">{t("title_hall", lang)}</h1>
      <p className="page-subtitle">{t("subtitle_hall", lang)}</p>

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
        <span className="vocab-count">
          {t("total_words", lang, entries.length)}
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
                  {searchResults.slice(0, SEARCH_MAX_DROPDOWN).map((e) => (
                    <div
                      key={e.id}
                      className="search-result-item"
                      onMouseDown={() => jumpToEntry(e.id)}
                    >
                      <span className="search-result-word">{e.word}</span>
                      <span className="search-result-lang">{e.lang}</span>
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

      {entries.length === 0 ? (
        <div className="empty-state">{t("no_hall_words", lang)}</div>
      ) : (
        <>
          {pagedEntries.map((entry) => (
            <HofItem
              key={entry.id}
              entry={entry}
              expanded={expandedId === entry.id}
              highlighted={highlightedId === entry.id}
              onToggle={() =>
                setExpandedId((prev) => (prev === entry.id ? null : entry.id))
              }
              onDemote={() => handleDemote(entry.id, entry.lang)}
              lang={lang}
              supportedLangs={supportedLangs}
            />
          ))}
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </>
      )}

      <ScrollButtons />
    </div>
  );
}

function HofItem({ entry, expanded, highlighted, onToggle, onDemote, lang, supportedLangs }) {
  const langName = supportedLangs.find(([c]) => c === entry.lang)?.[1] || entry.lang;

  // Parse encounter data JSON
  let firstData = null;
  let lastData = null;
  try {
    if (entry.first_encounter_data)
      firstData = JSON.parse(entry.first_encounter_data);
    if (entry.last_encounter_data)
      lastData = JSON.parse(entry.last_encounter_data);
  } catch (_) {}

  return (
    <div
      id={`hof-item-${entry.id}`}
      className={`hof-item${highlighted ? " highlighted" : ""}`}
    >
      <div
        style={{ display: "flex", alignItems: "center", cursor: "pointer" }}
        onClick={onToggle}
      >
        <span className={`vocab-chevron ${expanded ? "open" : ""}`} style={{ marginRight: 10 }}>
          ▶
        </span>
        <span className="hof-word">{entry.word}</span>
        <span className="vocab-lang-badge" style={{ marginLeft: 10 }}>
          {langName}
        </span>
        {entry.breakthrough_count > 0 && (
          <span className="hof-breakthrough">
            {t("breakthrough", lang)} ×{entry.breakthrough_count}
          </span>
        )}
      </div>

      <div className="hof-meta">
        {entry.total_encounters != null && (
          <span>{t("encounter_count", lang)} {entry.total_encounters}</span>
        )}
        {entry.promoted_at && (
          <span style={{ marginLeft: 12 }}>
            {entry.promoted_at}
          </span>
        )}
      </div>

      {expanded && (
        <div style={{ marginTop: 12 }}>
          {/* First encounter */}
          {firstData && (
            <div className="encounter-item">
              <div className="enc-label">{t("first_encounter_detail", lang)}</div>
              {firstData.sentence_zh && <div>{firstData.sentence_zh}</div>}
              {firstData.source_title && (
                <div style={{ color: "var(--text-muted)" }}>
                  {t("source_work", lang)} {firstData.source_title}
                </div>
              )}
            </div>
          )}

          {/* Last encounter */}
          {lastData && (
            <div className="encounter-item">
              <div className="enc-label">{t("final_encounter_detail", lang)}</div>
              {lastData.sentence_zh && <div>{lastData.sentence_zh}</div>}
              {lastData.source_title && (
                <div style={{ color: "var(--text-muted)" }}>
                  {t("source_work", lang)} {lastData.source_title}
                </div>
              )}
            </div>
          )}

          <button
            className="btn btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              onDemote();
            }}
            style={{ marginTop: 8 }}
          >
            {t("demote_button", lang)}
          </button>
        </div>
      )}
    </div>
  );
}
