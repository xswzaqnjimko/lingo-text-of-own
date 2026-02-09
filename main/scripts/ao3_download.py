#!/usr/bin/env python3
"""
AO3 作品批量下载脚本
使用 FanFicFare 从 urls_all.txt 批量下载 HTML 文件

v1.1 - 20260206

使用方法：
    # 直接在 PyCharm 运行（使用默认路径）：
    python3 ao3_download.py

    # 或指定路径：
    python3 ao3_download.py --urls /path/to/urls.txt --outdir /path/to/downloads

    # 下载单个失败的作品：
    python3 ao3_download.py --single "https://archiveofourown.org/works/12345"

前置条件：
    pip install FanFicFare
"""

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from dependencies.config import URLS_ALL_FILE, AO3_DOWNLOADS_DIR, DOWNLOAD_RETRY_WAIT_SECONDS


def check_fanficfare():
    """检查 FanFicFare 是否安装"""
    try:
        result = subprocess.run(
            ["fanficfare", "--version"],
            capture_output=True, text=True, timeout=10
        )
        print(f"✅ FanFicFare 已安装: {result.stdout.strip()}", file=sys.stderr)
        return True
    except FileNotFoundError:
        print("❌ FanFicFare 未安装。请先运行: pip install FanFicFare", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️ 检查 FanFicFare 时出错: {e}", file=sys.stderr)
        return False


def count_existing(outdir):
    """统计已下载的 HTML 文件数"""
    return len(list(Path(outdir).glob("*.html")))


def download_batch(urls_file, outdir):
    """
    使用 FanFicFare 批量下载

    （来自 README_URL收集v3.md 的踩坑记录：）
    - 必须 cd 到目标目录，然后用 outdir="." 才能正确下载到目标位置
    - 直接指定绝对路径的 outdir 会下载到当前目录（FFF 的 bug？）

    Returns:
        (success, failed_urls): 是否全部成功, 失败的URL列表
    """
    urls_file = Path(urls_file)
    outdir = Path(outdir)

    if not urls_file.exists():
        print(f"❌ URL 文件不存在: {urls_file}", file=sys.stderr)
        print(f"💡 请先运行 ao3_collect_urls.py 收集 URL", file=sys.stderr)
        return False, []

    # 确保输出目录存在
    outdir.mkdir(parents=True, exist_ok=True)

    # 读取 URL 数量
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    total = len(urls)

    existing = count_existing(outdir)
    print(f"📊 URL 文件: {urls_file}", file=sys.stderr)
    print(f"📊 输出目录: {outdir}", file=sys.stderr)
    print(f"📊 待下载: {total} 个 URL，已有 {existing} 个 HTML 文件", file=sys.stderr)
    print(f"", file=sys.stderr)

    # cd 到目标目录再运行，用 outdir="."
    # （参考 README_URL收集v3.md 中的踩坑记录）
    print(f"🚀 开始下载...", file=sys.stderr)
    print(f"", file=sys.stderr)

    # 统计用
    failed_urls = []
    skipped_uptodate = 0
    adult_blocked = 0

    try:
        proc = subprocess.Popen(
            [
                "fanficfare",
                "-i", str(urls_file.resolve()),  # 用绝对路径指向 URL 文件
                "-f", "html",
                "-o", 'outdir="."',
                "-o", "is_adult=true",  # 允许下载 Mature/Explicit 作品
            ],
            cwd=str(outdir),  # cd 到目标目录
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 合并到 stdout 方便逐行读
            text=True,
        )

        for line in proc.stdout:
            line = line.rstrip('\n')
            print(line)  # 实时输出给用户看

            # 分类统计
            if "more recently than Story" in line and "Skipping" in line:
                skipped_uptodate += 1
            elif "Adult check required" in line:
                adult_blocked += 1
            elif line.startswith("URL(") and "Failed" in line:
                m = re.search(r'URL\((https?://[^)]+)\)', line)
                if m:
                    failed_urls.append(m.group(1))

        proc.wait()

        final_count = count_existing(outdir)
        new_downloads = final_count - existing

        # 打印总结
        print(f"", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)
        print(f"📊 下载总结：", file=sys.stderr)
        print(f"  ✅ 新增下载: {new_downloads} 个", file=sys.stderr)
        print(f"  ⏭️  跳过（文件已最新）: {skipped_uptodate} 个", file=sys.stderr)
        if adult_blocked > 0:
            print(f"  🔞 跳过（需 adult 确认）: {adult_blocked} 个", file=sys.stderr)
        if failed_urls:
            print(f"  ❌ 失败: {len(failed_urls)} 个", file=sys.stderr)
            for url in failed_urls:
                print(f"     - {url}", file=sys.stderr)
        unaccounted = total - new_downloads - skipped_uptodate - adult_blocked - len(failed_urls)
        # unaccounted 包含已有且本次新增的重复（normally ~0 or equal to existing that were already downloaded previously）
        print(f"  📦 目录中共: {final_count} 个 HTML（目标 {total} 个）", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)

        if not failed_urls and adult_blocked == 0:
            print(f"🎉 全部完成！", file=sys.stderr)

        return (len(failed_urls) == 0 and adult_blocked == 0), failed_urls

    except KeyboardInterrupt:
        final_count = count_existing(outdir)
        print(f"\n⏹️ 用户中断。已下载 {final_count} 个文件。", file=sys.stderr)
        print(f"💡 已下载的文件不受影响，可以再次运行继续。", file=sys.stderr)
        return False, []
    except Exception as e:
        print(f"❌ 下载失败: {e}", file=sys.stderr)
        return False, []


def download_single(url, outdir):
    """下载单个 URL（用于重试失败的）"""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"📥 下载: {url}", file=sys.stderr)

    try:
        result = subprocess.run(
            [
                "fanficfare",
                "-f", "html",
                "-o", 'outdir="."',
                "-o", "is_adult=true",
                url
            ],
            cwd=str(outdir),
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 失败: {e}", file=sys.stderr)
        return False


def main():
    _start = datetime.now()  # Timer just for fun...

    ap = argparse.ArgumentParser(description="使用 FanFicFare 批量下载 AO3 作品 HTML")
    ap.add_argument("--urls", default=str(URLS_ALL_FILE),
                    help="URL 列表文件路径")
    ap.add_argument("--outdir", default=str(AO3_DOWNLOADS_DIR),
                    help="下载输出目录")
    ap.add_argument("--single", type=str, default=None,
                    help="下载单个 URL（用于重试特定失败的作品）")
    ap.add_argument("--no-retry", action="store_true",
                    help="不自动重试失败的 URL")
    args = ap.parse_args()

    # 检查 FanFicFare
    if not check_fanficfare():
        sys.exit(1)

    if args.single:
        # 单个下载模式
        success = download_single(args.single, args.outdir)
        sys.exit(0 if success else 1)
    else:
        # 批量下载模式
        success, failed_urls = download_batch(args.urls, args.outdir)

        # 自动重试失败的 URL（逐个下载）
        if failed_urls and not args.no_retry:
            print(f"", file=sys.stderr)
            print(f"⏳ {DOWNLOAD_RETRY_WAIT_SECONDS}秒后自动重试 {len(failed_urls)} 个失败的 URL...", file=sys.stderr)
            time.sleep(DOWNLOAD_RETRY_WAIT_SECONDS)

            still_failed = []
            for url in failed_urls:
                ok = download_single(url, args.outdir)
                if not ok:
                    still_failed.append(url)

            if still_failed:
                print(f"", file=sys.stderr)
                print(f"⚠️ 重试后仍有 {len(still_failed)} 个失败：", file=sys.stderr)
                for url in still_failed:
                    print(f"   - {url}", file=sys.stderr)
                print(f"💡 可以稍后用 --single 手动重试", file=sys.stderr)
            else:
                print(f"✅ 重试全部成功！", file=sys.stderr)

            final_count = count_existing(args.outdir)
            print(f"📦 目录中最终共 {final_count} 个 HTML", file=sys.stderr)

        sys.exit(0 if success and not failed_urls else 1)

    print(f"⏱️ 本次耗时: {datetime.now() - _start}", file=sys.stderr)


if __name__ == "__main__":
    main()
