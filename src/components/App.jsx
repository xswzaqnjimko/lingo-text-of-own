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
import FillBlank from "./FillBlank";
import Activity from "./Activity";
import Settings from "./Settings";

const PAGES = ["home", "vocab", "hall", "fillblank", "activity", "settings"];

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
  const [pendingJumpWordId, setPendingJumpWordId] = useState(null);
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

  // Navigate (lazy mount: track visited pages so components mount on first visit)
  const [visited, setVisited] = useState(new Set(["home"]));
  const navigate = useCallback((p) => {
    setPage(p);
    setVisited((prev) => prev.has(p) ? prev : new Set(prev).add(p));
  }, []);

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
            ["fillblank", t("nav_fillblank", lang)],
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

      {/* Main content — lazy mount + display:none to preserve page state */}
      <main className="main-content">
        {visited.has("home") && (
          <div style={{ display: page === "home" ? undefined : "none" }}>
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
              isActive={page === "home"}
            />
          </div>
        )}
        {visited.has("vocab") && (
          <div style={{ display: page === "vocab" ? undefined : "none" }}>
            <VocabList
              lang={lang}
              supportedLangs={supportedLangs}
              onRefreshStats={refreshStats}
              showToast={showToast}
              pendingJumpWordId={pendingJumpWordId}
              onJumpHandled={() => setPendingJumpWordId(null)}
              isActive={page === "vocab"}
            />
          </div>
        )}
        {visited.has("hall") && (
          <div style={{ display: page === "hall" ? undefined : "none" }}>
            <HallOfFame
              lang={lang}
              supportedLangs={supportedLangs}
              onRefreshStats={refreshStats}
              showToast={showToast}
            />
          </div>
        )}
        {visited.has("fillblank") && (
          <div style={{ display: page === "fillblank" ? undefined : "none" }}>
            <FillBlank
              lang={lang}
              supportedLangs={supportedLangs}
              showToast={showToast}
              onJumpToWord={(id) => {
                setPendingJumpWordId(id);
                navigate("vocab");
              }}
            />
          </div>
        )}
        {visited.has("activity") && (
          <div style={{ display: page === "activity" ? undefined : "none" }}>
            <Activity lang={lang} isActive={page === "activity"} />
          </div>
        )}
        {visited.has("settings") && (
          <div style={{ display: page === "settings" ? undefined : "none" }}>
            <Settings
              settings={settings}
              onSave={saveSettings}
              lang={lang}
              supportedLangs={supportedLangs}
              dataPaths={dataPaths}
              showToast={showToast}
            />
          </div>
        )}
      </main>

      {/* Toast */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
