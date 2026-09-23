import React, { useState, useEffect, useCallback } from "react";
import { t } from "../services/i18n";
import {
  getHallOfFameList,
  demoteFromHallOfFame,
  logWordReviewed,
} from "../services/database";

export default function HallOfFame({ lang, supportedLangs, onRefreshStats, showToast }) {
  const [entries, setEntries] = useState([]);
  const [filterLang, setFilterLang] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  const loadEntries = useCallback(async () => {
    try {
      const list = await getHallOfFameList(filterLang, 500);
      setEntries(list);
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

  return (
    <div>
      <h1 className="page-title">{t("title_hall", lang)}</h1>
      <p className="page-subtitle">{t("subtitle_hall", lang)}</p>

      {/* Language filter */}
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
      </div>

      {entries.length === 0 ? (
        <div className="empty-state">{t("no_hall_words", lang)}</div>
      ) : (
        entries.map((entry) => (
          <HofItem
            key={entry.id}
            entry={entry}
            expanded={expandedId === entry.id}
            onToggle={() =>
              setExpandedId((prev) => (prev === entry.id ? null : entry.id))
            }
            onDemote={() => handleDemote(entry.id, entry.lang)}
            lang={lang}
            supportedLangs={supportedLangs}
          />
        ))
      )}
    </div>
  );
}

function HofItem({ entry, expanded, onToggle, onDemote, lang, supportedLangs }) {
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
    <div className="hof-item">
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
