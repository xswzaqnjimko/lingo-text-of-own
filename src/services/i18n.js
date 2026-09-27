// i18n.js — UI text translations (port of i18n.py)

const UI_TEXTS = {
  zh: {
    // Navigation
    nav_home: "🍚 首页",
    nav_vocab: "📖 生词本",
    nav_hall: "🏖️ 名人堂",
    nav_activity: "📅 学习记录",

    // Stats
    stats_day: "📊 当前第 {0} 天",
    stats_vocab: "📝 生词本: {0} 个词",
    stats_hall: "🎤 总选名人堂: {0} 个词",
    stats_by_lang: "  · {0}: {1} 个",

    // Home
    title_home: "🍚 整点腿肉机翻假装能学外语ry",
    draw_sentence: "🎲 抽一句",
    pool_info: "📦 可抽取作品：{0} / {1} 篇",
    pool_sentences: "共 {0} 句",
    api_usage: "本月约 Google {0} / 500k · DeepL {1} / 500k",
    no_eligible: "当前筛选条件下无可用作品",
    original_sentence: "原文（中文）",
    english_translation: "英语翻译（过渡&对照用）",

    // Translation
    translation_google: "Google",
    translation_deepl: "DeepL",
    play_audio: "▶️",
    play_audio_hint: "在 {0} 打开此句听机器一读🔊",
    dict_external: "外部词典（{0}）",
    add_to_vocab: "📝 加入{0}生词本",
    word_input_placeholder: "不太认识！的词/词组不想手抄也起码该复制粘贴一次...",
    add_button: "加入",

    // Vocabulary page
    title_vocab: "📚 生词本",
    select_language: "选择语言",
    all_languages: "全部语言",
    sort_by: "排序方式",
    sort_last_encounter: "最近遭遇（新→旧）",
    sort_first_encounter: "最初遭遇（旧→新）",
    sort_encounter_count: "遭遇次数（多→少）",
    sort_last_reviewed: "最近温习（新→旧）",
    sort_alphabetical: "字母表顺序 (A-Z)",
    total_words: "共 {0} 个词",
    no_words: "还没有生词哦，开始学习吧！",

    // Word details
    word_entry: "词条：",
    language_label: "语言：",
    dict_link: "🔗词典释义",
    first_seen: "首次遭遇：",
    last_seen: "最近遭遇：",
    encounter_count: "遭遇次数：",
    day_gap: "距离上次遭遇：",
    day_gap_first: "首次记录",
    stats_hp: "白值：",
    breakthrough: "🌟突破",
    parent_word: "📖 原形：",
    child_words: "📚 变体：",

    // Learning feedback
    learning_feedback: "💪 学习反馈：",
    seems_familiar: "好像认识",
    dont_know: "不太认识",
    promoted_toast: "词条总选出道！",
    hp_updated_toast: "HP 已更新",

    // Notes
    personal_note: "📝 个人注释：",
    edit_note: "✏️ 编辑注释",
    save_note: "💾 保存",
    cancel: "取消",
    note_saved: "注释已保存",

    // Encounter history
    encounter_history: "📜 遭遇历史",
    encounter_index: "遭遇 #{0}",
    sentence_zh: "原文：",
    translation_en: "英文翻译：",
    translation_target: "{0}翻译：",
    source_work: "出处：",

    // Hall of Fame
    title_hall: "🏖️ 总选名人堂",
    subtitle_hall: "已掌握的词条（HP=0）",
    mastered_days: "{0}天前掌握",
    first_encounter_detail: "📖 初次遭遇",
    final_encounter_detail: "🎓 最终遭遇",
    demote_button: "↩️ 退回生词本",
    no_hall_words: "名人堂还是空的，继续加油！",

    // Activity
    title_activity: "📅 学习记录",
    range_7: "最近 7 天",
    range_30: "最近 30 天",
    range_365: "最近一年",
    active_days: "活跃天数",
    sentences_translated: "翻译句数",
    new_words: "新词",
    review_count: "复习次数",

    // Management
    management_tools: "🛠️ 生词本管理工具",
    quick_add: "快速添加词条（无例句）",
    quick_add_word: "词条内容",
    quick_add_button: "➕ 添加",
    rename_word: "重命名词条",
    old_word: "原词条",
    new_word: "新词条",
    rename_button: "✏️ 重命名",
    set_parent_label: "设置母词关系",
    child_word: "子词条",
    parent_word_select: "母词条",
    set_button: "🔗 设置",
    delete_word_label: "删除词条",
    delete_word_select: "选择要删除的词条",
    delete_button: "🗑️ 删除",
    confirm_delete: "确认删除",

    // Settings
    settings_title: "⚙️ 设置",
    ui_language: "🌐 界面语言",
    target_languages: "选择目标语言：",
    target_languages_hint: "（可多选，建议 1-2 个，多了怕慢= =）",
    comparison_mode: "📊 双机翻版本对照模式",
    comparison_hint: "开启时显示 Google 和 DeepL 两个版本",
    ao3_mode: "边吃边学(?)",
    ao3_hint: "🔖 启用 AO3 功能（CP筛选 & 作品信息）",
    rel_filter_title: "仅抽以下 Relationships：",
    rel_filter_hint: "（取消全选则从全部作品抽）",
    rel_select_all: "全选",
    rel_deselect_all: "取消全选",
    random_cp: "🎲 随机CP",
    random_cp_hint: "忽略CP筛选，从全部作品抽",
    library_path_label: "文库路径",
    library_path_hint: "AO3 HTML 文件所在位置",
    change_path: "更改...",
    copy_path: "复制路径",
    db_location: "数据库位置",
    api_keys: "API 密钥",
    google_api_key: "Google Cloud Translation API Key",
    deepl_api_key: "DeepL API Key (Free)",
    save_settings: "💾 保存设置",
    settings_saved: "设置已保存",

    // Work info
    work_info: "作品信息",
    work_title: "标题：",
    work_id_label: "Works ID：",
    work_published: "发布：",
    work_updated: "更新：",
    work_series: "所属 Series：",
    ao3_link: "AO3 链接",

    // Errors
    error_api: "API 调用失败：",
    error_no_library: "请先在设置中配置文库路径",

    // Draw from specific work (v2.1)
    draw_from_work: "抽一句 - 来自特定篇目：",
    work_id_placeholder: "AO3 work ID",
    draw_from_work_btn: "🎲 抽",
    work_not_found: "文库中未找到此 work ID 的作品",
    work_filtered_out: "此作品不满足当前 relationship 筛选条件",

    // Pagination (v2.1)
    page_label: "第 {0} / {1} 页",
    page_jump: "跳至",

    // Search (v2.1)
    search_placeholder: "搜索词条...",
    search_no_results: "无匹配结果",
    search_more: "还有 {0} 个结果...",

    // Scroll buttons (v2.1)
    scroll_top: "↑ 顶部",
    scroll_bottom: "↓ 底部",

    // Encounter pagination (v2.1)
    encounter_page: "遭遇记录 第 {0} / {1} 页",

    // Crit system (v2.2)
    crit_evasion_label: "必杀回避",
    crit_rate_label: "暴击率",
    crit_hit: "💥 暴击！",
    crit_miss: "未暴击",
    crit_hit_enemy: "💥 被暴击！",

    // Encounter engine labels (v2.2)
    engine_google: "(Google)",
    engine_deepl: "(DeepL)",

    // Fill-in-the-blank (v2.2)
    nav_fillblank: "✏️ Naive填空",
    fillblank_title: "✏️ Naive填空",
    fillblank_draw: "填一句",
    fillblank_mode_hint: "无提示模式（奖励翻倍）",
    fillblank_mode_no_hint: "无提示模式（奖励翻倍）",
    fillblank_select_lang: "选择目标语言",
    fillblank_lang_not_eligible: "该语言词汇量不足（需至少4个词）",
    fillblank_no_sentence: "未找到合适的句子，请再试一次",
    fillblank_correct: "✅ 正确！",
    fillblank_wrong: "❌ 错误，正确答案是：{0}",
    fillblank_source: "出处：",
    fillblank_evasion_title: "必杀回避变化：",
    fillblank_check_word: "📖",
    jump_word_not_found: "词条未找到，请检查语言筛选",

    // Manual (v2.2)
    manual_button: "❓ 使用说明",
    manual_title: "使用说明",
    manual_close: "关闭",
    manual_disclaimer: "本应用在开发过程中大量使用了Claude辅助。",
    manual_s1_title: "如何使用此应用",
    manual_s1_body: "扫描文库 → 抽取句子 → 翻译 → 添加生词 → 在生词本复习 → 填空测验 → 毕业进入名人堂",
    manual_s2_title: "HP 系统",
    manual_s2_body: "新词初始 HP = 30。点击“好像认识”HP 基础 -10；点击“不太认识”HP 基础 +20。HP ≤ 0 时总选出道，进入名人堂。",
    manual_s3_title: "暴击率",
    manual_s3_body: "由词条的“必杀回避”值决定。暴击倍率 ×1.5。好像认识暴击 = HP -15（伤害加深）；不太认识被暴击 = HP +30（词条回复更多）。",
    manual_s4_title: "必杀回避",
    manual_s4_body: "通过填空测验调整。答对 → 必杀回避降低（暴击率升高 → 词条更快毕业）；答错 → 必杀回避升高（暴击率降低 → 词条更难毕业）。无提示模式正确时奖励翻倍。",
    manual_s5_title: "填空说明",
    manual_s5_body: "四个选项从你的生词本同语言词条中随机抽取，非语义相关。空格匹配为朴素字符串匹配，可能无法匹配变位/变格形式，这也是叫 Naive 的原因。",
    manual_s6_title: "突破",
    manual_s6_body: "从名人堂退回生词本的次数。",
  },

  en: {
    nav_home: "🍚 Home",
    nav_vocab: "📖 Vocabulary",
    nav_hall: "🏖️ Hall of Fame",
    nav_activity: "📅 Activity",

    stats_day: "📊 Day {0}",
    stats_vocab: "📝 Vocabulary: {0} words",
    stats_hall: "🎤 Hall of Fame: {0} words",
    stats_by_lang: "  · {0}: {1} words",

    title_home: "🍚 Language Learning from Literature",
    draw_sentence: "🎲 Draw a sentence",
    pool_info: "📦 Eligible works: {0} / {1}",
    pool_sentences: "({0} sentences total)",
    api_usage: "Est. this month: Google {0} / 500k · DeepL {1} / 500k",
    no_eligible: "No works available under current filters",
    original_sentence: "Original (Chinese)",
    english_translation: "English Translation (Reference)",

    translation_google: "Google",
    translation_deepl: "DeepL",
    play_audio: "▶️",
    play_audio_hint: "Open in {0} to hear pronunciation🔊",
    dict_external: "External Dictionary ({0})",
    add_to_vocab: "📝 Add to {0} Vocabulary",
    word_input_placeholder: "Unknown word/phrase to add...",
    add_button: "Add",

    title_vocab: "📚 Vocabulary Notebook",
    select_language: "Select Language",
    all_languages: "All Languages",
    sort_by: "Sort by",
    sort_last_encounter: "Recent Encounters (New→Old)",
    sort_first_encounter: "First Seen (Old→New)",
    sort_encounter_count: "Encounter Count (Most→Least)",
    sort_last_reviewed: "Recently Reviewed (New→Old)",
    sort_alphabetical: "Alphabetical (A-Z)",
    total_words: "Total: {0} words",
    no_words: "No words yet. Start learning!",

    word_entry: "Word:",
    language_label: "Language:",
    dict_link: "🔗Dictionary",
    first_seen: "First seen:",
    last_seen: "Last seen:",
    encounter_count: "Encounters:",
    day_gap: "Days since last:",
    day_gap_first: "First record",
    stats_hp: "Stats:",
    breakthrough: "🌟Breakthrough",
    parent_word: "📖 Root:",
    child_words: "📚 Variants:",

    learning_feedback: "💪 Learning Feedback:",
    seems_familiar: "Seems Familiar",
    dont_know: "Don't Know Well",
    promoted_toast: "Promoted to Hall of Fame!",
    hp_updated_toast: "HP updated",

    personal_note: "📝 Personal Note:",
    edit_note: "✏️ Edit Note",
    save_note: "💾 Save",
    cancel: "Cancel",
    note_saved: "Note saved",

    encounter_history: "📜 Encounter History",
    encounter_index: "Encounter #{0}",
    sentence_zh: "Original:",
    translation_en: "English:",
    translation_target: "{0} Translation:",
    source_work: "Source:",

    title_hall: "🏖️ Hall of Fame",
    subtitle_hall: "Mastered Words (HP=0)",
    mastered_days: "Mastered {0} days ago",
    first_encounter_detail: "📖 First Encounter",
    final_encounter_detail: "🎓 Final Encounter",
    demote_button: "↩️ Return to Vocabulary",
    no_hall_words: "Hall of Fame is empty. Keep learning!",

    title_activity: "📅 Activity Log",
    range_7: "Last 7 days",
    range_30: "Last 30 days",
    range_365: "Last year",
    active_days: "Active Days",
    sentences_translated: "Sentences",
    new_words: "New Words",
    review_count: "Reviews",

    management_tools: "🛠️ Vocabulary Management",
    quick_add: "Quick Add (No Context)",
    quick_add_word: "Word",
    quick_add_button: "➕ Add",
    rename_word: "Rename Word",
    old_word: "Current",
    new_word: "New",
    rename_button: "✏️ Rename",
    set_parent_label: "Set Parent Relationship",
    child_word: "Child Word",
    parent_word_select: "Parent Word",
    set_button: "🔗 Set",
    delete_word_label: "Delete Word",
    delete_word_select: "Select word to delete",
    delete_button: "🗑️ Delete",
    confirm_delete: "Confirm Delete",

    settings_title: "⚙️ Settings",
    ui_language: "🌐 UI Language",
    target_languages: "Target Languages:",
    target_languages_hint: "(Multi-select, 1-2 recommended)",
    comparison_mode: "📊 Dual Translation Comparison",
    comparison_hint: "Show both Google and DeepL translations",
    ao3_mode: "Fun Learning Mode(?)",
    ao3_hint: "🔖 Enable AO3 features",
    rel_filter_title: "Filter by Relationships:",
    rel_filter_hint: "(Uncheck all to draw from all works)",
    rel_select_all: "Select All",
    rel_deselect_all: "Deselect All",
    random_cp: "🎲 Random Ship",
    random_cp_hint: "Ignore ship filter, draw from all works",
    library_path_label: "Library Path",
    library_path_hint: "Location of AO3 HTML files",
    change_path: "Change...",
    copy_path: "Copy Path",
    db_location: "Database Location",
    api_keys: "API Keys",
    google_api_key: "Google Cloud Translation API Key",
    deepl_api_key: "DeepL API Key (Free)",
    save_settings: "💾 Save Settings",
    settings_saved: "Settings saved",

    work_info: "Work Info",
    work_title: "Title:",
    work_id_label: "Works ID:",
    work_published: "Published:",
    work_updated: "Updated:",
    work_series: "Series:",
    ao3_link: "AO3 Link",

    error_api: "API call failed:",
    error_no_library: "Please set library path in Settings first",

    // Draw from specific work (v2.1)
    draw_from_work: "Draw from specific work:",
    work_id_placeholder: "AO3 work ID",
    draw_from_work_btn: "🎲 Draw",
    work_not_found: "Work ID not found in library",
    work_filtered_out: "This work does not match current relationship filter",

    // Pagination (v2.1)
    page_label: "Page {0} / {1}",
    page_jump: "Go to",

    // Search (v2.1)
    search_placeholder: "Search words...",
    search_no_results: "No matching results",
    search_more: "{0} more results...",

    // Scroll buttons (v2.1)
    scroll_top: "↑ Top",
    scroll_bottom: "↓ Bottom",

    // Encounter pagination (v2.1)
    encounter_page: "Encounters page {0} / {1}",

    // Crit system (v2.2)
    crit_evasion_label: "Crit Evasion",
    crit_rate_label: "Crit Rate",
    crit_hit: "💥 Crit!",
    crit_miss: "No crit",
    crit_hit_enemy: "💥 Got crit!",

    // Encounter engine labels (v2.2)
    engine_google: "(Google)",
    engine_deepl: "(DeepL)",

    // Fill-in-the-blank (v2.2)
    nav_fillblank: "✏️ Fill-Blank",
    fillblank_title: "✏️ Naive Fill-in-the-Blank",
    fillblank_draw: "Draw one",
    fillblank_mode_hint: "No-Hint Mode (2× reward)",
    fillblank_mode_no_hint: "No-Hint Mode (2× reward)",
    fillblank_select_lang: "Select target language",
    fillblank_lang_not_eligible: "Not enough words (need at least 4)",
    fillblank_no_sentence: "No suitable sentence found, try again",
    fillblank_correct: "✅ Correct!",
    fillblank_wrong: "❌ Wrong, correct answer: {0}",
    fillblank_source: "Source:",
    fillblank_evasion_title: "Crit Evasion changes:",
    fillblank_check_word: "📖",
    jump_word_not_found: "Word not found. Check language filter.",

    // Manual (v2.2)
    manual_button: "❓ Manual",
    manual_title: "Manual",
    manual_close: "Close",
    manual_disclaimer: "This app was developed with heavy use of Claude for assistant.",
    manual_s1_title: "How to Use",
    manual_s1_body: "Scan library → Draw sentences → Translate → Add words → Review in vocabulary notebook → Fill-blank quiz → Graduate to Hall of Fame",
    manual_s2_title: "HP System",
    manual_s2_body: "New words start at HP = 30. 'Seems Familiar' = base HP -10; 'Don't Know Well' = base HP +20. HP ≤ 0 = graduated to Hall of Fame.",
    manual_s3_title: "Crit Rate",
    manual_s3_body: "Derived from a word's Crit Evasion stat. Crit multiplier ×1.5. 'Seems Familiar' crit = HP -15 (extra damage); 'Don't Know Well' crit = HP +30 (word recovers more).",
    manual_s4_title: "Crit Evasion",
    manual_s4_body: "Adjusted by Fill-Blank quiz performance. Correct → evasion drops (higher crit rate → word graduates faster). Wrong → evasion rises (lower crit rate → word sticks around). No-hints mode doubles the reward for correct answers.",
    manual_s5_title: "Fill-Blank Notes",
    manual_s5_body: "Choices are randomly drawn from your vocab, not semantically curated. Blank matching is naive string match — may miss conjugated/declined forms. That's why it's called 'Naive'.",
    manual_s6_title: "Breakthrough",
    manual_s6_body: "Count of times a word was returned from Hall of Fame to the vocabulary notebook.",
  },
};

/**
 * Get translated text by key
 * @param {string} key - Text key
 * @param {string} lang - Language code ('zh' or 'en')
 * @param  {...any} args - Format arguments
 * @returns {string}
 */
export function t(key, lang = "zh", ...args) {
  const texts = UI_TEXTS[lang] || UI_TEXTS.zh;
  let text = texts[key] || UI_TEXTS.zh[key] || key;

  if (args.length > 0) {
    args.forEach((arg, i) => {
      text = text.replace(`{${i}}`, arg);
    });
  }

  return text;
}

export default t;
