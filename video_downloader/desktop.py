"""
VDL Desktop — pywebview 壳，复用 FastAPI Web UI。

启动链：注入打包资源 PATH → uvicorn 起在 127.0.0.1 随机空闲端口
→ pywebview 开原生窗口加载该地址 → 关窗即退出进程。

Usage:
    python -m video_downloader.desktop
    vdl-app
"""

import os
import socket
import sys
import threading
import time
from pathlib import Path

from .logger import logger


def _inject_bundled_binaries() -> None:
    """打包后把 .app/Contents/Resources/bin 里的 ffmpeg 等注入 PATH。"""
    if not getattr(sys, "frozen", False):
        return
    contents = Path(sys.executable).parent.parent  # .../VDL.app/Contents
    res_bin = contents / "Resources" / "bin"
    if res_bin.is_dir():
        os.environ["PATH"] = f"{res_bin}:{os.environ.get('PATH', '')}"
        logger.info(f"Bundled binaries injected: {res_bin}")


def _pick_port() -> int:
    # VDL_DESKTOP_PORT 供自动化测试固定端口；默认随机空闲端口
    custom = os.environ.get("VDL_DESKTOP_PORT")
    if custom and custom.isdigit():
        return int(custom)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    _inject_bundled_binaries()

    import uvicorn
    import webview

    from .web import app

    port = _pick_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # 等 uvicorn 完成启动再开窗口，避免窗口白屏
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    else:
        logger.error("Web server failed to start in time")
        return

    logger.info(f"VDL Desktop ready at http://127.0.0.1:{port}")
    window = webview.create_window(
        "VDL Video Downloader",
        f"http://127.0.0.1:{port}",
        width=920,
        height=780,
        min_size=(680, 560),
    )
    webview.start()  # 阻塞到窗口关闭

    server.should_exit = True
    server_thread.join(timeout=5)
    logger.info("VDL Desktop exited")


if __name__ == "__main__":
    main()
