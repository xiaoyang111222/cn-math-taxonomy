#!/usr/bin/env python3
"""知识图谱 · 本地预览启动器。

在仓库根目录起一个静态服务器，并用默认浏览器打开首页。页面通过 fetch 读取
data/*.json，浏览器不允许用 file:// 直接打开，所以本地查看必须起静态服务器
（README「打开网页」一节）。这个脚本就是那一步的封装：

- 默认监听 http://127.0.0.1:8000/
- 如果本项目的预览服务已经在运行，只提示一句，**不再新开浏览器标签页**
- 还没运行时，选第一个可绑定端口（8000、8001……），起服务并打开一次首页
- 关闭这个窗口即停止服务

用法：python scripts/preview.py [--port 8000] [--no-browser]
"""

from __future__ import annotations

import argparse
import functools
import http.server
import mimetypes
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8000
PORT_SCAN = 20
MARKER = b"assets/site.css"          # 本项目 index.html 的特征串

mimetypes.add_type("application/manifest+json", ".webmanifest")


class PreviewServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False      # Windows 上 SO_REUSEADDR 会允许端口被重复占用


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    """静态文件 + 关掉缓存（改完 data/ 刷新即可看到）。"""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:  # 页面一次加载几十个请求，不刷屏
        pass


def probe(port: int, timeout: float = 1.2) -> bool:
    """判断该端口上是否已经是本项目的预览服务。"""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/index.html", timeout=timeout) as resp:
            body = resp.read(8192)
            return resp.status == 200 and MARKER in body
    except Exception:
        return False


def open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass


def set_console_title(text: str) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(text)
    except Exception:
        pass


def banner(port: int, reused: bool) -> str:
    url = f"http://127.0.0.1:{port}/"
    lines = [
        "=" * 56,
        "  知识图谱 · 本地预览",
        f"  目录：{ROOT}",
        f"  地址：{url}",
    ]
    if reused:
        lines.append("  服务已在运行，这次不再新开浏览器标签页。")
    else:
        lines.append("  已在默认浏览器打开；关闭本窗口即停止服务。")
    lines.append("=" * 56)
    return "\n".join(lines)


def find_running(base: int) -> int | None:
    """找已经在运行的本项目预览服务，返回端口；没有则 None。"""
    for port in range(base, base + PORT_SCAN):
        if probe(port):
            return port
    return None


def bind_first_free(base: int) -> PreviewServer | None:
    """按顺序绑定第一个可用端口；全被占用时返回 None。"""
    handler = functools.partial(PreviewHandler, directory=str(ROOT))
    for port in range(base, base + PORT_SCAN):
        try:
            return PreviewServer(("127.0.0.1", port), handler)
        except OSError:
            continue
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="知识图谱本地预览启动器")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="起始端口，默认 8000")
    parser.add_argument("--no-browser", action="store_true", help="只起服务，不打开浏览器")
    args = parser.parse_args(argv)

    base = args.port

    # 已经在运行：只提示，不再新开标签页（用户 2026-11-12 要求）。
    running = find_running(base)
    if running is not None:
        print(banner(running, reused=True), flush=True)
        return 0

    httpd = bind_first_free(base)
    if httpd is None:
        print(f"没有可用端口（{base}–{base + PORT_SCAN - 1}）。", file=sys.stderr)
        return 1

    set_console_title(f"知识图谱本地预览 - 127.0.0.1:{httpd.server_port}")
    print(banner(httpd.server_port, reused=False), flush=True)
    if not args.no_browser:
        threading.Timer(0.3, open_browser, [f"http://127.0.0.1:{httpd.server_port}/"]).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
