# config.py - 集中配置文件
# v1.1: 所有路径、API密钥、偏好设置集中在此，方便日后修改
# 搬家/改路径/换API Key时只改这个文件就行

import os
import urllib.parse as up
from pathlib import Path
from datetime import date


# %% 路径配置 ============
# PROJECT_ROOT 指向 main/ 文件夹
PROJECT_ROOT = Path(__file__).parent.parent.parent  # dependencies/ -> scripts/ -> main/

DATA_DIR = PROJECT_ROOT / "data"
LIBRARY_DIR = DATA_DIR / "library" / "ao3"
AO3_DOWNLOADS_DIR = LIBRARY_DIR / "ao3_downloads"
URLS_ALL_FILE = LIBRARY_DIR / "urls_all.txt"
VOCAB_DB_PATH = DATA_DIR / "vocabulary_notebook" / "vocabulary.db"


# %% AO3 默认设置（用于 ao3_collect_urls.py & ao3_download.py） ============
DEFAULT_AO3_USER_URL = "https://archiveofourown.org/users/{your_user}}/works" # 请根据个人喜好更换

# ao3_collect_urls.py 自动重试设置（跑完就走，不用盯着）
COLLECT_MAX_AUTO_RETRIES = 5       # 最多自动重试几轮
COLLECT_RETRY_WAIT_SECONDS = 60    # 每轮失败后等多久再试（秒）

# ao3_download.py 失败重试设置
DOWNLOAD_RETRY_WAIT_SECONDS = 30   # 批量下载后，重试失败URL前等多久（秒）


# %% API Keys 配置 ============
# （优先级：环境变量 > 硬编码 > st.secrets）
# 意思一下，还是那句话，有需要还可以再加……
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY") # 请在lingo_text_launcher.txt里添加，运行时提供即可
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
# Free 端点,免费 50 万字符/月的配额，超了当月就会被拒，不会扣费
# https://developers.deepl.com/docs/resources/usage-limits

# BAIDU_APP_ID = os.getenv("BAIDU_APP_ID") or None
# BAIDU_API_KEY = os.getenv("BAIDU_API_KEY") or None


# %% 生词本配置 ============
BIRTH_DATE = date(2025, 10, 10)  # 程序生日
MAX_ENCOUNTERS = 128  # 每个词最多保留128次遭遇记录


# %% 偏好设置（如目标语种/喜好CP） ============

# ————— 默认语言 —————
# 想改默认学习语言时改这里
DEFAULT_LANG = 'es'  # 暂时默认语言：'es'=西语

# ————— 支持的语言配置 —————

# 语言代码 + 对应词典链接（供翻译页面和生词本使用）
# 暂时按字母表顺序排列语种了
# 语种可以随需求继续往上加……和，词典仅供参考，发现更喜欢词典的可以更新……

LANGUAGE_DICTIONARIES = {
    'es': 'https://www.ingles.com/traductor/',  # baka：我个人暂时感觉还挺好用的一个……
    'fr': 'https://dictionnaire.lerobert.com/definition/',
    'it': 'https://dizionari.corriere.it/dizionario_italiano/'
}

# 语言详细配置（TTS链接、词形正则等）
SUPPORTED_LANGUAGES = {
    'es': {
        'name': '西语',
        'tts_google': lambda text: f"https://translate.google.com/?sl=es&tl=en&text={up.quote_plus(text)}&op=translate",
        'tts_deepl': lambda text: f"https://www.deepl.com/translator#es/en/{up.quote(text, safe='')}",
        'word_pattern': r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"  # 西语字母
    },
    'fr': {
        'name': '法语',
        'tts_google': lambda text: f"https://translate.google.com/?sl=fr&tl=en&text={up.quote_plus(text)}&op=translate",
        'tts_deepl': lambda text: f"https://www.deepl.com/translator#fr/en/{up.quote(text, safe='')}",
        'word_pattern': r"[A-Za-zÀ-ÿÇçŒœ]+"  # 法语字母（包含重音符号和连字）
    },
    'it': {
        'name': '意大利语',
        'tts_google': lambda text: f"https://translate.google.com/?sl=it&tl=en&text={up.quote_plus(text)}&op=translate",
        'tts_deepl': lambda text: f"https://www.deepl.com/translator#it/en/{up.quote(text, safe='')}",
        'word_pattern': r"[A-Za-zÀÈÉÌÒÙàèéìòù]+"  # 意大利语字母（包含重音符号）
    },
}
# 20251024-现在用了 LANGUAGE_DICTIONARIES 和 SUPPORTED_LANGUAGES 两个变量存语言设置，
#   但是合并进比如 SUPPORTED_LANGUAGES 的话，我更新、尤其是更新词典的时候容易懒得下去翻它都有啥（。
#   所以先这样吧（。


# ————— 目标CP配置 —————
# （AO3 固定写法，尽量精确匹配，用于 设置-只选特定CP ）
TARGET_RELAS = [
    "Yuris Leclair | Yuri Leclerc/Claude von Riegan",
    "Kaminaga/Miyoshi (Joker Game)",
]   # 可以随个人喜好改其他CP（ry


# %% 翻译器配置 ============

# 翻译器插件化
# 同上，可以随需求继续往上加/改……
TRANSLATORS = {
    'google': {
        'name': 'Google',
        'requires_key': False,
        'requires_proxy': True,  # 国内需翻墙
        'enabled': True,
        'note': '需要科学上网'
    },
    'deepl': {
        'name': 'DeepL',
        'requires_key': True,
        'requires_proxy': False,
        'enabled': bool(DEEPL_API_KEY),  # 自动检测是否有key
        'note': '需要API密钥（免费50万字符/月），DeepL 密钥可通过环境变量 DEEPL_API_KEY 或 st.secrets 配置' # 超了当月就会被拒，不会扣费
    # },
    # 'baidu': {
    #     'name': '百度翻译',
    #     'requires_key': True,  # 百度也需要key，但申请容易
    #     'requires_proxy': False,
    #     'enabled': False,  # 默认关闭，需要用户配置
    #     'note': '国内可用，需要百度翻译API密钥'
    }
}
