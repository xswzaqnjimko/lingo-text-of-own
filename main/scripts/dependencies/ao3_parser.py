# ao3_parser.py - AO3 HTML 解析模块
# v1.1: 从 整点腿肉机翻.py 中提取出来的 AO3 HTML 解析相关函数
# 包括：FFF HTML 解析、中文分句、CP匹配等

import re
import unicodedata
from pathlib import Path
from html import unescape

from bs4 import BeautifulSoup

from dependencies.config import TARGET_RELAS


# %% 设置-抽句子基本 ============

# 简单中文分句（处理句末标点与右引号/括号）
SENT_RE = re.compile(r'.+?(?:[。！？]|……)(?:[」』"〉》）\)\]]+)?')


# %% 设置-AO3作品Meta ============

# 从 FFF 生成的文件名里抓 ao3 id：Something-ao3_123456.html
ID_IN_FILENAME_RE = re.compile(r'ao3_(\d+)\.html$', re.I)


# —— 基于两列表格的解析助手 ——

def _get_value_cell_by_label(soup: BeautifulSoup, label: str):
    """
    在两列表格中，找到左侧<b>Label:</b>的行，返回右侧<td>节点（或None）。
    label 匹配不区分大小写，仅比较前缀（去掉冒号）。
    """
    label = label.strip().lower().rstrip(':')
    for tr in soup.select('table tr'):
        tds = tr.find_all('td')
        if len(tds) >= 2:
            left = tds[0].get_text(" ", strip=True).lower().rstrip(':')
            if left.startswith(label):
                return tds[1]
    return None

def parse_fff_html(path: Path):
    """
    从 FFF 导出的 AO3 HTML 中提取：
      - work_id, title
      - relationships (list[str])
      - published (str), updated (str)
      - series (list[dict]: [{'title':..., 'href':...}])
      - doc_text_lc / fname_lc（用于兜底匹配或调试）
    """
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # 标题 & work_id（优先从 h1 > a）
    title = None
    work_id = None
    h1 = soup.find('h1')
    if h1:
        a = h1.find('a', href=re.compile(r'/works/\d+'))
        if a:
            title = a.get_text(strip=True)
            m = re.search(r'/works/(\d+)', a.get('href',''))
            if m:
                work_id = m.group(1)
    if not title and soup.title:
        title = soup.title.get_text(strip=True)
    if not title:
        title = path.stem
    if not work_id:
        m = ID_IN_FILENAME_RE.search(path.name)
        if m:
            work_id = m.group(1)

    # Relationships
    rel_td = _get_value_cell_by_label(soup, "Relationships")
    relationships = []
    if rel_td:
        relationships = [a.get_text(" ", strip=True) for a in rel_td.find_all('a')]
        if not relationships:
            raw = rel_td.get_text(" ", strip=True)
            relationships = [s.strip() for s in raw.split(",") if s.strip()]

    # Published / Updated
    published = None
    updated = None
    pub_td = _get_value_cell_by_label(soup, "Published")
    upd_td = _get_value_cell_by_label(soup, "Updated")
    if pub_td: published = pub_td.get_text(" ", strip=True)
    if upd_td: updated  = upd_td.get_text(" ", strip=True)

    # Series（可能有多个 a）
    series = []
    ser_td = _get_value_cell_by_label(soup, "Series")
    if ser_td:
        for a in ser_td.find_all('a', href=True):
            series.append({
                "title": a.get_text(" ", strip=True),
                "href": a['href']
            })

    # 额外：全文/文件名（小写），便于兜底匹配或调试
    doc_text_lc = (soup.get_text(" ", strip=True) or "").lower()
    fname_lc = path.name.lower()

    return {
        "work_id": work_id,
        "title": title,
        "relationships": relationships,
        "published": published,
        "updated": updated,
        "series": series,
        "doc_text_lc": doc_text_lc,
        "fname_lc": fname_lc,
    }

def clean_text(t: str) -> str:
    t = unescape(t)
    # 统一空白
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\u3000', ' ', t)  # 全角空格
    t = re.sub(r'\s*\n\s*', '\n', t)
    return t.strip()


def extract_meta_and_text_from_html(path: Path):
    """
    使用 parse_fff_html 精确抽取 meta，再抽正文中文句子。
    """
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # 先拿 meta
    info = parse_fff_html(path)

    # 正文（优先 userstuff / chapters 容器）
    text_blocks = []
    chapters = soup.find('div', id='chapters')
    if chapters:
        text_blocks.append(chapters.get_text("\n", strip=True))
    else:
        for block in soup.find_all('div', class_=re.compile(r'userstuff')):
            text_blocks.append(block.get_text("\n", strip=True))
        if not text_blocks:
            text_blocks.append(soup.get_text("\n", strip=True))

    full_text = clean_text("\n".join(text_blocks))
    sentences = [s.strip() for s in SENT_RE.findall(full_text) if s.strip()]

    # 合并返回
    return {
        "path": str(path),
        "work_id": info["work_id"],
        "title": info["title"],
        "relationships": info["relationships"],
        "published": info["published"],
        "updated": info["updated"],
        "series": info["series"],
        "doc_text_lc": soup.get_text(" ", strip=True).lower(),
        "fname_lc": Path(path).name.lower(),         # 兜底匹配要用
        "sentences": sentences,
    }


