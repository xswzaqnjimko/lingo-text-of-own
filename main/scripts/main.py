
# %% Import ============
import random
from pathlib import Path

import streamlit as st

import time
import json

# import concurrent.futures

# v1.1: 从 dependencies/ 导入模块
from dependencies.config import (
    DEFAULT_LANG, SUPPORTED_LANGUAGES, LANGUAGE_DICTIONARIES,
    TARGET_RELAS, TRANSLATORS, AO3_DOWNLOADS_DIR
)
from dependencies.ao3_parser import (
    norm_for_match, filter_by_relationship, index_local_corpus_core
)
from dependencies.translation import translate_sentence
from dependencies.ui_components import (
    display_translation_block, estimate_size, show_source_info, _fmt, show_flash_message
)

# 生词本数据库模块
import vocabulary_db as vdb



# %% 设置-一些偏好设置（如目标语种/喜好CP） & 个人信息 ============
# v1.1: 偏好设置已移至 dependencies/config.py
# 改默认语言、目标CP、支持语言等，请编辑 config.py

# ————— 默认语言 —————
# 想改默认学习语言时，搜索这个注释或搜索 DEFAULT_LANG
# v1.1: 现在在 config.py 里改
# （20251023-如SUPPORTED_LANGUAGES部分所说，语种按字母表顺序排列，更多待实装……



# ————— 本地文本库配置 —————
# 将来可以添加更多选项，比如：
# - 文库路径
# - 排除某些文件/文件夹
# - 最小/最大文件大小
# - 等等...


# %% 设置-缓存 ============

# 从本地文库准备

@st.cache_data(show_spinner=False)
def index_local_corpus(root_dirs, recursive=True, limit_files=0, only_fff=True):
    """扫描给定目录里的 .html，返回记录列表；缓存以加快后续使用。索引时可选"只认 FFF 文件名模式"（默认开启）"""
    return index_local_corpus_core(root_dirs, recursive=recursive, limit_files=limit_files, only_fff=only_fff)


# %% Streamlit 主界面 ============

st.set_page_config(page_title="整点腿肉机翻小助手（本地文库）", layout="centered")
st.title(" 整点腿肉假装学外语ry ")

# 侧边栏

