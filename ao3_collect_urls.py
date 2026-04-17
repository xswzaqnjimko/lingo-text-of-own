#!/usr/bin/env python3
"""
AO3 作品链接收集脚本（增强版）
支持断点续传、自动重试、进度保存
方便起见，使用时可临时设置所有作品游客可见

"""

import argparse
import time
from datetime import datetime
import sys
import re
import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from dependencies.config import DEFAULT_AO3_USER_URL, URLS_ALL_FILE, COLLECT_MAX_AUTO_RETRIES, COLLECT_RETRY_WAIT_SECONDS

from collections import OrderedDict

class TimingLogger:
    def __init__(self):
        self.timings = OrderedDict()
        self._starts = {}
        self._total = None
    def start_total(self):
        self._total = time.time()
    def start(self, name):
        self._starts[name] = time.time()
    def stop(self, name):
        if name in self._starts:
            self.timings[name] = time.time() - self._starts[name]
    def get_total(self):
        return time.time() - self._total if self._total else 0
    def fmt(self, d):
        return f"{int(d//60)}m {d%60:.1f}s" if d >= 60 else f"{d:.1f}s"
    def print_summary(self):
        print("\n" + "=" * 50, file=sys.stderr)
        print("⏱️  TIMING SUMMARY", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        for step, dur in self.timings.items():
            print(f"  {step:<35} {self.fmt(dur):>12}", file=sys.stderr)
        print("-" * 50, file=sys.stderr)
        print(f"  {'TOTAL':<35} {self.fmt(self.get_total()):>12}", file=sys.stderr)



HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.8,zh;q=0.6",
}

BASE = "https://archiveofourown.org"


def get(url, timeout, max_retries=3):
    """
    获取 URL，带重试机制
    """
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # 第1次等5秒，第2次等10秒，第3次等15秒
                print(f"⚠️  请求超时/连接错误，{wait_time}秒后重试 (尝试 {attempt + 2}/{max_retries})...", file=sys.stderr)
                time.sleep(wait_time)
            else:
                print(f"❌ 多次重试失败: {url}", file=sys.stderr)
                raise
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求错误: {url} - {e}", file=sys.stderr)
            raise


def find_last_page(soup):
    """
    从分页导航中找到最后一页的页码
    """
    nav = soup.select_one("ol.pagination")
    if not nav:
        return 1
    nums = []
    for a in nav.select("a"):
        if a.text.strip().isdigit():
            nums.append(int(a.text.strip()))
    return max(nums) if nums else 1


def extract_work_urls(soup):
    """
    从页面中提取所有作品 URL
    """
    urls = []
    for a in soup.select('li.work.blurb h4.heading a[href^="/works/"]'):
        href = a.get("href", "")
        # 排除 /series/… 等非作品链接
        if re.match(r"^/works/\d+($|[/?#])", href):
            urls.append(urljoin(BASE, href.split("?")[0]))
    return urls


def load_progress(progress_file):
    """
    加载进度文件
    返回：{
        'completed_pages': [1, 2, 3, ...],
        'collected_urls': set([url1, url2, ...])
    }
    """
    if not progress_file.exists():
        return {'completed_pages': [], 'collected_urls': set()}
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                'completed_pages': data.get('completed_pages', []),
                'collected_urls': set(data.get('collected_urls', []))
            }
    except Exception as e:
        print(f"⚠️  无法读取进度文件，将从头开始: {e}", file=sys.stderr)
        return {'completed_pages': [], 'collected_urls': set()}


def save_progress(progress_file, completed_pages, collected_urls):
    """
    保存进度文件
    """
    try:
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                'completed_pages': sorted(completed_pages),
                'collected_urls': sorted(list(collected_urls))
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  保存进度文件失败: {e}", file=sys.stderr)


def save_final_urls(outfile, urls):
    """
    保存最终的 URL 列表
    """
    sorted_urls = sorted(urls, key=lambda x: int(re.search(r"/works/(\d+)", x).group(1)))
    with open(outfile, "w", encoding="utf-8") as f:
        for u in sorted_urls:
            f.write(u + "\n")
    print(f"✅ 保存 {len(sorted_urls)} 个 URL 到 {outfile}")


