# lingo-text-of-own: Language Learning from Literature - Vocabulary Database Module
# SQLite database operations for vocabulary tracking
#
# Copyright (C) 2025 xswzaqnjimko
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Documentation and comments in this file are licensed under CC BY 4.0.
# See LICENSE-DOCS for details.

# Currently (as of Nov. 2025) Chinese UI; English version to be incorporated.

# 腿肉机翻生词本 - 数据库操作模块
# 使用 SQLite 存储生词和遭遇历史



# %% Import

import sqlite3
import json
from datetime import date
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# %% Configuration
DB_PATH = Path(__file__).parent / "vocabulary.db"
BIRTH_DATE = date(2025, 10, 10)  # 程序生日
MAX_ENCOUNTERS = 128  # 每个词最多保留128次遭遇记录


def init_db():
    """初始化数据库，创建表结构"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 元数据表
    c.execute('''
              CREATE TABLE IF NOT EXISTS metadata
              (
                  key
                  TEXT
                  PRIMARY
                  KEY,
                  value
                  TEXT
              )
              ''')

    # 生词表
    c.execute('''
              CREATE TABLE IF NOT EXISTS vocabulary
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,
                  lang
                  TEXT
                  NOT
                  NULL,
                  word
                  TEXT
                  NOT
                  NULL,
                  word_lower
                  TEXT
                  NOT
                  NULL,
                  first_seen_day
                  INTEGER
                  NOT
                  NULL,
                  encounter_count
                  INTEGER
                  DEFAULT
                  1,
                  last_encounter_day
                  INTEGER
                  NOT
                  NULL,
                  stat_hp
                  INTEGER
                  DEFAULT
                  3,
                  stat_atk
                  REAL,
                  stat_def
                  REAL,
                  stat_res
                  REAL,
                  stat_spd
                  REAL,
                  breakthrough
                  INTEGER
                  DEFAULT
                  0,
                  created_at
                  TIMESTAMP
                  DEFAULT
                  CURRENT_TIMESTAMP,
                  UNIQUE
              (
                  lang,
                  word_lower
              )
                  )
              ''')

    # 遭遇历史表
    c.execute('''
              CREATE TABLE IF NOT EXISTS encounters
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,
                  vocab_id
                  INTEGER
                  NOT
                  NULL,
                  encounter_index
                  INTEGER
                  NOT
                  NULL,
                  day
                  INTEGER,
                  day_gap
                  INTEGER,
                  sentence_zh
                  TEXT,
                  sentence_en_google
                  TEXT,
                  sentence_en_deepl
                  TEXT,
                  sentence_target_google
                  TEXT,
                  sentence_target_deepl
                  TEXT,
                  source_id
                  TEXT,
                  source_title
                  TEXT,
                  source_detail
                  TEXT,
                  created_at
                  TIMESTAMP
                  DEFAULT
                  CURRENT_TIMESTAMP,
                  FOREIGN
                  KEY
              (
                  vocab_id
              ) REFERENCES vocabulary
              (
                  id
              ) ON DELETE CASCADE,
                  UNIQUE
              (
                  vocab_id,
                  encounter_index
              )
                  )
              ''')

    # 名人堂表
    c.execute('''
              CREATE TABLE IF NOT EXISTS hall_of_fame
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,
                  lang
                  TEXT
                  NOT
                  NULL,
                  word
                  TEXT
                  NOT
                  NULL,
                  word_lower
                  TEXT
                  NOT
                  NULL,
                  first_encounter_day
                  INTEGER,
                  first_encounter_data
                  TEXT,
                  last_encounter_day
                  INTEGER,
                  last_encounter_data
                  TEXT,
                  total_encounters
                  INTEGER,
                  breakthrough_count
                  INTEGER,
                  promoted_at
                  TIMESTAMP
                  DEFAULT
                  CURRENT_TIMESTAMP,
                  UNIQUE
              (
                  lang,
                  word_lower
              )
                  )
              ''')

    # 创建索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_vocab_lang ON vocabulary(lang)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vocab_word ON vocabulary(lang, word_lower)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vocab_hp ON vocabulary(stat_hp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_encounters_vocab ON encounters(vocab_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_hof_lang ON hall_of_fame(lang)')

    # 兼容旧数据库：添加新字段（如果不存在）
    try:
        c.execute("SELECT parent_id FROM vocabulary LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE vocabulary ADD COLUMN parent_id INTEGER DEFAULT NULL")
    try:
        c.execute("SELECT note FROM vocabulary LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE vocabulary ADD COLUMN note TEXT")
    try:
        c.execute("SELECT last_reviewed_at FROM vocabulary LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE vocabulary ADD COLUMN last_reviewed_at TIMESTAMP")

    # 初始化元数据
    c.execute('''
              INSERT
              OR IGNORE INTO metadata (key, value) 
        VALUES ('birth_date', ?), ('schema_version', '1.0')
              ''', (BIRTH_DATE.isoformat(),))

    try:
        c.execute("SELECT first_encounter_data FROM hall_of_fame LIMIT 1")
    except sqlite3.OperationalError:
        # 添加新字段
        c.execute("ALTER TABLE hall_of_fame ADD COLUMN first_encounter_data TEXT")
        c.execute("ALTER TABLE hall_of_fame ADD COLUMN last_encounter_data TEXT")

    conn.commit()
    conn.close()


def get_current_day() -> int:
    """获取当前天数（从生日算起）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    result = c.execute(
        "SELECT value FROM metadata WHERE key='birth_date'"
    ).fetchone()

    conn.close()

    if result:
        birth = date.fromisoformat(result[0])
        return (date.today() - birth).days
    return 0


