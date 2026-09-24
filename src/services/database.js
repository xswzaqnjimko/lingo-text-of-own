// database.js — thin invoke() wrappers for Tauri commands
// Same pattern as yet_another_task_calendar/src/services/database.js

import { invoke } from "@tauri-apps/api/core";

// === Settings & Paths ===

export async function getDataPaths() {
  return invoke("get_data_paths");
}

export async function getSupportedLanguages() {
  return invoke("get_supported_languages");
}

// === Library ===

export async function scanLibrary(path) {
  return invoke("scan_library", { path });
}

export async function getRandomSentence(targetRels, randomAny) {
  return invoke("get_random_sentence", { targetRels, randomAny });
}

export async function getLibraryStats() {
  return invoke("get_library_stats");
}
export async function getLibraryRelationships() {
  return invoke("get_library_relationships");
}

export async function getEligibleCount(targetRels, randomAny) {
  return invoke("get_eligible_count", { targetRels, randomAny });
}

export async function getSentenceFromWork(workId, targetRels, randomAny) {
  return invoke("get_sentence_from_work", { workId, targetRels, randomAny });
}



// === Translation ===

export async function translateSentence(sentence, targetLangs, googleKey, deeplKey) {
  return invoke("translate_sentence", { sentence, targetLangs, googleKey, deeplKey });
}

export async function getDictionaryLinks(googleText, deeplText, langCode) {
  return invoke("get_dictionary_links", { googleText, deeplText, langCode });
}

export async function getTtsLink(text, langCode, engine) {
  return invoke("get_tts_link", { text, langCode, engine });
}

// === Vocabulary ===

export async function getStats() {
  return invoke("get_stats");
}

export async function addWord(word, lang, sentenceZh, enGoogle, enDeepl, targetGoogle, targetDeepl, sourceId, sourceTitle, sourceDetail) {
  return invoke("add_word", {
    word, lang, sentenceZh, enGoogle, enDeepl,
    targetGoogle, targetDeepl, sourceId, sourceTitle, sourceDetail,
  });
}

export async function addWordManual(word, lang, note) {
  return invoke("add_word_manual", { word, lang, note });
}

export async function getVocabularyList(lang, limit, sortBy) {
  return invoke("get_vocabulary_list", { lang, limit, sortBy });
}

export async function getWordEncounters(vocabId) {
  return invoke("get_word_encounters", { vocabId });
}

export async function getWordById(vocabId) {
  return invoke("get_word_by_id", { vocabId });
}

export async function getChildren(parentId) {
  return invoke("get_children", { parentId });
}

export async function decreaseHp(vocabId) {
  return invoke("decrease_hp", { vocabId });
}

export async function increaseHp(vocabId) {
  return invoke("increase_hp", { vocabId });
}

export async function deleteWord(vocabId) {
  return invoke("delete_word", { vocabId });
}

export async function renameWord(vocabId, newWord) {
  return invoke("rename_word", { vocabId, newWord });
}

export async function searchWord(word, lang) {
  return invoke("search_word", { word, lang });
}

export async function updateNote(vocabId, note) {
  return invoke("update_note", { vocabId, note });
}

export async function setParent(childId, parentId) {
  return invoke("set_parent", { childId, parentId });
}

// === Hall of Fame ===

export async function getHallOfFameList(lang, limit) {
  return invoke("get_hall_of_fame_list", { lang, limit });
}

export async function demoteFromHallOfFame(hofId) {
  return invoke("demote_from_hall_of_fame", { hofId });
}

// === Activity ===

export async function logSentenceViewed(lang) {
  return invoke("log_sentence_viewed", { lang });
}

export async function logWordAdded(lang) {
  return invoke("log_word_added", { lang });
}

export async function logWordReviewed(lang) {
  return invoke("log_word_reviewed", { lang });
}

export async function logWordGraduated(lang) {
  return invoke("log_word_graduated", { lang });
}

export async function getActivityHistory(days) {
  return invoke("get_activity_history", { days });
}

export async function getActivitySummary(days) {
  return invoke("get_activity_summary", { days });
}

// === API Usage ===

export async function getApiUsage() {
  return invoke("get_api_usage");
}
