import React, { useState, useEffect, useCallback, useRef } from "react";
import { load } from "@tauri-apps/plugin-store";
import { t } from "../services/i18n";
import {
  getStats,
  getSupportedLanguages,
  scanLibrary,
  getDataPaths,
} from "../services/database";

import SentenceView from "./SentenceView";
import VocabList from "./VocabList";
import HallOfFame from "./HallOfFame";
import Activity from "./Activity";
import Settings from "./Settings";

const PAGES = ["home", "vocab", "hall", "activity", "settings"];

const DEFAULT_SETTINGS = {
  libraryPath: "",
  googleApiKey: "",
  deeplApiKey: "",
  selectedLangs: ["es"],
  uiLang: "zh",
  showComparison: true,
  enableAo3: true,
  targetRelationships: [],
};

export default function App() {
  const [page, setPage] = useState("home");
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [stats, setStats] = useState(null);
  const [supportedLangs, setSupportedLangs] = useState([]);
  const [dataPaths, setDataPaths] = useState({ library_path: "", db_path: "" });
  const [libraryLoaded, setLibraryLoaded] = useState(false);
  const [toast, setToast] = useState(null);

  // Lifted from SentenceView so state persists across page switches
  const [sentence, setSentence] = useState(null);
  const [translations, setTranslations] = useState(null);
  const [dictLinks, setDictLinks] = useState({});
  const toastTimer = useRef(null);
  const storeRef = useRef(null);

  const lang = settings.uiLang;

  // Load settings from Tauri store on mount
  useEffect(() => {
    (async () => {
      try {
        const store = await load("settings.json", { autoSave: true });
        storeRef.current = store;

        const saved = await store.get("app_settings");
        if (saved) {
          setSettings((prev) => ({ ...prev, ...saved }));
        }
      } catch (e) {
        console.warn("Failed to load settings store:", e);
      }
    })();
  }, []);

  // Load supported languages once
  useEffect(() => {
    getSupportedLanguages()
      .then((langs) => setSupportedLangs(langs))
      .catch(console.error);
  }, []);

  // Load data paths
  useEffect(() => {
    getDataPaths()
      .then((paths) => setDataPaths(paths))
      .catch(console.error);
  }, []);

  // Scan library when path changes
  useEffect(() => {
    if (settings.libraryPath) {
      scanLibrary(settings.libraryPath)
        .then(() => setLibraryLoaded(true))
        .catch((e) => {
          console.error("Library scan failed:", e);
          setLibraryLoaded(false);
        });
    }
  }, [settings.libraryPath]);

  // Refresh stats
  const refreshStats = useCallback(async () => {
    try {
      const s = await getStats();
      setStats(s);
    } catch (e) {
      console.error("Failed to get stats:", e);
    }
  }, []);

  useEffect(() => {
    refreshStats();
  }, [refreshStats, page]);

  // Save settings
  const saveSettings = useCallback(
    async (newSettings) => {
      setSettings(newSettings);
      if (storeRef.current) {
        try {
          await storeRef.current.set("app_settings", newSettings);
        } catch (e) {
          console.warn("Failed to save settings:", e);
        }
      }
    },
    []
  );

  // Toast
  const showToast = useCallback((message) => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(message);
    toastTimer.current = setTimeout(() => setToast(null), 2500);
  }, []);

  // Navigate
  const navigate = useCallback((p) => setPage(p), []);

  // Render page content
  const renderPage = () => {
    switch (page) {
      case "home":
        return (
          <SentenceView
            settings={settings}
            lang={lang}
            supportedLangs={supportedLangs}
            onRefreshStats={refreshStats}
            showToast={showToast}
            sentence={sentence}
            setSentence={setSentence}
            translations={translations}
            setTranslations={setTranslations}
            dictLinks={dictLinks}
            setDictLinks={setDictLinks}
          />
        );
      case "vocab":
        return (
          <VocabList
            lang={lang}
            supportedLangs={supportedLangs}
            onRefreshStats={refreshStats}
            showToast={showToast}
          />
        );
      case "hall":
        return (
          <HallOfFame
            lang={lang}
            supportedLangs={supportedLangs}
            onRefreshStats={refreshStats}
            showToast={showToast}
          />
        );
      case "activity":
        return <Activity lang={lang} />;
      case "settings":
        return (
          <Settings
            settings={settings}
            onSave={saveSettings}
            lang={lang}
            supportedLangs={supportedLangs}
            dataPaths={dataPaths}
            showToast={showToast}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-title">🍚 lingo-text</div>
        <ul className="sidebar-nav">
          {[
            ["home", t("nav_home", lang)],
            ["vocab", t("nav_vocab", lang)],
            ["hall", t("nav_hall", lang)],
            ["activity", t("nav_activity", lang)],
          ].map(([key, label]) => (
            <li key={key}>
              <button
                className={page === key ? "active" : ""}
                onClick={() => navigate(key)}
              >
                {label}
              </button>
            </li>
          ))}

          {/* Settings at the bottom of the nav list */}
          <li style={{ marginTop: "8px" }}>
            <button
              className={page === "settings" ? "active" : ""}
              onClick={() => navigate("settings")}
            >
              {t("settings_title", lang)}
            </button>
          </li>
        </ul>

        {/* Stats */}
        {stats && (
          <div className="sidebar-stats">
            <div>{t("stats_day", lang, stats.current_day)}</div>
            <div>{t("stats_vocab", lang, stats.total_words)}</div>
            <div>{t("stats_hall", lang, stats.hall_of_fame_count)}</div>
            {stats.by_lang &&
              Object.entries(stats.by_lang).map(([code, count]) => (
                <div key={code}>{t("stats_by_lang", lang, code, count)}</div>
              ))}
          </div>
        )}
      </nav>

      {/* Main content */}
      <main className="main-content">{renderPage()}</main>

      {/* Toast */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