with st.sidebar:
    # 三向导航：首页 / 生词本 / 总选
    st.markdown("### 📚 页面导航")

    current_view = st.session_state.get('current_view', 'home')

    if current_view == 'home':
        # 在首页，显示两个前往按钮
        if st.button("📖 前往生词本", use_container_width=True, key="nav_to_vocab"):
            st.session_state['current_view'] = 'vocabulary'
            st.rerun()
        if st.button("🏖️ 前往总选名人堂", use_container_width=True, key="nav_to_hof"):
            st.session_state['current_view'] = 'hall_of_fame'
            st.rerun()

    elif current_view == 'vocabulary':
        # 在生词本，可以回首页或去名人堂
        if st.button("🍚 回到首页", use_container_width=True, key="vocab_to_home"):
            st.session_state['current_view'] = 'home'
            st.rerun()
        if st.button("🏖️ 前往总选名人堂", use_container_width=True, key="vocab_to_hof"):
            st.session_state['current_view'] = 'hall_of_fame'
            st.rerun()

    elif current_view == 'hall_of_fame':
        # 在名人堂，可以回首页或去生词本
        if st.button("🍚 回到首页", use_container_width=True, key="hof_to_home"):
            st.session_state['current_view'] = 'home'
            st.rerun()
        if st.button("📖 前往生词本", use_container_width=True, key="hof_to_vocab"):
            st.session_state['current_view'] = 'vocabulary'
            st.rerun()

    st.markdown("---")

    # 显示生词本统计
    try:
        stats = vdb.get_stats()
        st.caption(f"📊 当前第 {stats['current_day']} 天")
        if stats['total_words'] > 0:
            st.caption(f"📝 生词本: {stats['total_words']} 个词")
            for lang, count in stats['by_lang'].items():
                lang_name = SUPPORTED_LANGUAGES.get(lang, {}).get('name', lang)
                st.caption(f"  · {lang_name}: {count} 个")
        if stats.get('hall_of_fame_count', 0) > 0:
            st.caption(f"🎤 总选名人堂: {stats['hall_of_fame_count']} 个词")
    except Exception as e:
        st.caption(f"⚠️ 生词本加载失败：{e}")

    st.markdown("---")

    # 绿色版开关…（。（绿色版记得换本地文库233
    # 20251023-我暂时没有下一个文库，所以就先这样了，不知道日后要不要把上面的文库位置部分搬到if-else里写两次…
    enable_ao3 = st.checkbox(
        "### 边吃边学(?)",
        value=True,
        help="🔖 启用 AO3 功能（CP筛选 & 作品信息）"
    )
    # st.markdown("---")
    if enable_ao3:
        st.markdown("**仅抽以下 Relationships：**")
        sel_targets = st.multiselect(
            "（可多选）",
            options=sorted(TARGET_RELAS),
            default=sorted(TARGET_RELAS),
        )
        st.caption(f"💫 可通过 config.py 中的 TARGET_RELAS 更改目标CP配置")
        # 随机CP（忽略CP筛选，从全部作品抽）
        random_any = st.checkbox(
            "🎲 随机CP",
            value=False,
            help="（忽略 CP 筛选，从全部作品抽）"
        )
    else:
        # 关闭 AO3 功能时的简化设置
        # 自动设置为"全部作品"
        sel_targets = []
        random_any = True
    st.markdown("---")

    st.markdown("**选择目标语言：**")
    selected_langs = st.multiselect(
        "（可多选，建议 1-2 个，多了怕慢= =）",
        options=list(SUPPORTED_LANGUAGES.keys()),
        default=[DEFAULT_LANG],
        format_func=lambda x: SUPPORTED_LANGUAGES[x]['name']
    )
    # 20251024:
    #   现状：在已选择语言抽选并翻译后，再勾选新语言时，页面会多出新语言的"加入生词本"但没有对应翻译
    #   理想状态应该是「检测到语言变化时」「自动在当前英文译版的基础上生成新语言翻译」
    #   但可能会消耗额外的API配额（虽然这大概也消耗不了太多）、逻辑会变复杂、实际使用场景不多（多数时候是先选好语言再抽句子）
    #   所以暂时不管这个了ry：
    st.caption("💡 更改语言选择后，UI丑的话再「抽一句」眼不见心不烦…")
    st.caption(f"💫 可通过 config.py 中的 SUPPORTED_LANGUAGES 和 DEFAULT_LANG 更改目标语言配置")
    st.markdown("---")

    # "多版本对照"开关
    show_comparison = st.sidebar.checkbox(
        "📊 双机翻版本对照模式",
        value=True,  # 默认开启 # 不节省API配额，因为我自己反正是要它俩都翻译一遍的、因为我看俩版本（和多语言选项那里不一样= =）而且都翻译之后就可以随时切开关了ry
        help="开启时显示 Google 和 DeepL 两个版本对比学习/图一乐；关闭时仅显示 Google 翻译（页面清爽一点）；暂未实装更多引擎"
    )
    st.markdown("---")

    st.markdown("**选择翻译引擎：**")
    available_translators = [k for k, v in TRANSLATORS.items() if v['enabled']]
    selected_translators = st.multiselect(
        label="选择翻译引擎",
        options=available_translators,
        default=available_translators[:2],  # 默认前两个可用的
        format_func=lambda x: TRANSLATORS[x]['name']
    )
    # 显示提示
    for t in selected_translators:
        if TRANSLATORS[t].get('note'):
            st.caption(f"💡 {TRANSLATORS[t]['name']}: {TRANSLATORS[t]['note']}")
    st.markdown("---")

    st.markdown("### 本地库设置")
    default_roots = []
    cand = [
        AO3_DOWNLOADS_DIR,
        ]
    for p in cand:
        if p.exists():
            default_roots.append(str(p))
    roots_input = st.text_input(
        "本地库根目录（逗号分隔，可留空用默认）",
        value=", ".join(sorted(set([d for d in default_roots if Path(d).exists()])))
    )
    recursive = st.checkbox("递归扫描子目录", value=True)
    only_fff = st.checkbox("只识别 FFF 文件名（*-ao3_<ID>.html）", value=True) # 20251023-没想好"绿色版（AO3 off）"时要不要也加这句，先这样吧ry
    st.markdown("---")

    if st.sidebar.button("🔄 清缓存 "):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"💡 提醒管理员：建议修改代码时先停止程序= =")

# 索引本地库
root_dirs = [s.strip() for s in roots_input.split(",") if s.strip()]
records, scanned = index_local_corpus(root_dirs, recursive=recursive, only_fff=only_fff)

# 根据侧栏多选决定当前生效的文库内目标（全不选=空；随机CP时忽略）
active_targets = sel_targets[:] if not random_any else []
active_patterns = [s.lower() for s in active_targets]
# 计算可抽取集合
if random_any:
    eligible = records[:]   # 全部作品
else:
    eligible = filter_by_relationship(records, active_targets, active_patterns)


