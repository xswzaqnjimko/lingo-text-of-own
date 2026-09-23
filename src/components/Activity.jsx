import React, { useState, useEffect, useCallback } from "react";
import { t } from "../services/i18n";
import { getActivityHistory, getActivitySummary } from "../services/database";

const RANGES = [
  { key: 7, label: "range_7" },
  { key: 30, label: "range_30" },
  { key: 365, label: "range_365" },
];

export default function Activity({ lang }) {
  const [range, setRange] = useState(30);
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);

  const loadData = useCallback(async () => {
    try {
      const [sum, hist] = await Promise.all([
        getActivitySummary(range),
        getActivityHistory(range),
      ]);
      setSummary(sum);
      setHistory(hist);
    } catch (e) {
      console.error("Failed to load activity:", e);
    }
  }, [range]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Fill in all days in the range (so empty days show as gaps in the chart)
  // Only fill gaps for short ranges (≤30 days); longer ranges just show active days
  const filledHistory = React.useMemo(() => {
    if (history.length === 0) return [];
    if (range > 30) return history;
    const byDay = {};
    history.forEach((d) => { byDay[d.day] = d; });
    const maxDay = Math.max(...history.map((d) => d.day));
    const minDay = Math.max(1, maxDay - range + 1);
    const filled = [];
    for (let day = minDay; day <= maxDay; day++) {
      filled.push(byDay[day] || { day, sentences_viewed: 0, words_added: 0, words_reviewed: 0, words_graduated: 0, langs_used: "" });
    }
    return filled;
  }, [history, range]);

  // Calculate chart max value
  const maxVal = Math.max(
    1,
    ...filledHistory.map((d) =>
      Math.max(d.sentences_viewed, d.words_added, d.words_reviewed)
    )
  );

  return (
    <div>
      <h1 className="page-title">{t("title_activity", lang)}</h1>

      {/* Range selector */}
      <div className="range-selector">
        {RANGES.map((r) => (
          <button
            key={r.key}
            className={`range-btn ${range === r.key ? "active" : ""}`}
            onClick={() => setRange(r.key)}
          >
            {t(r.label, lang)}
          </button>
        ))}
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="activity-summary">
          <div className="summary-card">
            <div className="summary-value">{summary.active_days}</div>
            <div className="summary-label">{t("active_days", lang)}</div>
          </div>
          <div className="summary-card">
            <div className="summary-value">{summary.sentences_viewed}</div>
            <div className="summary-label">{t("sentences_translated", lang)}</div>
          </div>
          <div className="summary-card">
            <div className="summary-value">{summary.words_added}</div>
            <div className="summary-label">{t("new_words", lang)}</div>
          </div>
          <div className="summary-card">
            <div className="summary-value">{summary.words_reviewed}</div>
            <div className="summary-label">{t("review_count", lang)}</div>
          </div>
        </div>
      )}

      {/* Bar chart */}
      {filledHistory.length > 0 && (
        <div className="chart-container">
          <div className="chart-bars">
            {filledHistory.map((day, i) => {
              const sH = (day.sentences_viewed / maxVal) * 100;
              const wH = (day.words_added / maxVal) * 100;
              const rH = (day.words_reviewed / maxVal) * 100;

              // Show day label for every Nth bar depending on range
              const step = range <= 7 ? 1 : range <= 30 ? 5 : Math.max(1, Math.floor(filledHistory.length / 10));
              const showLabel = i % step === 0;

              return (
                <div
                  className="chart-bar-group"
                  key={day.day}
                  title={`Day ${day.day}: ${day.sentences_viewed}s / ${day.words_added}w / ${day.words_reviewed}r`}
                >
                  <div style={{ display: "flex", gap: 1, alignItems: "flex-end", height: "100%" }}>
                    <div
                      className="chart-bar sentences"
                      style={{ height: `${Math.max(sH, day.sentences_viewed > 0 ? 3 : 0)}%` }}
                    />
                    <div
                      className="chart-bar words"
                      style={{ height: `${Math.max(wH, day.words_added > 0 ? 3 : 0)}%` }}
                    />
                    <div
                      className="chart-bar reviews"
                      style={{ height: `${Math.max(rH, day.words_reviewed > 0 ? 3 : 0)}%` }}
                    />
                  </div>
                  <div className="chart-bar-label" style={showLabel ? {} : { visibility: "hidden" }}>{day.day}</div>
                </div>
              );
            })}
          </div>

          <div className="chart-legend">
            <span>
              <span className="chart-legend-dot" style={{ background: "#93c5fd" }} />
              {t("sentences_translated", lang)}
            </span>
            <span>
              <span className="chart-legend-dot" style={{ background: "#86efac" }} />
              {t("new_words", lang)}
            </span>
            <span>
              <span className="chart-legend-dot" style={{ background: "#fbbf24" }} />
              {t("review_count", lang)}
            </span>
          </div>
        </div>
      )}

      {history.length === 0 && (
        <div className="empty-state">{t("no_words", lang)}</div>
      )}
    </div>
  );
}