# %% 设置-只选特定CP ============

# 洗格式（比如用来确保搜得到CP…）
def norm_for_match(s: str) -> str:
    """NFKC + 去零宽/BOM/NBSP + casefold + 收敛空白"""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")  # ZWSP/ZWNJ/ZWJ
    s = s.replace("\ufeff", "")                                              # BOM
    s = s.replace("\u00a0", " ").replace("\u202f", " ")                      # NBSP/NARROW NBSP
    s = s.casefold()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def strip_implied_variants(rel_norm: str) -> str:
    """
    把关系标签里的 'implied' 修饰去掉（前缀/后缀两种常见写法）后返回。
    例：'implied yuris leclerc/claude von riegan' -> 'yuris leclerc/claude von riegan'
        'yuris leclerc/claude von riegan (implied)' -> 'yuris leclerc/claude von riegan'
    """
    if not rel_norm:
        return ""
    # 前缀：implied / implied: / implied- / implied—
    rel_norm = re.sub(r'^(implied|suggested)\s*[:\-–—]?\s*', '', rel_norm)
    # 后缀：(implied) / (suggested)
    rel_norm = re.sub(r'\s*\((implied|suggested)\)\s*$', '', rel_norm)
    return rel_norm.strip()

TARGET_NORM = [norm_for_match(x) for x in TARGET_RELAS]
TARGET_PATTERNS = [s.lower() for s in TARGET_RELAS]  # 兜底：全文本子串匹配

def filter_by_relationship(records, targets_exact: list[str], targets_patterns: list[str]):
    """
    规范化后匹配：
      1) relationships 列表：先 norm，再 strip implied，再与目标 norm 等价匹配；
      2) 兜底：全文/文件名 norm 后，允许出现 'implied ' + 目标 或 目标本身的子串。
    """
    # 目标集（规范化）
    exact_norm_set = set(norm_for_match(x) for x in targets_exact)
    pat_norm_list  = [norm_for_match(x) for x in targets_patterns]
    pat_norm_list_implied = [f"implied {p}" for p in pat_norm_list]  # 兜底时同时认可「implied 目标」

    result = []
    for r in records:
        # 1) 先看 relationships 列表（最可靠）
        rels = [x for x in (r.get("relationships") or []) if x]
        rels_norm_clean = [strip_implied_variants(norm_for_match(x)) for x in rels]
        if exact_norm_set and any(x in exact_norm_set for x in rels_norm_clean):
            result.append(r)
            continue

        # 2) 兜底：全文/文件名子串（同时认可 implied 前缀）
        if pat_norm_list:
            blob = " ".join([r.get("doc_text_lc",""), r.get("fname_lc","")])
            blob_norm = norm_for_match(blob)
            if any(p in blob_norm for p in pat_norm_list) or any(p in blob_norm for p in pat_norm_list_implied):
                result.append(r)
                continue
    return result

# 统计诊断信息/匹配到的作品
def _diag_breakdown(records, targets_exact, targets_patterns):
    exact_norm_set = set(norm_for_match(x) for x in targets_exact)
    pat_norm_list  = [norm_for_match(x) for x in targets_patterns]
    by_exact, by_fallback = [], []
    for r in records:
        rels_norm = [norm_for_match(x) for x in (r.get("relationships") or [])]
        blob_norm = norm_for_match(" ".join([r.get("doc_text_lc",""), r.get("fname_lc","")]))
        if exact_norm_set and any(x in exact_norm_set for x in rels_norm):
            by_exact.append(r)
        elif pat_norm_list and any(p in blob_norm for p in pat_norm_list):
            by_fallback.append(r)
    return by_exact, by_fallback


def index_local_corpus_core(root_dirs, recursive=True, limit_files=0, only_fff=True):
    """扫描给定目录里的 .html，返回记录列表。索引时可选"只认 FFF 文件名模式"（默认开启）
    注意：Streamlit 的 @st.cache_data 装饰器在 main.py 里加，这里是纯逻辑。
    """
    records = []
    total = 0
    for d in root_dirs:
        base = Path(d).expanduser()
        if not base.exists():
            continue
        pattern = "**/*.html" if recursive else "*.html"
        for p in base.glob(pattern):
            if only_fff and not ID_IN_FILENAME_RE.search(p.name):
                continue  # 只要 FFF 保存出来的 -ao3_ID.html
            total += 1
            try:
                rec = extract_meta_and_text_from_html(p)
                records.append(rec)
            except Exception:
                # 忽略无法解析的文件
                continue
            if limit_files and len(records) >= limit_files:
                break
    return records, total