def add_word(word: str, lang: str, sentence_zh: str, translations: dict, source_info: dict) -> Tuple[bool, str]:
    """
    添加生词或更新遭遇记录

    Args:
        word: 要添加的词（保留原样）
        lang: 语言代码（'es', 'fr', 'it'）
        sentence_zh: 中文原句
        translations: 翻译结果字典，格式：
            {
                'en': {'google': '...', 'deepl': '...'},
                'es': {'google': '...', 'deepl': '...'}
            }
        source_info: 出处信息字典，格式：
            {
                'work_id': '...',
                'title': '...',
                'series': [...],
                'relationships': [...]
            }

    Returns:
        (is_new, message): (是否是新词, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    current_day = get_current_day()
    word_lower = word.strip().lower()
    word = word.strip()  # 去掉首尾空格但保留大小写

    if not word:
        conn.close()
        return False, "词不能为空"

    # 检查是否已存在
    c.execute('''
              SELECT id, word, encounter_count, last_encounter_day
              FROM vocabulary
              WHERE lang = ?
                AND word_lower = ?
              ''', (lang, word_lower))

    result = c.fetchone()

    # 如果生词本没有，检查名人堂
    if result is None:
        c.execute('''
                  SELECT id, word
                  FROM hall_of_fame
                  WHERE lang = ?
                    AND word_lower = ?
                  ''', (lang, word_lower))

        hof_result = c.fetchone()
        if hof_result:
            conn.close()
            return False, f"⚠️ 词条 '{hof_result[1]}' 已在总选名人堂，无需重复添加"

    # 准备翻译文本
    en_google = translations.get('en', {}).get('google', '')
    en_deepl = translations.get('en', {}).get('deepl', '')
    target_google = translations.get(lang, {}).get('google', '')
    target_deepl = translations.get(lang, {}).get('deepl', '')

    # 准备出处详情（JSON格式）
    source_detail = json.dumps({
        'series': source_info.get('series', []),
        'relationships': source_info.get('relationships', []),
        'published': source_info.get('published'),
        'updated': source_info.get('updated')
    }, ensure_ascii=False)

    if result is None:
        # 首次添加
        c.execute('''
                  INSERT INTO vocabulary
                  (lang, word, word_lower, first_seen_day, encounter_count, last_encounter_day, stat_hp)
                  VALUES (?, ?, ?, ?, 1, ?, 3)
                  ''', (lang, word, word_lower, current_day, current_day))

        vocab_id = c.lastrowid

        # 添加初次遭遇（index=0，永久保留）
        c.execute('''
                  INSERT INTO encounters
                  (vocab_id, encounter_index, day,
                   sentence_zh, sentence_en_google, sentence_en_deepl,
                   sentence_target_google, sentence_target_deepl,
                   source_id, source_title, source_detail)
                  VALUES (?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  ''', (vocab_id, current_day,
                        sentence_zh, en_google, en_deepl, target_google, target_deepl,
                        source_info.get('work_id'), source_info.get('title'), source_detail))

        conn.commit()
        conn.close()
        return True, f"✓ 新词 '{word}' 已加入生词本！"

    else:
        # 已存在，更新
        vocab_id, existing_word, count, last_day = result
        day_gap = current_day - last_day

        # 更新生词表
        c.execute('''
                  UPDATE vocabulary
                  SET encounter_count    = encounter_count + 1,
                      last_encounter_day = ?,
                      stat_hp            = stat_hp + 2
                  WHERE id = ?
                  ''', (current_day, vocab_id))

        # 计算下一个 index（1-127循环，index=0永久保留初次遭遇）
        next_index = ((count - 1) % (MAX_ENCOUNTERS - 1)) + 1

        # 插入或替换遭遇记录
        c.execute('''
            INSERT OR REPLACE INTO encounters
            (vocab_id, encounter_index, day_gap,
             sentence_zh, sentence_en_google, sentence_en_deepl,
             sentence_target_google, sentence_target_deepl,
             source_id, source_title, source_detail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vocab_id, next_index, day_gap,
              sentence_zh, en_google, en_deepl, target_google, target_deepl,
              source_info.get('work_id'), source_info.get('title'), source_detail))

        conn.commit()
        conn.close()
        return False, f"✓ 已更新！这是第 {count + 1} 次遇到 '{existing_word}'"


def get_vocabulary_list(lang: Optional[str] = None, limit: int = 100,
                        sort_by: str = 'last_encounter') -> List[Dict]:
    """
    获取生词列表

    Args:
        lang: 语言代码，None表示所有语言
        limit: 返回数量限制
        sort_by: 排序方式
            - 'last_encounter': 最近遭遇（倒序）
            - 'first_encounter': 最初遭遇（正序）
            - 'encounter_count': 遇到次数（倒序）
            - 'last_reviewed': 最近温习（倒序）
            - 'alphabetical': 字母表顺序

    Returns:
        生词列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 根据排序方式选择 ORDER BY 子句
    if sort_by == 'alphabetical':
        order_clause = 'ORDER BY word_lower ASC'
    elif sort_by == 'first_encounter':
        order_clause = 'ORDER BY first_seen_day ASC, created_at ASC'
    elif sort_by == 'encounter_count':
        order_clause = 'ORDER BY encounter_count DESC, last_encounter_day DESC, created_at DESC'
    elif sort_by == 'last_reviewed':  # ← 新增
        order_clause = 'ORDER BY last_reviewed_at DESC NULLS LAST, last_encounter_day DESC'
    else:  # 默认：last_encounter
        order_clause = 'ORDER BY last_encounter_day DESC, created_at DESC'

    if lang:
        query = f'''
            SELECT * FROM vocabulary 
            WHERE lang = ?
            {order_clause}
            LIMIT ?
        '''
        c.execute(query, (lang, limit))
    else:
        query = f'''
            SELECT * FROM vocabulary 
            {order_clause}
            LIMIT ?
        '''
        c.execute(query, (limit,))

    results = [dict(row) for row in c.fetchall()]
    conn.close()

    return results