def scrape_once(args, outfile, progress_file):
    """
    一轮抓取逻辑。成功返回 True，失败返回 False（进度已保存，可 resume）。
    """
    # 加载进度（默认 resume）
    if not args.fresh:
        progress = load_progress(progress_file)
        completed_pages = set(progress['completed_pages'])
        all_urls = progress['collected_urls']
        if completed_pages:
            print(f"📂 从进度文件恢复：已完成 {len(completed_pages)} 页，已收集 {len(all_urls)} 个 URL", file=sys.stderr)
    else:
        completed_pages = set()
        all_urls = set()
        # 如果是全新模式，删除旧的进度文件
        if progress_file.exists():
            progress_file.unlink()
            print(f"🗑️  删除旧进度文件", file=sys.stderr)

    # 获取第一页（或跳过如果已完成）
    if 1 not in completed_pages:
        print(f"📖 获取第 1 页...", file=sys.stderr)
        first = get(args.url, args.timeout)
        soup = BeautifulSoup(first.text, "html.parser")

        # 检测总页数
        last_page = find_last_page(soup)
        if args.max_pages and args.max_pages > 0:
            last_page = min(last_page, args.max_pages)
        print(f"📊 检测到总页数: {last_page}", file=sys.stderr)

        # 提取第一页的 URL
        urls_page1 = extract_work_urls(soup)
        all_urls.update(urls_page1)
        completed_pages.add(1)
        
        # 保存进度
        save_progress(progress_file, completed_pages, all_urls)
        print(f"✅ 第 1/{last_page} 页完成 ({len(all_urls)} 个作品)", file=sys.stderr)
    else:
        # 如果第一页已完成，重新检测总页数
        print(f"⏭️  跳过第 1 页（已完成）", file=sys.stderr)
        first = get(args.url, args.timeout)
        soup = BeautifulSoup(first.text, "html.parser")
        last_page = find_last_page(soup)
        if args.max_pages and args.max_pages > 0:
            last_page = min(last_page, args.max_pages)
        print(f"📊 检测到总页数: {last_page}", file=sys.stderr)

    # 抓取剩余页面
    for p in range(2, last_page + 1):
        if p in completed_pages:
            print(f"⏭️  跳过第 {p} 页（已完成）", file=sys.stderr)
            continue
        
        page_url = f"{args.url}?page={p}"
        print(f"⏳ 等待 {args.sleep} 秒后获取第 {p}/{last_page} 页...", file=sys.stderr)
        time.sleep(args.sleep)
        
        try:
            r = get(page_url, args.timeout)
            soup = BeautifulSoup(r.text, "html.parser")
            urls_this_page = extract_work_urls(soup)
            all_urls.update(urls_this_page)
            completed_pages.add(p)
            
            # 每页都保存进度
            save_progress(progress_file, completed_pages, all_urls)
            print(f"✅ 第 {p}/{last_page} 页完成 ({len(all_urls)} 个作品)", file=sys.stderr)
            
        except Exception as e:
            print(f"❌ 第 {p} 页抓取失败: {e}", file=sys.stderr)
            print(f"💾 进度已保存到 {progress_file}", file=sys.stderr)
            return False  # 不 sys.exit，让调用方决定重试

    # 保存最终结果
    save_final_urls(outfile, all_urls)
    
    # 清理进度文件
    if progress_file.exists():
        progress_file.unlink()
        print(f"🗑️  清理进度文件", file=sys.stderr)
    
    print(f"🎉 全部完成！共收集 {len(all_urls)} 个作品链接", file=sys.stderr)
    return True


def main():
    timer = TimingLogger()
    timer.start_total()
    try:
        ap = argparse.ArgumentParser(description="收集 AO3 作者作品链接（支持断点续传 & 自动重试）")
        ap.add_argument("--url", default=DEFAULT_AO3_USER_URL,
                        help="作者作品页，例如 https://archiveofourown.org/users/<n>/works （方便起见，可临时设置所有作品游客可见）")
        ap.add_argument("--outfile", default=str(URLS_ALL_FILE), help="输出文件路径，例如 urls_all.txt")
        ap.add_argument("--sleep", type=float, default=3.0, help="页面间隔秒数（默认3秒）")
        ap.add_argument("--timeout", type=float, default=30, help="HTTP超时秒数（默认30秒）")
        ap.add_argument("--max-pages", type=int, default=0, help="可选：限制最大页数（0=自动检测）")
        ap.add_argument("--fresh", action="store_true", help="忽略进度文件，从头开始（默认自动 resume）")
        args = ap.parse_args()

        outfile = Path(args.outfile)
        progress_file = outfile.parent / f".{outfile.stem}_progress.json"

        # 自动重试循环：失败后等一会儿自动 resume，最多 N 轮
        for attempt in range(COLLECT_MAX_AUTO_RETRIES):
            timer.start(f"Attempt {attempt + 1}: scrape")
            success = scrape_once(args, outfile, progress_file)
            timer.stop(f"Attempt {attempt + 1}: scrape")

            if success:
                timer.print_summary()
                sys.exit(0)

            remaining = COLLECT_MAX_AUTO_RETRIES - attempt - 1
            if remaining > 0:
                # 失败后下一轮自动 resume（不管 --fresh 与否，重试时一定 resume）
                args.fresh = False
                print(f"", file=sys.stderr)
                print(f"⏳ 第 {attempt + 1} 轮失败，{COLLECT_RETRY_WAIT_SECONDS}秒后自动重试（剩余 {remaining} 次）...",
                      file=sys.stderr)
                timer.start(f"Attempt {attempt + 1}: retry wait")
                time.sleep(COLLECT_RETRY_WAIT_SECONDS)
                timer.stop(f"Attempt {attempt + 1}: retry wait")
            else:
                print(f"", file=sys.stderr)
                print(f"❌ 已达最大重试次数 ({COLLECT_MAX_AUTO_RETRIES})，放弃。", file=sys.stderr)
                print(f"💾 进度已保存，下次运行会自动 resume。", file=sys.stderr)
                timer.print_summary()
                sys.exit(1)
    except SystemExit:
        raise
    except Exception:
        timer.print_summary()
        raise

if __name__ == "__main__":
    main()
