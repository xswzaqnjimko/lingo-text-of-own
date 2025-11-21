# i18n.py - 国际化文本管理
# 中英文 UI 切换支持

UI_TEXTS = {
    "zh": {
        # 侧边栏导航
        "nav_home": "🍚 回到首页",
        "nav_vocab": "📖 前往生词本",
        "nav_vocab_short": "📖 生词本",
        "nav_hall": "🏖️ 前往总选名人堂",
        "nav_hall_short": "🏆 名人堂",
        
        # 统计信息
        "stats_day": "📊 当前第 {} 天",
        "stats_vocab": "📝 生词本: {} 个词",
        "stats_hall": "🎤 总选名人堂: {} 个词",
        "stats_by_lang": "  · {}: {} 个",
        
        # 主页
        "title_home": "🍚 整点腿肉机翻",
        "subtitle_home": "从自己喜欢的文本学语言",
        "draw_sentence": "🎲 抽句子吃",
        "no_eligible": "当前筛选条件下无可用作品",
        "original_sentence": "原文（中文）",
        "english_translation": "英语翻译（过渡&对照用）",
        
        # 翻译显示
        "translation_google": "Google",
        "translation_deepl": "DeepL",
        "play_audio": "▶️",
        "play_audio_hint": "在 {} 打开此句听机器一读🔊",
        "dict_external": "外部词典（{}）",
        "add_to_vocab": "📝 加入{}生词本",
        "word_input_placeholder": "不太认识！的词/词组不想手抄也起码该复制粘贴一次...",
        "add_button": "加入",
        
        # 生词本页面
        "title_vocab": "📚 生词本",
        "select_language": "选择语言",
        "all_languages": "全部语言",
        "sort_by": "排序方式",
        "sort_last_encounter": "最近遭遇（新→旧）",
        "sort_first_encounter": "最初遭遇（旧→新）",
        "sort_encounter_count": "遭遇次数（多→少）",
        "sort_last_reviewed": "最近温习（新→旧）",
        "sort_alphabetical": "字母表顺序 (A-Z)",
        "total_words": "共 {} 个词",
        "no_words": "还没有生词哦，开始学习吧！",
        
        # 词条详情
        "word_entry": "词条：",
        "language": "语言：",
        "dict_link": "🔗词典释义",
        "first_seen": "首次遭遇：",
        "last_seen": "最近遭遇：",
        "encounter_count": "遭遇次数：",
        "day_gap": "距离上次遭遇：",
        "day_gap_first": "首次记录",
        "stats_hp": "白值：",
        "breakthrough": "🌟突破",
        "parent_word": "📖 原形：",
        "child_words": "📚 变体：",
        
        # 学习反馈
        "learning_feedback": "💪 学习反馈：",
        "seems_familiar": "好像认识",
        "dont_know": "不太认识",
        "promoted_toast": "词条总选出道！（已返回词条列表）",
        "hp_updated_toast": "HP 已更新（已返回词条列表，HP-1不能连点吧✓）",
        
        # 个人注释
        "personal_note": "📝 个人注释：",
        "edit_note": "✏️ 编辑注释",
        "save_note": "💾 保存",
        "cancel": "取消",
        "note_saved": "注释已保存",
        
        # 遭遇历史
        "encounter_history": "📜 遭遇历史",
        "encounter_index": "遭遇 #{}",
        "sentence_zh": "原文：",
        "translation_en": "英文翻译：",
        "translation_target": "{}翻译：",
        "source_work": "出处：",
        
        # 名人堂
        "title_hall": "🏖️ 总选名人堂",
        "subtitle_hall": "已掌握的词条（HP=0）",
        "mastered_days": "{}天前掌握",
        "first_encounter_detail": "📖 初次遭遇",
        "final_encounter_detail": "🎓 最终遭遇",
        "demote_button": "↩️ 退回生词本",
        "no_hall_words": "名人堂还是空的，继续加油！",
        
        # 管理工具
        "management_tools": "🛠️ 生词本管理工具",
        "quick_add": "快速添加词条（无例句）",
        "quick_add_word": "词条内容",
        "quick_add_button": "➕ 添加",
        "rename_word": "重命名词条",
        "old_word": "原词条",
        "new_word": "新词条",
        "rename_button": "✏️ 重命名",
        "set_parent": "设置母词关系",
        "child_word": "子词条",
        "parent_word_select": "母词条",
        "set_button": "🔗 设置",
        "delete_word": "删除词条",
        "delete_word_select": "选择要删除的词条",
        "delete_button": "🗑️ 删除",
        "confirm_delete": "确认删除",
        
        # 设置选项
        "settings_title": "⚙️ 设置",
        "ui_language": "🌐 界面语言",
        "target_languages": "选择目标语言：",
        "target_languages_hint": "（可多选，建议 1-2 个，多了怕慢= =）",
        "comparison_mode": "📊 双机翻版本对照模式",
        "comparison_hint": "开启时显示 Google 和 DeepL 两个版本对比学习/图一乐；关闭时仅显示 Google 翻译（页面清爽一点）",
        "ao3_mode": "边吃边学(?)",
        "ao3_hint": "🔖 启用 AO3 功能（CP筛选 & 作品信息）",
        "clear_cache": "🔄 清缓存",
        
        # AI 功能
        "ai_features": "🤖 AI 增强功能",
        "ai_status": "Claude API 状态",
        "ai_configured": "✅ 已配置",
        "ai_not_configured": "⚠️ 未配置",
        "analyze_word": "🔍 用 AI 分析",
        "suggest_related": "💡 推荐相关词学习",
        "analyze_difficulty": "📊 分析学习难度",
        "ai_analyzing": "🤖 AI 正在分析...",
        "ai_semantic": "🤖 AI 正在分析语义关联...",
        
        # AI 分析结果
        "parent_suggestions": "🌳 可能的母词（原形）：",
        "child_suggestions": "🌱 可能的变体：",
        "generated_note": "📝 AI 生成的学习笔记：",
        "save_note_button": "💾 保存此笔记",
        "note_saved_success": "笔记已保存！",
        "related_words_title": "🎯 推荐一起学习的词：",
        "recommendation_reason": "📌 推荐理由：",
        "learning_strategy": "💡 学习策略：",
        "difficulty_priority": "优先级：",
        "difficulty_high": "⚠️ 高优先级",
        "difficulty_medium": "📊 中等优先级",
        "difficulty_low": "✅ 学习顺利",
        "ai_suggestions": "💡 AI 建议：",
        "recommended_review": "📅 建议复习频率：",
        
        # 错误信息
        "error_api": "API 调用失败：",
        "error_analysis": "分析失败：",
        "error_no_data": "数据不足，多复习几次后再试！",
    },
    
    "en": {
        # Sidebar navigation
        "nav_home": "🍚 Back to Home",
        "nav_vocab": "📖 Go to Vocabulary",
        "nav_vocab_short": "📖 Vocabulary",
        "nav_hall": "🏖️ Go to Hall of Fame",
        "nav_hall_short": "🏆 Hall of Fame",
        
        # Statistics
        "stats_day": "📊 Day {}",
        "stats_vocab": "📝 Vocabulary: {} words",
        "stats_hall": "🎤 Hall of Fame: {} words",
        "stats_by_lang": "  · {}: {} words",
        
        # Home page
        "title_home": "🍚 Language Learning from Literature",
        "subtitle_home": "Learn languages through texts you love",
        "draw_sentence": "🎲 Draw a sentence",
        "no_eligible": "No works available under current filters",
        "original_sentence": "Original (Chinese)",
        "english_translation": "English Translation (Reference)",
        
        # Translation display
        "translation_google": "Google",
        "translation_deepl": "DeepL",
        "play_audio": "▶️",
        "play_audio_hint": "Open in {} to hear pronunciation🔊",
        "dict_external": "External Dictionary ({})",
        "add_to_vocab": "📝 Add to {} Vocabulary",
        "word_input_placeholder": "Unknown word/phrase to add...",
        "add_button": "Add",
        
        # Vocabulary page
        "title_vocab": "📚 Vocabulary Notebook",
        "select_language": "Select Language",
        "all_languages": "All Languages",
        "sort_by": "Sort by",
        "sort_last_encounter": "Recent Encounters (New→Old)",
        "sort_first_encounter": "First Seen (Old→New)",
        "sort_encounter_count": "Encounter Count (Most→Least)",
        "sort_last_reviewed": "Recently Reviewed (New→Old)",
        "sort_alphabetical": "Alphabetical (A-Z)",
        "total_words": "Total: {} words",
        "no_words": "No words yet. Start learning!",
        
        # Word details
        "word_entry": "Word:",
        "language": "Language:",
        "dict_link": "🔗Dictionary",
        "first_seen": "First seen:",
        "last_seen": "Last seen:",
        "encounter_count": "Encounters:",
        "day_gap": "Days since last:",
        "day_gap_first": "First record",
        "stats_hp": "Stats:",
        "breakthrough": "🌟Breakthrough",
        "parent_word": "📖 Root:",
        "child_words": "📚 Variants:",
        
        # Learning feedback
        "learning_feedback": "💪 Learning Feedback:",
        "seems_familiar": "Seems Familiar",
        "dont_know": "Don't Know Well",
        "promoted_toast": "Promoted to Hall of Fame!",
        "hp_updated_toast": "HP updated (returning to list)",
        
        # Personal notes
        "personal_note": "📝 Personal Note:",
        "edit_note": "✏️ Edit Note",
        "save_note": "💾 Save",
        "cancel": "Cancel",
        "note_saved": "Note saved",
        
        # Encounter history
        "encounter_history": "📜 Encounter History",
        "encounter_index": "Encounter #{}",
        "sentence_zh": "Original:",
        "translation_en": "English:",
        "translation_target": "{} Translation:",
        "source_work": "Source:",
        
        # Hall of Fame
        "title_hall": "🏖️ Hall of Fame",
        "subtitle_hall": "Mastered Words (HP=0)",
        "mastered_days": "Mastered {} days ago",
        "first_encounter_detail": "📖 First Encounter",
        "final_encounter_detail": "🎓 Final Encounter",
        "demote_button": "↩️ Return to Vocabulary",
        "no_hall_words": "Hall of Fame is empty. Keep learning!",
        
        # Management tools
        "management_tools": "🛠️ Vocabulary Management",
        "quick_add": "Quick Add (No Context)",
        "quick_add_word": "Word",
        "quick_add_button": "➕ Add",
        "rename_word": "Rename Word",
        "old_word": "Current",
        "new_word": "New",
        "rename_button": "✏️ Rename",
        "set_parent": "Set Parent Relationship",
        "child_word": "Child Word",
        "parent_word_select": "Parent Word",
        "set_button": "🔗 Set",
        "delete_word": "Delete Word",
        "delete_word_select": "Select word to delete",
        "delete_button": "🗑️ Delete",
        "confirm_delete": "Confirm Delete",
        
        # Settings
        "settings_title": "⚙️ Settings",
        "ui_language": "🌐 UI Language",
        "target_languages": "Target Languages:",
        "target_languages_hint": "(Multi-select, 1-2 recommended)",
        "comparison_mode": "📊 Dual Translation Comparison",
        "comparison_hint": "Show both Google and DeepL translations",
        "ao3_mode": "Fun Learning Mode(?)",
        "ao3_hint": "🔖 Enable AO3 features",
        "clear_cache": "🔄 Clear Cache",
        
        # AI features
        "ai_features": "🤖 AI Features",
        "ai_status": "Claude API Status",
        "ai_configured": "✅ Configured",
        "ai_not_configured": "⚠️ Not Configured",
        "analyze_word": "🔍 Analyze with AI",
        "suggest_related": "💡 Suggest Related Words",
        "analyze_difficulty": "📊 Analyze Difficulty",
        "ai_analyzing": "🤖 AI is analyzing...",
        "ai_semantic": "🤖 AI is analyzing semantic relations...",
        
        # AI analysis results
        "parent_suggestions": "🌳 Potential Parent Words (Root Forms):",
        "child_suggestions": "🌱 Potential Children (Variants):",
        "generated_note": "📝 AI-Generated Note:",
        "save_note_button": "💾 Save This Note",
        "note_saved_success": "Note saved!",
        "related_words_title": "🎯 Recommended Words to Review:",
        "recommendation_reason": "📌 Reason:",
        "learning_strategy": "💡 Strategy:",
        "difficulty_priority": "Priority:",
        "difficulty_high": "⚠️ High Priority",
        "difficulty_medium": "📊 Medium Priority",
        "difficulty_low": "✅ Doing Well",
        "ai_suggestions": "💡 AI Suggestions:",
        "recommended_review": "📅 Recommended Review:",
        
        # Error messages
        "error_api": "API call failed:",
        "error_analysis": "Analysis failed:",
        "error_no_data": "Not enough data yet. Review more times!",
    }
}


def get_text(key: str, lang: str = "zh", *args) -> str:
    """
    获取翻译文本
    
    Args:
        key: 文本键
        lang: 语言代码 ('zh' 或 'en')
        *args: 格式化参数
    
    Returns:
        翻译后的文本
    """
    text = UI_TEXTS.get(lang, UI_TEXTS["zh"]).get(key, key)
    if args:
        try:
            return text.format(*args)
        except:
            return text
    return text


# 快捷函数
def t(key: str, *args, lang: str = "zh") -> str:
    """get_text 的简写形式"""
    return get_text(key, lang, *args)
