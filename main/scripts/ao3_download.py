#!/usr/bin/env python3
"""
AO3 作品批量下载脚本
使用 FanFicFare 从 urls_all.txt 批量下载 HTML 文件

v1.1 - 20260206
v1.1.2 - 20260416 修复*2：不再依赖系统 PATH 里的 fanficfare 命令；改为始终用当前运行脚本的 Python 解释器执行 FanFicFare

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


def fanficfare_cmd():
    """Return a command that runs FanFicFare with the current Python interpreter."""
    return [sys.executable, "-m", "fanficfare.cli"]


def check_fanficfare():
    """检查 FanFicFare 是否安装（使用当前 Python 解释器）"""
    try:
        result = subprocess.run(
            fanficfare_cmd() + ["--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version = (result.stdout or result.stderr).strip()
            print(
                f"✅ FanFicFare 已安装（当前解释器: {sys.executable}）: {version}",
                file=sys.stderr,
            )
            return True

        print("❌ 当前 Python 环境中找不到 FanFicFare。", file=sys.stderr)
        print(f"   当前解释器: {sys.executable}", file=sys.stderr)
        print("   请运行:", file=sys.stderr)
        print(f"   {sys.executable} -m pip install FanFicFare", file=sys.stderr)
        stderr_text = (result.stderr or result.stdout or "").strip()
        if stderr_text:
            print(f"   详细信息: {stderr_text}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️ 检查 FanFicFare 时出错: {e}", file=sys.stderr)
        print(f"   当前解释器: {sys.executable}", file=sys.stderr)
        print(f"   可尝试运行: {sys.executable} -m pip install FanFicFare", file=sys.stderr)
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
            fanficfare_cmd() + [
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
            fanficfare_cmd() + [
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
    timer = TimingLogger()
    timer.start_total()
    try:
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
            timer.start("Single download")
            success = download_single(args.single, args.outdir)
            timer.stop("Single download")
            timer.print_summary()
            sys.exit(0 if success else 1)
        else:
            # 批量下载模式
            timer.start("Batch download")
            success, failed_urls = download_batch(args.urls, args.outdir)
            timer.stop("Batch download")

            # 自动重试失败的 URL（逐个下载）
            if failed_urls and not args.no_retry:
                print(f"", file=sys.stderr)
                print(f"⏳ {DOWNLOAD_RETRY_WAIT_SECONDS}秒后自动重试 {len(failed_urls)} 个失败的 URL...",
                      file=sys.stderr)
                timer.start("Retry wait")
                time.sleep(DOWNLOAD_RETRY_WAIT_SECONDS)
                timer.stop("Retry wait")

                timer.start("Retry downloads")
                still_failed = []
                for url in failed_urls:
                    ok = download_single(url, args.outdir)
                    if not ok:
                        still_failed.append(url)
                timer.stop("Retry downloads")

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

            timer.print_summary()
            sys.exit(0 if success and not failed_urls else 1)
    except SystemExit:
        raise
    except Exception:
        timer.print_summary()
        raise


if __name__ == "__main__":
    main()
