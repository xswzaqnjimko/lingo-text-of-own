import React, { useState, useEffect } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { t } from "../services/i18n";
import { getLibraryRelationships } from "../services/database";

export default function Settings({
  settings,
  onSave,
  lang,
  supportedLangs,
  dataPaths,
  showToast,
}) {
  // Local draft of settings
  const [draft, setDraft] = useState({ ...settings });

  // Sync when settings prop changes
  useEffect(() => {
    setDraft({ ...settings });
  }, [settings]);

  const update = (key, value) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  };

  // Available relationships from scanned library
  const [availableRels, setAvailableRels] = useState([]);

  useEffect(() => {
    if (draft.enableAo3) {
      getLibraryRelationships()
        .then((rels) => setAvailableRels(rels))
        .catch(console.error);
    }
  }, [draft.enableAo3]);

  const toggleRel = (rel) => {
    setDraft((prev) => {
      const rels = prev.targetRelationships || [];
      const next = rels.includes(rel)
        ? rels.filter((r) => r !== rel)
        : [...rels, rel];
      return { ...prev, targetRelationships: next };
    });
  };

  const selectAllRels = () => {
    setDraft((prev) => ({ ...prev, targetRelationships: [...availableRels] }));
  };

  const deselectAllRels = () => {
    setDraft((prev) => ({ ...prev, targetRelationships: [] }));
  };

  const toggleLang = (code) => {
    setDraft((prev) => {
      const langs = prev.selectedLangs.includes(code)
        ? prev.selectedLangs.filter((c) => c !== code)
        : [...prev.selectedLangs, code];
      return { ...prev, selectedLangs: langs };
    });
  };

  const handleSave = () => {
    onSave(draft);
    showToast(t("settings_saved", lang));
  };

  const handleChooseLibrary = async () => {
    try {
      const selected = await open({
        directory: true,
        title: t("library_path_label", lang),
      });
      if (selected) {
        update("libraryPath", selected);
      }
    } catch (e) {
      console.error("Dialog error:", e);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(
      () => showToast("Copied!"),
      () => showToast("Copy failed")
    );
  };

  return (
    <div>
      <h1 className="page-title">{t("settings_title", lang)}</h1>

      {/* UI Language */}
      <div className="settings-section">
        <h3>{t("ui_language", lang)}</h3>
        <select
          value={draft.uiLang}
          onChange={(e) => update("uiLang", e.target.value)}
          style={{ width: 160 }}
        >
          <option value="zh">中文</option>
          <option value="en">English</option>
        </select>
      </div>

      {/* Target Languages */}
      <div className="settings-section">
        <h3>{t("target_languages", lang)}</h3>
        <p className="form-hint">{t("target_languages_hint", lang)}</p>
        <div className="lang-checkboxes" style={{ marginTop: 8 }}>
          {supportedLangs.map(([code, name, nameEn]) => (
            <label key={code} className="lang-checkbox">
              <input
                type="checkbox"
                checked={draft.selectedLangs.includes(code)}
                onChange={() => toggleLang(code)}
              />
              {name} ({nameEn})
            </label>
          ))}
        </div>
      </div>

      {/* Comparison mode */}
      <div className="settings-section">
        <div className="toggle-row">
          <div>
            <div className="toggle-label">{t("comparison_mode", lang)}</div>
            <div className="toggle-hint">{t("comparison_hint", lang)}</div>
          </div>
          <button
            className={`toggle ${draft.showComparison ? "on" : ""}`}
            onClick={() => update("showComparison", !draft.showComparison)}
          />
        </div>
      </div>

      {/* AO3 mode */}
      <div className="settings-section">
        <div className="toggle-row">
          <div>
            <div className="toggle-label">{t("ao3_mode", lang)}</div>
            <div className="toggle-hint">{t("ao3_hint", lang)}</div>
          </div>
          <button
            className={`toggle ${draft.enableAo3 ? "on" : ""}`}
            onClick={() => update("enableAo3", !draft.enableAo3)}
          />
        </div>

        {/* Relationship filter — shown when AO3 is on */}
        {draft.enableAo3 && availableRels.length > 0 && (
          <RelationshipFilter
            availableRels={availableRels}
            targetRels={draft.targetRelationships || []}
            toggleRel={toggleRel}
            selectAllRels={selectAllRels}
            deselectAllRels={deselectAllRels}
            lang={lang}
          />
        )}
      </div>

      {/* Library Path */}
      <div className="settings-section">
        <h3>{t("library_path_label", lang)}</h3>
        <p className="form-hint">{t("library_path_hint", lang)}</p>
        <div className="path-display" style={{ marginTop: 8 }}>
          <span className="path-text">
            {draft.libraryPath || "—"}
          </span>
          <button className="btn btn-sm" onClick={handleChooseLibrary}>
            {t("change_path", lang)}
          </button>
          {draft.libraryPath && (
            <button
              className="btn btn-sm"
              onClick={() => copyToClipboard(draft.libraryPath)}
            >
              {t("copy_path", lang)}
            </button>
          )}
        </div>
      </div>

      {/* Database Location */}
      <div className="settings-section">
        <h3>{t("db_location", lang)}</h3>
        <div className="path-display">
          <span className="path-text">
            {dataPaths.db_path || "—"}
          </span>
          {dataPaths.db_path && (
            <button
              className="btn btn-sm"
              onClick={() => copyToClipboard(dataPaths.db_path)}
            >
              {t("copy_path", lang)}
            </button>
          )}
        </div>
      </div>

      {/* API Keys */}
      <div className="settings-section">
        <h3>{t("api_keys", lang)}</h3>
        <div className="form-group">
          <label>{t("google_api_key", lang)}</label>
          <input
            type="password"
            value={draft.googleApiKey}
            onChange={(e) => update("googleApiKey", e.target.value)}
            placeholder="AIza..."
          />
        </div>
        <div className="form-group">
          <label>{t("deepl_api_key", lang)}</label>
          <input
            type="password"
            value={draft.deeplApiKey}
            onChange={(e) => update("deeplApiKey", e.target.value)}
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx"
          />
        </div>
      </div>

      {/* Save button */}
      <button className="btn btn-primary btn-lg" onClick={handleSave}>
        {t("save_settings", lang)}
      </button>
    </div>
  );
}