def get_word_encounters(vocab_id: int) -> List[Dict]:
    """获取某个词的所有遭遇记录"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
              SELECT *
              FROM encounters
              WHERE vocab_id = ?
              ORDER BY encounter_index
              ''', (vocab_id,))

    results = [dict(row) for row in c.fetchall()]
    conn.close()

    return results


def get_stats() -> Dict:
    """获取统计信息"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    stats = {}

    # 当前天数
    stats['current_day'] = get_current_day()

    # 各语言词数
    c.execute('SELECT lang, COUNT(*) as count FROM vocabulary GROUP BY lang')
    stats['by_lang'] = {row[0]: row[1] for row in c.fetchall()}

    # 总词数
    c.execute('SELECT COUNT(*) FROM vocabulary')
    stats['total_words'] = c.fetchone()[0]

    # 总遭遇次数
    c.execute('SELECT SUM(encounter_count) FROM vocabulary')
    stats['total_encounters'] = c.fetchone()[0] or 0

    # 名人堂词数
    c.execute('SELECT COUNT(*) FROM hall_of_fame')
    stats['hall_of_fame_count'] = c.fetchone()[0]

    conn.close()

    return stats


def delete_word(vocab_id: int) -> Tuple[bool, str]:
    """
    删除生词本词条（管理员通道）

    Args:
        vocab_id: 词条ID

    Returns:
        (success, message): (是否成功, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # 先获取词条信息用于提示
        c.execute('SELECT word, lang FROM vocabulary WHERE id = ?', (vocab_id,))
        result = c.fetchone()

        if not result:
            conn.close()
            return False, "❌ 词条不存在"

        word, lang = result

        # 删除词条（encounters 会因为 ON DELETE CASCADE 自动删除）
        c.execute('DELETE FROM vocabulary WHERE id = ?', (vocab_id,))
        conn.commit()
        conn.close()

        return True, f"✓ 已删除 '{word}' ({lang})"

    except Exception as e:
        conn.close()
        return False, f"❌ 删除失败：{str(e)}"


def rename_word(vocab_id: int, new_word: str) -> Tuple[bool, str]:
    """
    重命名词条（保留所有历史数据）

    Args:
        vocab_id: 词条ID
        new_word: 新的词（保留大小写）

    Returns:
        (success, message): (是否成功, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        new_word = new_word.strip()
        new_word_lower = new_word.lower()

        if not new_word:
            conn.close()
            return False, "❌ 新词不能为空"

        # 获取原词信息
        c.execute('SELECT word, lang, word_lower FROM vocabulary WHERE id = ?', (vocab_id,))
        result = c.fetchone()

        if not result:
            conn.close()
            return False, "❌ 词条不存在"

        old_word, lang, old_word_lower = result

        # 检查新词是否与其他词条冲突（同语言下）
        c.execute('''
                  SELECT id, word
                  FROM vocabulary
                  WHERE lang = ?
                    AND word_lower = ?
                    AND id != ?
                  ''', (lang, new_word_lower, vocab_id))

        conflict = c.fetchone()
        if conflict:
            conn.close()
            return False, f"❌ 该语言下已存在词条 '{conflict[1]}'"

        # 更新词条
        c.execute('''
                  UPDATE vocabulary
                  SET word       = ?,
                      word_lower = ?
                  WHERE id = ?
                  ''', (new_word, new_word_lower, vocab_id))

        conn.commit()
        conn.close()

        return True, f"✓ 已将 '{old_word}' 重命名为 '{new_word}'"

    except Exception as e:
        conn.close()
        return False, f"❌ 重命名失败：{str(e)}"


def search_word(word: str, lang: Optional[str] = None) -> List[Dict]:
    """
    搜索词条（用于管理工具）

    Args:
        word: 要搜索的词
        lang: 语言代码（可选）

    Returns:
        匹配的词条列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    word_lower = word.strip().lower()

    if lang:
        c.execute('''
                  SELECT *
                  FROM vocabulary
                  WHERE lang = ?
                    AND word_lower = ?
                  ''', (lang, word_lower))
    else:
        c.execute('''
                  SELECT *
                  FROM vocabulary
                  WHERE word_lower = ?
                  ''', (word_lower,))

    results = [dict(row) for row in c.fetchall()]
    conn.close()

    return results


def update_note(vocab_id: int, note: str) -> Tuple[bool, str]:
    """
    更新词条注释

    Args:
        vocab_id: 词条ID
        note: 注释内容

    Returns:
        (success, message): (是否成功, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute('SELECT word FROM vocabulary WHERE id = ?', (vocab_id,))
        result = c.fetchone()

        if not result:
            conn.close()
            return False, "❌ 词条不存在"

        word = result[0]

        c.execute('''
                  UPDATE vocabulary
                  SET note = ?
                  WHERE id = ?
                  ''', (note.strip(), vocab_id))

        conn.commit()
        conn.close()

        if note.strip():
            return True, f"✓ 已更新 '{word}' 的注释"
        else:
            return True, f"✓ 已清空 '{word}' 的注释"

    except Exception as e:
        conn.close()
        return False, f"❌ 更新失败：{str(e)}"


def set_parent(child_id: int, parent_id: Optional[int]) -> Tuple[bool, str]:
    """
    设置词条的母词条

    Args:
        child_id: 子词条ID
        parent_id: 母词条ID（None 表示取消关联）

    Returns:
        (success, message): (是否成功, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # 获取子词信息
        c.execute('SELECT word, lang FROM vocabulary WHERE id = ?', (child_id,))
        child_result = c.fetchone()

        if not child_result:
            conn.close()
            return False, "❌ 子词条不存在"

        child_word, child_lang = child_result

        if parent_id is None:
            # 取消关联
            c.execute('UPDATE vocabulary SET parent_id = NULL WHERE id = ?', (child_id,))
            conn.commit()
            conn.close()
            return True, f"✓ 已取消 '{child_word}' 的母词条关联"

        # 获取母词信息（需要同时检查生词本和名人堂）
        c.execute('SELECT word, lang FROM vocabulary WHERE id = ?', (parent_id,))
        parent_result = c.fetchone()

        if not parent_result:
            # 🔧 修复：检查名人堂
            c.execute('''
                      SELECT word, lang
                      FROM hall_of_fame
                      WHERE id = ?
                      ''', (parent_id,))
            hof_result = c.fetchone()

            if not hof_result:
                conn.close()
                return False, "❌ 母词条不存在（在生词本或名人堂中都找不到）"

            # 如果母词在名人堂，不允许设置关系
            conn.close()
            return False, f"❌ 母词条 '{hof_result[0]}' 在名人堂中，暂不支持此场景"

        parent_word, parent_lang = parent_result

        # 检查语言是否相同
        if child_lang != parent_lang:
            conn.close()
            return False, f"❌ 语言不匹配（子词: {child_lang}, 母词: {parent_lang}）"

        # 防止自己指向自己
        if child_id == parent_id:
            conn.close()
            return False, "❌ 不能将词条设置为自己的母词条"

        # 防止循环引用（如果母词条本身是某个词的子词条）
        c.execute('SELECT parent_id FROM vocabulary WHERE id = ?', (parent_id,))
        parent_parent = c.fetchone()[0]
        if parent_parent is not None:
            conn.close()
            return False, f"❌ 母词条 '{parent_word}' 本身是其他词的子词条，不支持多级关系"

        # 设置母词条
        c.execute('UPDATE vocabulary SET parent_id = ? WHERE id = ?', (parent_id, child_id))
        conn.commit()
        conn.close()

        return True, f"✓ 已将 '{child_word}' 设置为 '{parent_word}' 的子词条"

    except Exception as e:
        conn.close()
        return False, f"❌ 设置失败：{str(e)}"


def get_word_by_id(vocab_id: int) -> Optional[Dict]:
    """
    通过 ID 获取词条

    Args:
        vocab_id: 词条ID

    Returns:
        词条数据字典，不存在则返回 None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM vocabulary WHERE id = ?', (vocab_id,))
    result = c.fetchone()

    conn.close()

    return dict(result) if result else None


def get_children(parent_id: int) -> List[Dict]:
    """
    获取某词条的所有子词条

    Args:
        parent_id: 母词条ID

    Returns:
        子词条列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
              SELECT *
              FROM vocabulary
              WHERE parent_id = ?
              ORDER BY word_lower
              ''', (parent_id,))

    results = [dict(row) for row in c.fetchall()]
    conn.close()

    return results


def add_word_manual(word: str, lang: str, note: str = "") -> Tuple[bool, str]:
    """
    手动添加词条（无例句）

    Args:
        word: 词
        lang: 语言代码
        note: 可选注释

    Returns:
        (is_new, message): (是否是新词, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    current_day = get_current_day()
    word_lower = word.strip().lower()
    word = word.strip()

    if not word:
        conn.close()
        return False, "❌ 词不能为空"

    # 检查是否已存在
    c.execute('''
              SELECT id, word
              FROM vocabulary
              WHERE lang = ?
                AND word_lower = ?
              ''', (lang, word_lower))

    result = c.fetchone()

    if result:
        conn.close()
        return False, f"⚠️ 词条 '{result[1]}' 已存在"

    # 检查名人堂
    c.execute('''
              SELECT id, word
              FROM hall_of_fame
              WHERE lang = ?
                AND word_lower = ?
              ''', (lang, word_lower))

    hof_result = c.fetchone()
    if hof_result:
        conn.close()
        return False, f"⚠️ 词条 '{hof_result[1]}' 已在总选名人堂，无需重复添加"

    # 添加新词条
    c.execute('''
              INSERT INTO vocabulary
              (lang, word, word_lower, first_seen_day, encounter_count, last_encounter_day, stat_hp, note)
              VALUES (?, ?, ?, ?, 1, ?, 3, ?)
              ''', (lang, word, word_lower, current_day, current_day, note))

    conn.commit()
    conn.close()

    return True, f"✓ 已添加词条 '{word}'"

# %% 配置-白值&总选名人堂相关…（先这么叫了*2

def decrease_hp(vocab_id: int) -> Tuple[bool, str, bool]:
    """
    好像认识：HP -1INSERT INTO vocabulary

    Args:
        vocab_id: 词条ID

    Returns:
        (success, message, promoted):
        - success: 是否成功
        - message: 提示信息
        - promoted: 是否出道（HP降到0）
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # 获取词条信息
        c.execute('''
                  SELECT word, lang, stat_hp
                  FROM vocabulary
                  WHERE id = ?
                  ''', (vocab_id,))

        result = c.fetchone()
        if not result:
            conn.close()
            return False, "❌ 词条不存在", False

        word, lang, current_hp = result
        new_hp = current_hp - 1

        # HP 降到 0 或以下，移入总选
        if new_hp <= 0:
            success = promote_to_hall_of_fame(vocab_id)
            if success:
                return True, f"🎉 '{word}' 总选出道！", True
            else:
                return False, "❌ 移入总选失败", False

        # 更新 HP
        c.execute('''
                  UPDATE vocabulary
                  SET stat_hp          = ?,
                      last_reviewed_at = CURRENT_TIMESTAMP
                  WHERE id = ?
                  ''', (new_hp, vocab_id))

        conn.commit()
        conn.close()

        return True, f"✓ '{word}' HP -1（当前 HP: {new_hp}）", False

    except Exception as e:
        conn.close()
        return False, f"❌ 操作失败：{str(e)}", False


def increase_hp(vocab_id: int) -> Tuple[bool, str]:
    """
    不太认识：HP +2

    Args:
        vocab_id: 词条ID

    Returns:
        (success, message): (是否成功, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # 获取词条信息
        c.execute('''
                  SELECT word, stat_hp
                  FROM vocabulary
                  WHERE id = ?
                  ''', (vocab_id,))

        result = c.fetchone()
        if not result:
            conn.close()
            return False, "❌ 词条不存在"

        word, current_hp = result
        new_hp = current_hp + 2

        # 更新 HP
        c.execute('''
                  UPDATE vocabulary
                  SET stat_hp          = ?,
                      last_reviewed_at = CURRENT_TIMESTAMP
                  WHERE id = ?
                  ''', (new_hp, vocab_id))

        conn.commit()
        conn.close()

        return True, f"✓ '{word}' HP +2（当前 HP: {new_hp}）"

    except Exception as e:
        conn.close()
        return False, f"❌ 操作失败：{str(e)}"


def promote_to_hall_of_fame(vocab_id: int) -> bool:
    """
    将词条移入总选（HP = 0 时调用）

    Args:
        vocab_id: 词条ID

    Returns:
        是否成功
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # 获取词条完整信息
        c.execute('SELECT * FROM vocabulary WHERE id = ?', (vocab_id,))
        vocab = dict(zip([d[0] for d in c.description], c.fetchone()))

        if not vocab:
            conn.close()
            return False

        # 获取初次遭遇（index = 0）完整数据
        c.execute('''
                  SELECT *
                  FROM encounters
                  WHERE vocab_id = ?
                    AND encounter_index = 0
                  ''', (vocab_id,))
        first_enc_row = c.fetchone()
        first_encounter_data = ""
        first_encounter_day = vocab['first_seen_day']

        if first_enc_row:
            first_enc = dict(zip([d[0] for d in c.description], first_enc_row))
            first_encounter_data = json.dumps({
                'day': first_enc.get('day'),
                'sentence_zh': first_enc.get('sentence_zh'),
                'sentence_en_google': first_enc.get('sentence_en_google'),
                'sentence_en_deepl': first_enc.get('sentence_en_deepl'),
                'sentence_target_google': first_enc.get('sentence_target_google'),
                'sentence_target_deepl': first_enc.get('sentence_target_deepl'),
                'source_id': first_enc.get('source_id'),
                'source_title': first_enc.get('source_title'),
                'source_detail': first_enc.get('source_detail')
            }, ensure_ascii=False)
            first_encounter_day = first_enc.get('day', first_encounter_day)

        # 获取最近遭遇完整数据
        c.execute('''
                  SELECT *
                  FROM encounters
                  WHERE vocab_id = ?
                  ORDER BY encounter_index DESC LIMIT 1
                  ''', (vocab_id,))
        last_enc_row = c.fetchone()
        last_encounter_data = ""
        last_encounter_day = vocab['last_encounter_day']

        if last_enc_row:
            last_enc = dict(zip([d[0] for d in c.description], last_enc_row))
            last_encounter_data = json.dumps({
                'day': last_enc.get('day'),
                'sentence_zh': last_enc.get('sentence_zh'),
                'sentence_en_google': last_enc.get('sentence_en_google'),
                'sentence_en_deepl': last_enc.get('sentence_en_deepl'),
                'sentence_target_google': last_enc.get('sentence_target_google'),
                'sentence_target_deepl': last_enc.get('sentence_target_deepl'),
                'source_id': last_enc.get('source_id'),
                'source_title': last_enc.get('source_title'),
                'source_detail': last_enc.get('source_detail')
            }, ensure_ascii=False)
            last_encounter_day = last_enc.get('day', last_encounter_day)

        # 插入总选表（保留生词本中的突破数）
        # 🔧 修复：从生词本读取 breakthrough，而不是从名人堂查询
        current_breakthrough = vocab.get('breakthrough', 0)

        c.execute('''
                INSERT OR REPLACE INTO hall_of_fame 
                (lang, word, word_lower, 
                 first_encounter_day, first_encounter_data,
                 last_encounter_day, last_encounter_data,
                 total_encounters, breakthrough_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (vocab['lang'], vocab['word'], vocab['word_lower'],
                  first_encounter_day, first_encounter_data,
                  last_encounter_day, last_encounter_data,
                  vocab['encounter_count'],
                  current_breakthrough))

        # 删除生词本中的记录
        c.execute('DELETE FROM vocabulary WHERE id = ?', (vocab_id,))

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"移入总选失败：{e}")
        conn.close()
        return False


def demote_from_hall_of_fame(hof_id: int) -> Tuple[bool, str]:
    """
    从总选移回生词本（突破数 +1）

    Args:
        hof_id: 总选词条ID

    Returns:
        (success, message): (是否成功, 提示信息)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        current_day = get_current_day()

        # 获取总选词条信息
        c.execute('SELECT * FROM hall_of_fame WHERE id = ?', (hof_id,))
        hof = dict(zip([d[0] for d in c.description], c.fetchone()))

        if not hof:
            conn.close()
            return False, "❌ 词条不存在"

        word = hof['word']
        new_breakthrough = hof['breakthrough_count'] + 1

        # 重新加入生词本（保留首次遭遇日期）
        c.execute('''
                  INSERT INTO vocabulary
                  (lang, word, word_lower, first_seen_day, encounter_count,
                   last_encounter_day, stat_hp, breakthrough)
                  VALUES (?, ?, ?, ?, ?, ?, 3, ?)
                  ''', (hof['lang'], hof['word'], hof['word_lower'],
                        hof['first_encounter_day'],
                        hof['total_encounters'],
                        current_day,
                        new_breakthrough))

        vocab_id = c.lastrowid

        # 恢复初次遭遇记录（完整数据）
        if hof.get('first_encounter_data'):
            first_data = json.loads(hof['first_encounter_data'])
            c.execute('''
                      INSERT INTO encounters
                      (vocab_id, encounter_index, day,
                       sentence_zh, sentence_en_google, sentence_en_deepl,
                       sentence_target_google, sentence_target_deepl,
                       source_id, source_title, source_detail)
                      VALUES (?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                      ''', (vocab_id, first_data.get('day'),
                            first_data.get('sentence_zh'),
                            first_data.get('sentence_en_google'),
                            first_data.get('sentence_en_deepl'),
                            first_data.get('sentence_target_google'),
                            first_data.get('sentence_target_deepl'),
                            first_data.get('source_id'),
                            first_data.get('source_title'),
                            first_data.get('source_detail')))

        # 🔧 修复：更新突破数但不删除名人堂记录
        c.execute('''
                  UPDATE hall_of_fame
                  SET breakthrough_count = ?
                  WHERE id = ?
                  ''', (new_breakthrough, hof_id))

        conn.commit()
        conn.close()

        return True, f"✓ '{word}' 回归生词本（突破 {new_breakthrough} 次）"

    except Exception as e:
        conn.close()
        return False, f"❌ 操作失败：{str(e)}"


def get_hall_of_fame_list(lang: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    获取总选列表

    Args:
        lang: 语言代码，None表示所有语言
        limit: 返回数量限制

    Returns:
        总选列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 🔧 修复：只显示当前在名人堂的词（已回到生词本的不显示）
    if lang:
        c.execute('''
                  SELECT h.*
                  FROM hall_of_fame h
                  WHERE h.lang = ?
                    AND NOT EXISTS (SELECT 1
                                    FROM vocabulary v
                                    WHERE v.lang = h.lang
                                      AND v.word_lower = h.word_lower)
                  ORDER BY h.promoted_at DESC LIMIT ?
                  ''', (lang, limit))
    else:
        c.execute('''
                  SELECT h.*
                  FROM hall_of_fame h
                  WHERE NOT EXISTS (SELECT 1
                                    FROM vocabulary v
                                    WHERE v.lang = h.lang
                                      AND v.word_lower = h.word_lower)
                  ORDER BY h.promoted_at DESC LIMIT ?
                  ''', (limit,))

    results = [dict(row) for row in c.fetchall()]
    conn.close()

    return results


# 初始化数据库（导入时自动执行）
try:
    init_db()
except Exception as e:
    print(f"数据库初始化失败：{e}")