# 生词本查看页面 - 📚 复习模式
if st.session_state.get('current_view') == 'vocabulary':
    show_flash_message()
    st.markdown("## 📚 生词本")

    # # 关闭按钮 【⬅️挪去侧边栏了
    # if st.button("✕ 关闭生词本"):
    #     st.session_state['show_vocabulary'] = False
    #     st.rerun()

    # 语言筛选，含默认语言设置
    vocab_lang = st.selectbox(
        "选择语言",
        options=['all'] + list(SUPPORTED_LANGUAGES.keys()),
        index=1,  # 默认西语
        format_func=lambda x: "全部语言" if x == 'all' else SUPPORTED_LANGUAGES[x]['name']
    )

    # 排序方式选择
    sort_by = st.selectbox(
        "排序方式",
        options=['last_encounter', 'first_encounter', 'encounter_count', 'last_reviewed', 'alphabetical'],
        format_func=lambda x: {
            'last_encounter': '最近遭遇（新→旧）',
            'first_encounter': '最初遭遇（旧→新）',
            'encounter_count': '遭遇次数（多→少）',
            'last_reviewed': '最近温习（新→旧）',
            'alphabetical': '字母表顺序 (A-Z)'
        }[x]
    )

    # 获取生词列表
    try:
        if vocab_lang == 'all':
            vocab_list = vdb.get_vocabulary_list(lang=None, limit=200, sort_by=sort_by)
        else:
            vocab_list = vdb.get_vocabulary_list(lang=vocab_lang, limit=200, sort_by=sort_by)

        if vocab_list:
            st.write(f"共 {len(vocab_list)} 个词")

            # 显示生词列表
            for word_data in vocab_list:
                lang_name = SUPPORTED_LANGUAGES.get(word_data['lang'], {}).get('name', word_data['lang'])
                # 格式：语种 ｜ 词 ｜ 遭遇次数 ｜ 最初/最近遭遇 ｜ HP #我这里用的是中文（全角）"｜"（。
                with st.expander(
                        f"**{lang_name} ｜ {word_data['word']}** ｜ "
                        f"{word_data['encounter_count']}次 ｜ "
                        f"第{word_data['first_seen_day']}天~第{word_data['last_encounter_day']}天 ｜ "
                        f"HP: {word_data['stat_hp']}"
                ):

                    # 词典外链准备
                    lang_code = word_data['lang']
                    word_for_dict = word_data['word']
                    dict_base = LANGUAGE_DICTIONARIES.get(lang_code)
                    # 语种&词典链接
                    if dict_base:
                        import urllib.parse as up
                        word_encoded = up.quote(word_for_dict.lower())
                        dict_url = f"{dict_base}{word_encoded}"
                        st.markdown(f"**词条：** `{word_data['word']}` ｜ " # 方便复制用ry
                                    f"**语言：** {SUPPORTED_LANGUAGES.get(word_data['lang'], {}).get('name', word_data['lang'])} - "
                                    f"[🔗词典释义]({dict_url})"
                                    )
                    st.write(
                        f"**首次遭遇：** 第 {word_data['first_seen_day']} 天 ｜ "
                        f"**最近遭遇：** 第 {word_data['last_encounter_day']} 天 ｜ "
                        f"**遭遇次数：** {word_data['encounter_count']}"
                    )

                    # 获取遭遇记录
                    encounters = vdb.get_word_encounters(word_data['id'])

                    # 计算并显示遭遇间隔
                    if encounters:  # ← 新增：先检查
                        last_day = word_data.get('last_encounter_day')
                        last_candidates = [e for e in encounters if e.get('day') == last_day]
                        if last_candidates:
                            last_enc_for_gap = max(last_candidates, key=lambda e: e.get('encounter_index', -1))
                        elif encounters:
                            last_enc_for_gap = max(encounters, key=lambda e: e.get('encounter_index', -1))
                        else:
                            last_enc_for_gap = None

                        if last_enc_for_gap:
                            gap = last_enc_for_gap.get('day_gap')
                            if gap is not None:
                                st.write(f"**距离上次遭遇：** {gap} 天")
                            else:
                                st.write(f"**距离上次遭遇：** 首次记录")

                    hp = word_data.get('stat_hp')
                    atk = word_data.get('stat_atk')
                    spd = word_data.get('stat_spd')
                    df = word_data.get('stat_def')
                    res = word_data.get('stat_res')
                    breakthrough = word_data.get('breakthrough', 0)

                    # 显示白值
                    if breakthrough > 0:
                        st.write(
                            f"**白值：** HP {_fmt(hp)} ｜ Atk {_fmt(atk)} ｜ Spd {_fmt(spd)} ｜ Def {_fmt(df)} ｜ Res {_fmt(res)} ｜ 🌟突破 {breakthrough}")
                    else:
                        st.write(
                            f"**白值：** HP {_fmt(hp)} ｜ Atk {_fmt(atk)} ｜ Spd {_fmt(spd)} ｜ Def {_fmt(df)} ｜ Res {_fmt(res)}")


                    # 📖 母子词条关系
                    parent_id = word_data.get('parent_id')
                    if parent_id:
                        # 这是子词条，显示母词
                        parent = vdb.get_word_by_id(parent_id)
                        if parent:
                            st.info(f"📖 原形：**{parent['word']}**")
                    else:
                        # 这是母词条，显示子词
                        children = vdb.get_children(word_data['id'])
                        if children:
                            child_words = ', '.join([f"**{c['word']}**" for c in children])
                            st.info(f"📚 变体：{child_words}")

                    # 💪 学习反馈
                    st.markdown("**💪 学习反馈：**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("好像认识", key=f"know_{word_data['id']}", use_container_width=True):
                            success, message, promoted = vdb.decrease_hp(word_data['id'])
                            if success:
                                if promoted:
                                    st.toast(f"词条总选出道！（已返回词条列表）", icon="🎉")  # ← Toast 通知
                                else:
                                    st.toast(f"HP 已更新（已返回词条列表，HP-1不能连点吧✓）")
                                    time.sleep(1)  # 让用户看到通知
                                    st.balloons()
                                st.rerun()
                            else:
                                st.error(message)
                    with col2:
                        if st.button("不太认识", key=f"dont_know_{word_data['id']}", use_container_width=True):
                            success, message = vdb.increase_hp(word_data['id'])
                            if success:
                                st.info(message)
                                st.rerun()
                            else:
                                st.error(message)


                    # 📝 个人注释
                    note = word_data.get('note', '')
                    if note:
                        st.markdown("**📝 个人注释：**")
                        st.info(note)

                    # ✏️ 编辑注释
                    st.markdown("**✏️ 编辑注释：**")

                    note_key = f"note_{word_data['id']}"
                    current_note = word_data.get('note', '')

                    new_note = st.text_area(
                        "个人注释",
                        value=current_note,
                        key=note_key,
                        placeholder="可以记录词性、用法、助记等...",
                        height=80,
                        label_visibility="collapsed"
                    )

                    if st.button("💾 保存注释", key=f"save_note_{word_data['id']}"):
                        success, message = vdb.update_note(word_data['id'], new_note)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

                    st.markdown("---")

                    # 显示遭遇记录详情（初次 + 最近）

                    # —— 初次遭遇（index == 0）——
                    first_enc_list = [e for e in encounters if e.get('encounter_index') == 0]
                    if first_enc_list:
                        enc = first_enc_list[0]
                        st.markdown("**初次遭遇：**")
                        if enc.get('sentence_zh'):
                            st.write(f"中文：{enc['sentence_zh']}")
                        if enc.get('sentence_en_google'):
                            st.write(f"英语对照 (Google)：{enc['sentence_en_google']}")
                        if enc.get('sentence_en_deepl'):
                            st.write(f"英语对照 (DeepL)：{enc['sentence_en_deepl']}")
                        if enc.get('sentence_target_google'):
                            st.write(f"{lang_name} (Google)：{enc['sentence_target_google']}")
                        if enc.get('sentence_target_deepl'):
                            st.write(f"{lang_name} (DeepL)：{enc['sentence_target_deepl']}")
                        show_source_info(enc)
                    else:  # ← 新增：没有初次遭遇记录
                        st.markdown("**初次遭遇：**")
                        st.caption("📝 手动添加的词条，暂无例句记录")

                        # —— 最近遭遇（按 last_encounter_day 匹配；如无则取最大 encounter_index 兜底）——
                        if encounters:  # ← 新增：先检查是否有遭遇记录
                            last_day = word_data.get('last_encounter_day')
                            last_candidates = [e for e in encounters if e.get('day') == last_day]
                            if last_candidates:
                                last_enc = max(last_candidates, key=lambda e: e.get('encounter_index', -1))
                            else:
                                last_enc = max(encounters, key=lambda e: e.get('encounter_index', -1))

                            st.markdown("**最近遭遇：**")
                            if last_enc.get('sentence_zh'):
                                st.write(f"中文：{last_enc['sentence_zh']}")
                            if last_enc.get('sentence_en_google'):
                                st.write(f"英语对照 (Google)：{last_enc['sentence_en_google']}")
                            if last_enc.get('sentence_en_deepl'):
                                st.write(f"英语对照 (DeepL)：{last_enc['sentence_en_deepl']}")
                            if last_enc.get('sentence_target_google'):
                                st.write(f"{lang_name} (Google)：{last_enc['sentence_target_google']}")
                            if last_enc.get('sentence_target_deepl'):
                                st.write(f"{lang_name} (DeepL)：{last_enc['sentence_target_deepl']}")
                            show_source_info(last_enc)
                        else:  # ← 新增：没有遭遇记录时的提示
                            st.markdown("**最近遭遇：**")
                            st.caption("📝 手动添加的词条，暂无例句记录")


        else:
            st.info("生词本还是空的，好强！？")

    except Exception as e:
        st.error(f"加载生词本失败：{e}")

    st.markdown("---")
    st.markdown("**提示：** 关闭生词本后，可以继续抽句子")

    # 🔧 生词本管理工具区
    st.markdown("---")
    st.markdown("## 🔧 管理工具")

    with st.expander("🛠️ 高级操作（谨慎使用）", expanded=False):

        tab1, tab2, tab3, tab4 = st.tabs(["✏️ 重命名词条", "🔗 设置母子关系", "🗑️ 删除词条", "➕ 快速添加"])

        # ===== Tab 1: 重命名 =====
        with tab1:
            st.markdown("### ✏️ 重命名词条")
            st.caption("💡 适用于修改大小写、纠正拼写等，保留所有历史数据")

            col1, col2 = st.columns([2, 1])
            with col1:
                rename_word_input = st.text_input(
                    "输入要重命名的词",
                    key="rename_word_input",
                    placeholder="输入后按回车或点击文本框外部"
                )
            with col2:
                rename_lang = st.selectbox(
                    "语言",
                    options=list(SUPPORTED_LANGUAGES.keys()),
                    format_func=lambda x: SUPPORTED_LANGUAGES[x]['name'],
                    key="rename_lang"
                )

            if rename_word_input:
                # 搜索词条
                found = vdb.search_word(rename_word_input, rename_lang)

                if found:
                    word_data = found[0]  # 应该只有一个
                    st.info(
                        f"找到词条：**{word_data['word']}** ({SUPPORTED_LANGUAGES[word_data['lang']]['name']}) - 遭遇 {word_data['encounter_count']} 次")

                    new_word = st.text_input("输入新名字", key="new_word_input")

                    if new_word and new_word.strip():
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("✓ 确认重命名", key="confirm_rename", type="primary"):
                                success, message = vdb.rename_word(word_data['id'], new_word)
                                if success:
                                    st.session_state['flash_message'] = ('success', message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.warning(f"未找到词条 '{rename_word_input}' ({SUPPORTED_LANGUAGES[rename_lang]['name']})")

        # ===== Tab 2: 设置母子关系 =====
        with tab2:
            st.markdown("### 🔗 设置母子关系")
            st.caption("💡 将变位/复数形式设置为原形的子词条")

            col1, col2 = st.columns([2, 1])
            with col1:
                child_word_input = st.text_input("输入子词（如 espero）",
                                                 key="child_word_input",
                                                 placeholder="输入后按回车或点击文本框外部"
                                                 )
            with col2:
                relation_lang = st.selectbox(
                    "语言",
                    options=list(SUPPORTED_LANGUAGES.keys()),
                    format_func=lambda x: SUPPORTED_LANGUAGES[x]['name'],
                    key="relation_lang"
                )

            if child_word_input:
                # 搜索子词
                found_child = vdb.search_word(child_word_input, relation_lang)

                if found_child:
                    child_data = found_child[0]
                    st.info(
                        f"子词：**{child_data['word']}** ({SUPPORTED_LANGUAGES[child_data['lang']]['name']})")

                    # 显示当前母词（如果有）
                    current_parent_id = child_data.get('parent_id')
                    if current_parent_id:
                        current_parent = vdb.get_word_by_id(current_parent_id)
                        if current_parent:
                            st.warning(f"⚠️ 当前母词：**{current_parent['word']}**")
                            if st.button("🔗 取消关联", key="unlink_parent"):
                                success, message = vdb.set_parent(child_data['id'], None)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            st.markdown("---")

                    # 输入母词
                    parent_word_input = st.text_input("输入母词（原形，如 esperar）",
                                                      key="parent_word_input",
                                                      placeholder="输入后按回车或点击文本框外部",
                                                      )

                    if parent_word_input:
                        # 搜索母词
                        found_parent = vdb.search_word(parent_word_input, relation_lang)

                        if found_parent:
                            parent_data = found_parent[0]

                            # 检查母词是否本身是子词
                            if parent_data.get('parent_id'):
                                st.error(f"❌ '{parent_data['word']}' 本身是其他词的子词条，不能作为母词")
                            else:
                                st.success(f"母词：**{parent_data['word']}**")

                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    if st.button("✓ 确认设置", key="confirm_relation", type="primary"):
                                        success, message = vdb.set_parent(child_data['id'], parent_data['id'])
                                        if success:
                                            st.session_state['flash_message'] = ('success', message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                        else:
                            st.warning(f"未找到母词 '{parent_word_input}'")
                            st.caption("💡 提示：请先将母词添加到生词本")
                else:
                    st.warning(f"未找到子词 '{child_word_input}'")

        # ===== Tab 3: 删除 =====
        with tab3:
            st.markdown("### 🗑️ 删除词条")
            st.caption("⚠️ 将永久删除词条及其所有遭遇记录，不可恢复！")

            col1, col2 = st.columns([2, 1])
            with col1:
                delete_word_input = st.text_input(
                    "输入要删除的词",
                    key="delete_word_input",
                    placeholder="输入后按回车或点击文本框外部"
                )
            with col2:
                delete_lang = st.selectbox(
                    "语言",
                    options=list(SUPPORTED_LANGUAGES.keys()),
                    format_func=lambda x: SUPPORTED_LANGUAGES[x]['name'],
                    key="delete_lang"
                )

            if delete_word_input:
                # 搜索词条
                found = vdb.search_word(delete_word_input, delete_lang)

                if found:
                    word_data = found[0]
                    st.warning(
                        f"⚠️ 找到词条：**{word_data['word']}** ({SUPPORTED_LANGUAGES[word_data['lang']]['name']}) - 遭遇 {word_data['encounter_count']} 次")
                    st.error(
                        f"确定要删除吗？此操作将永久删除该词条及其 {word_data['encounter_count']} 次遭遇记录！")

                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("✓ 确定删除", key="confirm_delete_mgmt", type="primary"):
                            success, message = vdb.delete_word(word_data['id'])
                            if success:
                                st.session_state['flash_message'] = ('success', message)
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.warning(f"未找到词条 '{delete_word_input}' ({SUPPORTED_LANGUAGES[delete_lang]['name']})")

        # ===== Tab 4: 快速添加 =====
        with tab4:
            st.markdown("### ➕ 快速添加词条")
            st.caption("💡 无需例句，直接添加词条到生词本")

            col1, col2 = st.columns([2, 1])
            with col1:
                manual_word = st.text_input("输入词",
                                            key="manual_word_input",
                                            placeholder="输入后按回车或点击文本框外部"
                                            )
            with col2:
                manual_lang = st.selectbox(
                    "语言",
                    options=list(SUPPORTED_LANGUAGES.keys()),
                    format_func=lambda x: SUPPORTED_LANGUAGES[x]['name'],
                    key="manual_lang"
                )

            manual_note = st.text_input("个人注释（可选，日后可更改）", key="manual_note_input",
                                        placeholder="如：动词原形、名词单数等...")

            if manual_word and manual_word.strip():
                if st.button("✓ 添加到生词本", key="add_manual", type="primary"):
                    success, message = vdb.add_word_manual(manual_word, manual_lang, manual_note)
                    if success:
                        st.session_state['flash_message'] = ('success', message)
                        st.rerun()
                    else:
                        st.error(message)

    st.markdown("---")
    st.markdown("**提示：** 关闭生词本后，可以继续抽句子")

    st.stop()  # 显示生词本时，不显示下面的抽句子功能

# 总选页面 - 🎤 已出道词条
if st.session_state.get('current_view') == 'hall_of_fame':
    show_flash_message()
    st.markdown("## 🏖 生词本-总选出道名人堂")

    # 语言筛选
    hof_lang = st.selectbox(
        "选择语言",
        options=['all'] + list(SUPPORTED_LANGUAGES.keys()),
        index=0,
        format_func=lambda x: "全部语言" if x == 'all' else SUPPORTED_LANGUAGES[x]['name'],
        key="hof_lang"
    )

    # 获取总选列表
    try:
        if hof_lang == 'all':
            hof_list = vdb.get_hall_of_fame_list(lang=None, limit=200)
        else:
            hof_list = vdb.get_hall_of_fame_list(lang=hof_lang, limit=200)

        if hof_list:
            st.write(f"共 {len(hof_list)} 个词已出道")

            # 显示词条
            for hof_data in hof_list:
                lang_name = SUPPORTED_LANGUAGES.get(hof_data['lang'], {}).get('name', hof_data['lang'])
                breakthrough = hof_data.get('breakthrough_count', 0)  # 确保有默认值

                # 判断是否满破（1次或以上）
                is_max_breakthrough = breakthrough >= 1
                breakthrough_stars = '⭐' * min(breakthrough, 10)  # FEH教育我们+10是满破……
                breakthrough_text = f"{breakthrough_stars} (满破！)" if is_max_breakthrough else breakthrough_stars if breakthrough > 0 else ""

                # 标题
                # 计算出道天数
                current_day = vdb.get_current_day()
                days_since_promoted = current_day - hof_data.get('last_encounter_day', 0)
                title = f"**{lang_name} ｜ {hof_data['word']}** ｜ 出道第 {days_since_promoted} 天"

                if breakthrough_text:
                    title += f" ｜ {breakthrough_text}"

                # 金框样式（满破）
                if is_max_breakthrough:
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 3px solid gold; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        {title}
                        </div>
                        """, unsafe_allow_html=True)
                        expander = st.expander("展开详情", expanded=False)
                else:
                    expander = st.expander(title, expanded=False)

                with expander:
                    st.write(
                        f"**初次遭遇：** 第 {hof_data['first_encounter_day']} 天 ｜ "
                        f"**出道日期：** 第 {hof_data.get('last_encounter_day', '?')} 天 ｜ "
                        f"**总遭遇：** {hof_data['total_encounters']} 次"
                    )

                    if breakthrough > 0:
                        st.write(f"**突破次数：** {breakthrough}")

                    # 初次遭遇
                    if hof_data.get('first_encounter_data'):
                        first_data = json.loads(hof_data['first_encounter_data'])
                        st.markdown("**初次遭遇：**")
                        if first_data.get('sentence_zh'):
                            st.write(f"中文：{first_data['sentence_zh']}")
                        if first_data.get('sentence_en_google'):
                            st.write(f"英语对照 (Google)：{first_data['sentence_en_google']}")
                        if first_data.get('sentence_en_deepl'):
                            st.write(f"英语对照 (DeepL)：{first_data['sentence_en_deepl']}")
                        if first_data.get('sentence_target_google'):
                            st.write(f"{lang_name} (Google)：{first_data['sentence_target_google']}")
                        if first_data.get('sentence_target_deepl'):
                            st.write(f"{lang_name} (DeepL)：{first_data['sentence_target_deepl']}")
                        # 显示出处
                        if first_data.get('source_title') or first_data.get('source_id'):
                            st.caption("对应出处信息：")
                            title = first_data.get('source_title', '未知')
                            work_id = first_data.get('source_id', '')
                            st.caption(f"出处标题：《{title}》（ID: {work_id}）")

                    # 最终遭遇
                    if hof_data.get('last_encounter_data'):
                        last_data = json.loads(hof_data['last_encounter_data'])
                        st.markdown("**最终遭遇：**")
                        if last_data.get('sentence_zh'):
                            st.write(f"中文：{last_data['sentence_zh']}")
                        if last_data.get('sentence_en_google'):
                            st.write(f"英语对照 (Google)：{last_data['sentence_en_google']}")
                        if last_data.get('sentence_en_deepl'):
                            st.write(f"英语对照 (DeepL)：{last_data['sentence_en_deepl']}")
                        if last_data.get('sentence_target_google'):
                            st.write(f"{lang_name} (Google)：{last_data['sentence_target_google']}")
                        if last_data.get('sentence_target_deepl'):
                            st.write(f"{lang_name} (DeepL)：{last_data['sentence_target_deepl']}")
                        # 显示出处
                        if last_data.get('source_title') or last_data.get('source_id'):
                            st.caption("对应出处信息：")
                            title = last_data.get('source_title', '未知')
                            work_id = last_data.get('source_id', '')
                            st.caption(f"出处标题：《{title}》（ID: {work_id}）")

                    # 回归按钮
                    st.markdown("---")
                    st.warning("⚠️ 觉得还不太熟？")
                    if st.button("回归生词本", key=f"demote_{hof_data['id']}", type="secondary"):
                        success, message = vdb.demote_from_hall_of_fame(hof_data['id'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("还没有已总选出道的词，继续加油！")

    except Exception as e:
        st.error(f"加载总选结果失败：{e}")

    st.markdown("---")
    st.markdown("**提示：** 关闭总选名人堂后，可以继续抽句子")
    st.stop() # 显示时不显示下面的抽句子功能……



# 抽选按钮 - 📖 学习模式（默认）

# 看看缓存有啥ry
total_sentences = sum(len(r['sentences']) for r in records)
cache_size_mb = estimate_size(records) / (1024 * 1024)
st.caption(
    f"📦 缓存：{len(records)} 篇文章，{total_sentences} 个句子，约 {cache_size_mb:.1f} MB"
)

# 诊断框：
if enable_ao3:
    st.markdown(
        f"**已扫描 HTML 文件：** {scanned} 个；"
        f"**可抽取（{'全库随机' if random_any else '匹配关系'}）作品：** {len(eligible)} 篇。"
    )

    if random_any:
        st.caption("（已启用「随机CP」，忽略CP筛选，从全库中抽取句子。）")

        # if active_targets:
        #     by_exact, by_fallback = _diag_breakdown(eligible, active_targets, active_patterns)
        #     st.caption(f"命中分布：精确标签 {len(by_exact)} 篇 · 兜底文本 {len(by_fallback)} 篇")
        # else:
        #     st.caption("（未选择任何 CP，无需筛选）")

        # 可选：列出最多 5 篇"关系表解析为空但全文包含人名共现"的可疑样本

    else:
        if active_targets:
            def _name_cooccur(blob: str) -> bool:
                t = norm_for_match(blob)
                yuri_ok = ("yuri" in t or "yuris" in t) and ("leclerc" in t or "leclair" in t)
                cla_ok = ("claude" in t and "von riegan" in t)
                km_ok = ("kaminaga" in t and "miyoshi" in t)
                return (yuri_ok and cla_ok) or km_ok
            in_paths = {r["path"] for r in eligible}
            suspects = []
            for r in records:
                if r["path"] in in_paths:
                    continue
                if not r.get("relationships"):
                    blob = " ".join([r.get("doc_text_lc", ""), r.get("fname_lc", "")])
                    if _name_cooccur(blob):
                        suspects.append(r)
            if suspects:
                st.caption("⚠️ 可能漏算的样本（前 5 篇）：")
                # 20251023-这里现在会把所有可选的目标CP的潜在漏算样本都列出来（即比如即使只选了神三神，也会把鹿狼鹿的可能篇目写在这里233）但先这样吧ry
                for r in suspects[:5]:
                    st.write(f"- {r.get('title') or '(无标题)'} (ID: {r.get('work_id') or '未知'})")


col_btn1, col_btn2 = st.columns(2)
do_pick = col_btn1.button("抽一句 & 翻译（和右边其实没区别）")
reroll = col_btn2.button("🎲 再来一句（日后要做成“在同一篇里再抽一句”吗🤔️）")

# 抽选句子并输出（避免再往下执行到 random.choice
# 点按钮时：先翻译，再存到 session_state
# 显示时：从 session_state 读取（如果有的话）
# 下次点按钮：覆盖掉旧的
# 不要把"显示句子"放在 if do_pick or reroll: 的里面

if do_pick or reroll:
    rec = random.choice(eligible)
    if not rec["sentences"]:
        st.error("这篇作品没有抽到中文句子，换一篇试试？")
        # # 清空之前的缓存
        # if 'current_sentence' in st.session_state:
        #     del st.session_state['current_sentence']
    else:
        sent = random.choice(rec["sentences"])
        translations = translate_sentence(sent, selected_langs)

        # 保存到 session_state
        st.session_state['current_sentence'] = sent
        st.session_state['current_translations'] = translations
        st.session_state['current_record'] = rec
        st.session_state['current_langs'] = selected_langs

# 显示保存的句子（如果有）
if 'current_sentence' in st.session_state:
    sent = st.session_state['current_sentence']
    translations = st.session_state['current_translations']
    rec = st.session_state['current_record']
    display_langs = st.session_state['current_langs']

    # 显示原文
    st.markdown("### 原文")
    st.write(sent)

    # 显示英语（过渡用）
    st.markdown("### 英语翻译")
    if show_comparison:
        st.write(f"**Google：** {translations['en']['google']}")
        st.write(f"**DeepL：** {translations['en']['deepl']}")
    else:
        st.write(translations['en']['google'])

    # 显示各目标语言
    for lang_code in selected_langs:
        display_translation_block(lang_code, translations, sent, rec, show_comparison)
        if lang_code != selected_langs[-1]:  # 不是最后一个语言
            st.divider()

    # st.divider()

    # 只在启用 AO3 时显示作品信息
    if enable_ao3:
        st.divider()

        st.markdown("### 作品信息")

        work_id = rec.get("work_id") or "未知"
        title = rec.get("title") or "(无标题)"
        published = rec.get("published") or "(未知)"
        updated = rec.get("updated") or "(未知)"
        ao3_link = f"https://archiveofourown.org/works/{work_id}" if work_id and work_id.isdigit() else None

        # 所属 Series
        series_list = rec.get("series", [])
        if series_list:
            st.markdown("**所属 Series：** " + " | ".join(
                f"[{s.get('title', '')}]({s.get('href', '')})" if s.get('href') else s.get('title', '')
                for s in series_list
            ))

        meta_cols = st.columns(2)
        with meta_cols[0]:
            st.write(f"**标题：** {title}")
            st.write(f"**works ID：** {work_id}")
            if ao3_link:
                st.write(f"[AO3 链接]({ao3_link})")
        with meta_cols[1]:
            st.write(f"**发布：** {published}")
            st.write(f"**更新：** {updated}")



# End