// Featured relationships shown as top-level checkboxes; rest are collapsible
const FEATURED_RELS = [
  "Kaminaga/Miyoshi (Joker Game)",
  "Yuris Leclair | Yuri Leclerc/Claude von Riegan",
  "Yuris Leclair | Yuri Leclerc & Claude von Riegan",
];

function RelationshipFilter({ availableRels, targetRels, toggleRel, selectAllRels, deselectAllRels, lang }) {
  const [showOthers, setShowOthers] = React.useState(false);

  const featured = availableRels.filter((r) => FEATURED_RELS.includes(r));
  const others = availableRels.filter((r) => !FEATURED_RELS.includes(r));

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <strong>{t("rel_filter_title", lang)}</strong>
        <button className="btn btn-sm" onClick={selectAllRels}>
          {t("rel_select_all", lang)}
        </button>
        <button className="btn btn-sm" onClick={deselectAllRels}>
          {t("rel_deselect_all", lang)}
        </button>
      </div>
      <p className="form-hint">{t("rel_filter_hint", lang)}</p>
      <div className="lang-checkboxes" style={{ marginTop: 4 }}>
        {featured.map((rel) => (
          <label key={rel} className="lang-checkbox">
            <input
              type="checkbox"
              checked={targetRels.includes(rel)}
              onChange={() => toggleRel(rel)}
            />
            {rel}
          </label>
        ))}
      </div>
      {others.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div
            className="collapsible-header"
            onClick={() => setShowOthers(!showOthers)}
            style={{ cursor: "pointer", fontSize: "0.9em" }}
          >
            <span className={`vocab-chevron ${showOthers ? "open" : ""}`}>▶</span>
            {lang === "zh" ? `其他 (${others.length})` : `Others (${others.length})`}
          </div>
          {showOthers && (
            <div className="lang-checkboxes" style={{ marginTop: 4 }}>
              {others.map((rel) => (
                <label key={rel} className="lang-checkbox">
                  <input
                    type="checkbox"
                    checked={targetRels.includes(rel)}
                    onChange={() => toggleRel(rel)}
                  />
                  {rel}
                </label>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
