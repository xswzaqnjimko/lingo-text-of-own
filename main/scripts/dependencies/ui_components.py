# ui_components.py - Streamlit UI 组件模块
# v1.1: 从 整点腿肉机翻.py 中提取出来的 Streamlit 显示相关函数

import sys
import urllib.parse as up

import streamlit as st

from dependencies.config import SUPPORTED_LANGUAGES, LANGUAGE_DICTIONARIES
from dependencies.translation import generate_dictionary_links, get_tts_link
import vocabulary_db as vdb


# Streamlit输出模块

def display_translation_block(lang_code, translations, original_sentence, record, show_comparison=True):
    """
    显示某个目标语言的翻译结果

    Args:
        show_comparison: 是否显示双引擎对照（True=显示Google+DeepL，False=仅显示Google）
        （202510-暂时只打算用这两个引擎、不打算加更多翻译器的接口，所以先这么照着只有俩翻译器的版本硬写了……
    """
    lang_config = SUPPORTED_LANGUAGES.get(lang_code)
    if not lang_config:
        return

    lang_name = lang_config['name']
    lang_trans = translations.get(lang_code, {})

    st.markdown(f"### {lang_name}翻译")

    if show_comparison:
        # ===== 双引擎对照模式 =====

        # Google 版本
        if lang_trans.get('google'):
            g_url = get_tts_link(lang_trans['google'], lang_code, 'google')
            col_left, col_right = st.columns([1, 9])
            with col_left:
                st.markdown("**Google**")
            with col_right:
                if g_url:
                    st.link_button("▶️", g_url, help=f"在 Google Translate 打开此句听机器一读🔊")
            st.write(lang_trans['google'])

        # DeepL 版本
        if lang_trans.get('deepl') and isinstance(lang_trans['deepl'], str):
            d_url = get_tts_link(lang_trans['deepl'], lang_code, 'deepl')
            col_left, col_right = st.columns([1, 9])
            with col_left:
                st.markdown("**DeepL**")
            with col_right:
                if d_url:
                    st.link_button("▶️", d_url, help=f"在 DeepL 打开此句听机器一读🔊")
            st.write(lang_trans['deepl'])

        # 词典链接（双版本）
        st.markdown(f"**外部词典（{lang_name}）**")
        chips_google, chips_deepl_extra = generate_dictionary_links(
            lang_trans.get('google', ''),
            lang_trans.get('deepl', ''),
            lang_code
        )
        if chips_google:
            st.write(" · ".join(chips_google[:120]))
        if chips_deepl_extra:
            st.write(" · ".join(chips_deepl_extra[:120]))

    else:
        # ===== 简洁模式（仅 Google）=====

        if lang_trans.get('google'):
            g_url = get_tts_link(lang_trans['google'], lang_code, 'google')

            # 播放按钮在右上角
            if g_url:
                col_text, col_button = st.columns([9, 1])
                with col_text:
                    st.write(lang_trans['google'])
                with col_button:
                    st.link_button("▶️", g_url, help=f"在 Google Translate 打开此句听机器一读🔊")
            else:
                st.write(lang_trans['google'])

            # 词典链接（仅基于 Google 版本）
            st.markdown(f"**外部词典（{lang_name}）**")
            chips_google, _ = generate_dictionary_links(
                lang_trans.get('google', ''),
                '',  # 不需要 DeepL 版本
                lang_code
            )
            if chips_google:
                st.write(" · ".join(chips_google[:120]))

    # 生词本输入框
    st.markdown(f"**📝 加入{lang_name}生词本**")
    with st.form(key=f"vocab_form_{lang_code}_{hash(original_sentence)}"):  # 用hash避免重复key
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            new_word = st.text_input(
                "不认识的词/词组",
                key=f"vocab_input_{lang_code}_{hash(original_sentence)}",
                placeholder="不太认识！的词/词组不想手抄也起码该复制粘贴一次...",
                label_visibility="collapsed"
            )
        with col_btn:
            submitted = st.form_submit_button("加入", use_container_width=True)

        if submitted and new_word.strip():
            # 添加到生词本
            is_new, message = vdb.add_word(
                word=new_word.strip(),
                lang=lang_code,
                sentence_zh=original_sentence,
                translations=translations,
                source_info=record
            )

            if is_new:
                st.success(message)
            else:
                st.info(message)


# 看看缓存有多少ry

def estimate_size(obj, seen=None):
    """快速估算对象大小（MB）"""
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(estimate_size(k, seen) + estimate_size(v, seen)
                    for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(estimate_size(item, seen) for item in obj)

    return size


# %% 设置-生词本UI相关 ============

# 显示出处信息
def show_source_info(enc):
    # AO3兼容、未来扩展可统一命名为"出处标题""出处详情""出处注释"
    title = enc.get('work_title') or enc.get('source_title')
    work_id = enc.get('work_id') or enc.get('source_id')
    series = enc.get('series_title') or enc.get('source_note')
    if title or work_id or series:
        st.caption("对应出处信息：")
        if title:
            st.caption(f"出处标题：《{title}》")
        if work_id:
            ao3_link = f"https://archiveofourown.org/works/{work_id}" if str(work_id).isdigit() else None
            if ao3_link:
                st.caption(f"Works ID: [{work_id}]({ao3_link})")
            else:
                st.caption(f"Works ID: {work_id}")
        if series:
            st.caption(f"Series: {series}")


def _fmt(v):
    """格式化白值显示"""
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


def show_flash_message():
    """显示闪现消息（一次性提示）"""
    if 'flash_message' in st.session_state:
        msg_type, msg = st.session_state['flash_message']
        if msg_type == 'success':
            st.success(msg)
        elif msg_type == 'error':
            st.error(msg)
        elif msg_type == 'info':
            st.info(msg)
        elif msg_type == 'warning':
            st.warning(msg)
        del st.session_state['flash_message']
