# translation.py - 翻译模块
# v1.1: 从 整点腿肉机翻.py 中提取出来的翻译相关函数
# 包括：DeepL翻译、Google翻译、词典链接生成、TTS链接等

import re
import urllib.parse as up

import requests
from deep_translator import GoogleTranslator

from dependencies.config import DEEPL_API_KEY, DEEPL_API_URL, SUPPORTED_LANGUAGES, LANGUAGE_DICTIONARIES


# DeepL翻译
def deepl_translate(text, source_lang, target_lang):
    if not DEEPL_API_KEY:
        return "(DeepL 未配置密钥)"

    # 使用 Authorization header（DeepL 新标准，2026-01-15 后旧方式失效）
    headers = {
        'Authorization': f'DeepL-Auth-Key {DEEPL_API_KEY}'
    }

    data = {
        'text': text,
        'source_lang': source_lang.upper(),
        'target_lang': target_lang.upper()
    }

    try:
        r = requests.post(DEEPL_API_URL, data=data, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()['translations'][0]['text']
    except Exception as e:
        return f"(DeepL 调用失败：{e})"


# def baidu_translate(text, from_lang='zh', to_lang='en'):
#     # 百度翻译需要：APP ID + 密钥
#     # 申请：https://fanyi-api.baidu.com/
#     # 标准版：免费 5万字符/月（QPS=1，够个人用）
#     # 以上三行：ClaudeSonnet4.5说的，我还没查证（。
#     if not BAIDU_APP_ID or not BAIDU_API_KEY:
#         return "(百度翻译未配置)"
#
#     salt = random.randint(32768, 65536)
#     sign_str = f"{BAIDU_APP_ID}{text}{salt}{BAIDU_API_KEY}"
#     sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
#
#     url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
#     params = {
#         'q': text,
#         'from': from_lang,
#         'to': to_lang,
#         'appid': BAIDU_APP_ID,
#         'salt': salt,
#         'sign': sign
#     }
#
#     try:
#         r = requests.get(url, params=params, timeout=10)
#         result = r.json()
#         if 'trans_result' in result:
#             return result['trans_result'][0]['dst']
#         return f"(百度翻译错误：{result.get('error_msg', '未知')})"
#     except Exception as e:
#         return f"(百度翻译调用失败：{e})"


def translate_sentence(sent: str, target_langs: list[str]) -> dict:
    """
    翻译一个中文句子到多个目标语言（简单版本）；暂未用并发翻译
    Args:
        sent: 中文句子
        target_langs: 目标语言代码列表，如['es', 'fr']
    Returns:
        {
            'en': {'google': ..., 'deepl': ...},  # 英语（过渡&对照用）
            'es': {'google': ..., 'deepl': ...},  # 各目标语言
            'fr': {'google': ..., 'deepl': ...},
        }
    """
    results = {}
    # 第一步：中文 → 英文（所有语言都需要）
    google_en = GoogleTranslator(source='zh-CN', target='en').translate(sent)
    deepl_en = deepl_translate(sent, 'zh', 'en')

    results['en'] = {
        'google': google_en,
        'deepl': deepl_en
    }

    # 第二步：英文 → 各目标语言
    for lang in target_langs:
        google_target = GoogleTranslator(source='en', target=lang).translate(google_en)
        deepl_target = deepl_translate(deepl_en, 'en', lang)

        results[lang] = {
            'google': google_target,
            'deepl': deepl_target
        }

    return results

# 不同平台的语言代码不一样，需要映射（暂时未使用，将来如果支持多翻译器可以用）
# LANG_CODE_MAP = {
#     'google': {'zh': 'zh-CN', 'en': 'en', 'es': 'es', 'fr': 'fr', 'it': 'it'},
#     'deepl': {'zh': 'ZH', 'en': 'EN', 'es': 'ES', 'fr': 'FR', 'it': 'IT'},
#     'baidu': {'zh': 'zh', 'en': 'en', 'es': 'spa', 'fr': 'fra', 'it': 'it'},
# }


# 词典链接

def extract_words(text: str, pattern: str) -> list[str]:
    """根据正则模式提取单词"""
    if not text:
        return []
    # 去掉常见标点
    text = text.replace("¿", "").replace("¡", "").replace("?", "").replace("!", "")
    tokens = re.findall(pattern, text)
    return tokens


def generate_dictionary_links(google_text: str, deepl_text: str,
                              lang_code: str) -> tuple[list[str], list[str]]:
    """
    生成词典链接

    Args:
        google_text: Google 翻译结果
        deepl_text: DeepL 翻译结果
        lang_code: 语言代码（如 'es'）

    Returns:
        (google_chips, deepl_extra_chips)
    """
    lang_config = SUPPORTED_LANGUAGES.get(lang_code)
    if not lang_config:
        return [], []

    word_pattern = lang_config.get('word_pattern', r'[A-Za-z]+')
    dict_base = LANGUAGE_DICTIONARIES.get(lang_code, '')

    if not dict_base:
        return [], []

    # 提取 Google 翻译的词（作为"基础词集"）
    google_words = extract_words(google_text, word_pattern)
    google_words_lower = set(w.lower() for w in google_words)

    google_chips = []
    for word in google_words:
        word_lower = word.lower()
        url = f"{dict_base}{up.quote(word_lower)}"
        chip = f"[{word}]({url})"
        google_chips.append(chip)

    # 提取 DeepL 翻译中"Google 没有的新词"
    deepl_words = extract_words(deepl_text, word_pattern)
    deepl_extra_chips = []
    for word in deepl_words:
        word_lower = word.lower()
        if word_lower not in google_words_lower:
            url = f"{dict_base}{up.quote(word_lower)}"
            chip = f"[{word}]({url})"
            deepl_extra_chips.append(chip)

    return google_chips, deepl_extra_chips


def get_tts_link(text: str, lang_code: str, engine: str) -> str | None:
    """
    生成 TTS（机器朗读）链接

    Args:
        text: 要朗读的文本
        lang_code: 语言代码
        engine: 'google' 或 'deepl'

    Returns:
        URL 字符串，或 None
    """
    lang_config = SUPPORTED_LANGUAGES.get(lang_code)
    if not lang_config:
        return None

    if engine == 'google':
        tts_func = lang_config.get('tts_google')
    elif engine == 'deepl':
        tts_func = lang_config.get('tts_deepl')
    else:
        return None

    if tts_func and text:
        return tts_func(text)

    return None
