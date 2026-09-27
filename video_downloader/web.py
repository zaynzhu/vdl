"""
VDL Web UI — local web server for video downloading.

Usage:
    python -m video_downloader.web
    vdl-web
"""

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .config import DownloaderConfig
from .core import VideoDownloader
from .models import DownloadOptions, ContentType, ExtractionContext
from .extractors.yt_dlp import YtDlpExtractor
from .logger import logger

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File
    from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    raise ImportError(
        "Web UI requires fastapi and uvicorn. Install with:\n"
        "  pip install fastapi uvicorn[standard]"
    )


# ---------------------------------------------------------------------------
# Download task state
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    id: str
    url: str
    title: str = ""
    thumbnail: str = ""
    duration: int = 0
    platform: str = ""
    quality: str = ""
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    file_path: str = ""
    file_size: int = 0
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# User settings (persisted)
# ---------------------------------------------------------------------------

SETTINGS_PATH = Path.home() / ".vdl" / "settings.json"

# 桌面/网页模式的默认设置；proxy 留空表示跟随环境变量（yt-dlp 原生行为）
DEFAULT_SETTINGS = {
    "proxy": "",
    "download_dir": str(Path.home() / "Downloads" / "vdl"),
    "browser_cookies": "",  # chrome / edge / firefox / safari，空 = 不使用
}

BROWSER_COOKIE_APPS = ("chrome", "edge", "firefox", "safari", "brave", "opera", "vivaldi", "chromium")


def _load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    try:
        if SETTINGS_PATH.exists():
            settings.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load settings from {SETTINGS_PATH}: {e}")
    return settings


def _save_settings(settings: dict) -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        logger.error(f"Failed to save settings to {SETTINGS_PATH}: {e}")
        raise HTTPException(500, f"无法保存设置: {e}")


# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

class AppState:
    def __init__(self):
        # Use empty cookie_file to avoid permission errors on default ./cookies.txt
        config = DownloaderConfig()
        config.cookie_file = ""
        self.downloader = VideoDownloader(config)
        self.tasks: Dict[str, DownloadTask] = {}
        self.async_tasks: Dict[str, asyncio.Task] = {}
        self.sse_clients: Set[asyncio.Queue] = set()
        self.cookie_dir = Path("./cookies")
        self.cookie_dir.mkdir(exist_ok=True)

    async def emit(self, event: dict):
        """Broadcast event to all connected SSE clients."""
        dead = set()
        for q in self.sse_clients:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.add(q)
        self.sse_clients -= dead


def _make_config(cookie_name: Optional[str] = None) -> DownloaderConfig:
    """Create a config with safe defaults for web usage."""
    config = DownloaderConfig()
    # Don't use the default ./cookies.txt — it may not exist or be locked
    config.cookie_file = ""
    if cookie_name:
        cookie_path = state.cookie_dir / cookie_name
        if cookie_path.exists():
            config.cookie_file = str(cookie_path)
    return config


state = AppState()

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="VDL Web UI", version="0.1.0")

# Serve static files
STATIC_DIR = Path(__file__).parent / "web_static"


@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>VDL Web UI</h1><p>index.html not found</p>")


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

@app.post("/api/preview")
async def preview(body: dict):
    """Extract metadata for a URL without downloading."""
    url = body.get("url", "").strip()
    if not url:
        raise HTTPException(400, "URL is required")

    # 预览与下载共用 cookies/代理设置：YouTube 无 cookies 预览会报 bot 检测
    settings = _load_settings()
    cookie_file, browser_spec = _resolve_cookie_source(body.get("cookie"), settings)
    proxy = settings.get("proxy") or None
    browser_cookies = browser_spec[0] if browser_spec else None

    extractor = YtDlpExtractor()
    platform_name = extractor.get_platform_name_for_url(url) or "yt_dlp"
    context = ExtractionContext(
        cookies=[],
        fingerprint=state.downloader.fingerprint_gen.generate_fingerprint(platform_name),
    )

    try:
        metadata = await extractor.extract_metadata(
            url, context,
            cookie_file=cookie_file,
            proxy=proxy,
            browser_cookies=browser_cookies,
        )
    except Exception as e:
        raise HTTPException(400, str(e))

    return {
        "title": metadata.title,
        "author": metadata.author,
        "duration": metadata.duration,
        "thumbnail": metadata.thumbnail_url,
        "platform": metadata.platform,
        "url": metadata.url,
        "qualities": [
            {
                "id": q.quality_id,
                "name": q.name,
                "height": q.height,
                "size": q.file_size_estimate,
            }
            for q in (metadata.quality_options or [])
        ],
        "content_type": metadata.content_type.value,
    }


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

@app.post("/api/download")
async def start_download(body: dict):
    """Start downloading a video."""
    url = body.get("url", "").strip()
    quality = body.get("quality")
    cookie_name = body.get("cookie")

    if not url:
        raise HTTPException(400, "URL is required")

    # Validate cookie_name if provided
    if cookie_name:
        if not cookie_name.startswith("browser:"):
            _validate_cookie_path(cookie_name)

    task_id = str(uuid.uuid4())[:8]
    task = DownloadTask(
        id=task_id,
        url=url,
        quality=quality or "",
        # 预览阶段已拿到的元数据直接带上，避免下载端二次提取
        title=str(body.get("title") or ""),
        thumbnail=str(body.get("thumbnail") or ""),
        platform=str(body.get("platform") or ""),
        duration=int(body.get("duration") or 0),
    )
    state.tasks[task_id] = task

    # Start download in background, store reference for cancellation
    async_task = asyncio.create_task(_run_download(task, cookie_name))
    state.async_tasks[task_id] = async_task

    return {"id": task_id, "status": task.status}


def _build_format_selector(quality: Optional[str]) -> str:
    """把画质档翻译成 yt-dlp format selector。

    - 空 → 最高画质（含 4K）
    - format_id（如 '313'）→ 直选该视频流 + 最佳音频
    - 高度形式（如 '2160p'）→ 高度上限选择器
    """
    if not quality:
        return "bv*+ba/b"
    q = quality.strip().lower()
    if q.endswith("p") and q[:-1].isdigit():
        height = int(q[:-1])
        return f"bv*[height<={height}]+ba/b[height<={height}]/bv*+ba/b"
    if q.isdigit():
        return f"{q}+bestaudio/{q}/bv*+ba/b"
    return "bv*+ba/b"


def _resolve_cookie_source(
    cookie_name: Optional[str], settings: dict
) -> Tuple[Optional[str], Optional[tuple]]:
    """解析 cookies 来源 → (cookie_file, browser_spec)。UI 显式选择优先于设置默认值。"""
    if cookie_name:
        if cookie_name.startswith("browser:"):
            app = cookie_name.split(":", 1)[1]
            if app in BROWSER_COOKIE_APPS:
                return None, (app,)
        else:
            path = state.cookie_dir / Path(cookie_name).name
            if path.exists():
                return str(path), None
        return None, None
    default_browser = settings.get("browser_cookies") or ""
    if default_browser in BROWSER_COOKIE_APPS:
        return None, (default_browser,)
    return None, None


async def _download_with_ytdlp(task: DownloadTask, cookie_name: Optional[str]) -> None:
    """用 yt-dlp 直接下载（含分片与 ffmpeg 合并）。

    走 lessons 验证过的链路：yt-dlp ≥2026.8 + 代理 + cookies。
    适用于 YtDlpExtractor 覆盖的平台，绕开 core.py 对 DASH 内容的单 URL 缺陷。
    """
    import yt_dlp

    settings = _load_settings()
    output_dir = os.path.expanduser(
        settings.get("download_dir") or DEFAULT_SETTINGS["download_dir"]
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cookie_file, browser_spec = _resolve_cookie_source(cookie_name, settings)
    # proxy 留空 = 交给 yt-dlp 读环境变量
    proxy = settings.get("proxy") or None

    loop = asyncio.get_running_loop()
    last_emit = {"ts": 0.0}

    def progress_hook(d):
        if d.get("status") != "downloading":
            return
        now = time.monotonic()
        if now - last_emit["ts"] < 1.0:  # 节流：每秒最多推一次
            return
        last_emit["ts"] = now
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        done = d.get("downloaded_bytes") or 0
        pct = round(done / total * 100, 1) if total else 0
        task.progress = pct
        asyncio.run_coroutine_threadsafe(
            state.emit({"type": "progress", "id": task.id, "progress": pct}), loop
        )

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "outtmpl": str(Path(output_dir) / "%(title).70s.%(ext)s"),
        "format": _build_format_selector(task.quality or None),
        "merge_output_format": "mp4",
        "retries": 3,
        # YouTube JS 挑战求解器（详见 lessons/ytdlp-ejs-challenge.md）
        "remote_components": ["ejs:github"],
        "progress_hooks": [progress_hook],
    }
    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file
    if browser_spec:
        ydl_opts["cookiesfrombrowser"] = browser_spec
    if proxy:
        ydl_opts["proxy"] = proxy

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(task.url, download=True)

    try:
        info = await asyncio.to_thread(_run)
        requested = info.get("requested_downloads") or []
        file_path = ""
        if requested:
            file_path = requested[0].get("filepath") or requested[0].get("filename") or ""
        if not file_path:
            raise RuntimeError("下载完成但未找到输出文件")
        task.file_path = file_path
        task.file_size = os.path.getsize(file_path)
        task.progress = 100.0
        if not task.title:
            task.title = info.get("title", "")
        task.status = TaskStatus.COMPLETED
        await state.emit({
            "type": "completed", "id": task.id,
            "file_path": task.file_path, "file_size": task.file_size,
        })
    except asyncio.CancelledError:
        raise
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        await state.emit({"type": "failed", "id": task.id, "error": task.error})


async def _download_via_core(task: DownloadTask, cookie_name: Optional[str]) -> None:
    """原有链路：走 VideoDownloader（DouyinExtractor 等平台）。"""
    try:
        config = _make_config(cookie_name)
        downloader = state.downloader if not cookie_name else VideoDownloader(config)

        if not task.title:
            try:
                metadata = await downloader.extract_metadata(task.url)
                task.title = metadata.title
                task.thumbnail = metadata.thumbnail_url
                task.duration = metadata.duration
                task.platform = metadata.platform
                await state.emit({
                    "type": "preview", "id": task.id,
                    "title": task.title, "thumbnail": task.thumbnail,
                    "platform": task.platform,
                })
            except Exception:
                pass

        if task.status == TaskStatus.CANCELLED:
            return

        options = DownloadOptions(quality=task.quality or None)
        result = await downloader.download(task.url, options)

        if task.status == TaskStatus.CANCELLED:
            return

        if result.success:
            task.status = TaskStatus.COMPLETED
            task.file_path = result.file_path or ""
            task.file_size = result.file_size
            await state.emit({
                "type": "completed", "id": task.id,
                "file_path": task.file_path, "file_size": task.file_size,
            })
        else:
            task.status = TaskStatus.FAILED
            task.error = result.error or "Unknown error"
            await state.emit({
                "type": "failed", "id": task.id, "error": task.error,
            })
    except asyncio.CancelledError:
        raise


async def _run_download(task: DownloadTask, cookie_name: Optional[str] = None):
    """Execute download in background."""
    try:
        task.status = TaskStatus.DOWNLOADING
        await state.emit({"type": "status", "id": task.id, "status": "downloading"})

        # 平台分流：yt-dlp 覆盖的平台走直连下载，其余走 core 原路径
        try:
            extractor = state.downloader._get_extractor_for_url(task.url)
        except Exception as e:
            logger.warning(f"Extractor selection failed for {task.url}: {e}")
            extractor = None

        if isinstance(extractor, YtDlpExtractor):
            await _download_with_ytdlp(task, cookie_name)
        else:
            await _download_via_core(task, cookie_name)

    except asyncio.CancelledError:
        task.status = TaskStatus.CANCELLED
        await state.emit({"type": "cancelled", "id": task.id})
    except Exception as e:
        if task.status != TaskStatus.CANCELLED:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await state.emit({"type": "failed", "id": task.id, "error": str(e)})
    finally:
        state.async_tasks.pop(task.id, None)


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------

@app.get("/api/queue")
async def get_queue():
    """Get all download tasks."""
    return [asdict(t) for t in state.tasks.values()]


@app.delete("/api/queue/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a pending/running task."""
    task = state.tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        raise HTTPException(400, "Task already finished")

    task.status = TaskStatus.CANCELLED

    # Actually cancel the asyncio task
    async_task = state.async_tasks.get(task_id)
    if async_task and not async_task.done():
        async_task.cancel()

    await state.emit({"type": "cancelled", "id": task_id})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Cookies
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """Sanitize uploaded filename — strip path components and dangerous chars."""
    # Take only the basename (strip any path traversal)
    name = Path(name).name
    # Reject empty or dot-only names
    if not name or name in (".", ".."):
        raise HTTPException(400, "Invalid filename")
    # Reject path separators (belt-and-suspenders)
    if "/" in name or "\\" in name or "\0" in name:
        raise HTTPException(400, "Invalid filename")
    return name


def _validate_cookie_path(name: str) -> Path:
    """Validate that cookie name resolves to a path inside cookie_dir."""
    _sanitize_filename(name)
    resolved = (state.cookie_dir / name).resolve()
    cookie_resolved = state.cookie_dir.resolve()
    if not str(resolved).startswith(str(cookie_resolved)):
        raise HTTPException(400, "Invalid cookie name")
    return resolved


@app.get("/api/cookies")
async def list_cookies():
    """List uploaded cookie files."""
    cookies = []
    for f in state.cookie_dir.glob("*.txt"):
        cookies.append({
            "name": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return cookies


@app.post("/api/cookies")
async def upload_cookie(file: UploadFile = File(...)):
    """Upload a cookies.txt file."""
    if not file.filename:
        raise HTTPException(400, "No filename")
    name = _sanitize_filename(file.filename)
    dest = state.cookie_dir / name
    content = await file.read()
    dest.write_bytes(content)
    return {"name": name, "size": len(content)}


@app.delete("/api/cookies/{name}")
async def delete_cookie(name: str):
    """Delete a cookie file."""
    path = _validate_cookie_path(name)
    if not path.exists():
        raise HTTPException(404, "Cookie file not found")
    path.unlink()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.get("/api/settings")
async def get_settings():
    """Return user settings plus the effective proxy value."""
    settings = _load_settings()
    # 设置值优先；留空时回落到环境变量（yt-dlp 也会自动读取）
    effective_proxy = (
        settings.get("proxy")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("HTTP_PROXY")
        or ""
    )
    return {**settings, "effective_proxy": effective_proxy}


@app.post("/api/settings")
async def update_settings(body: dict):
    """Update persisted user settings."""
    settings = _load_settings()
    for key in ("proxy", "download_dir", "browser_cookies"):
        if key in body:
            settings[key] = str(body.get(key) or "").strip()
    if settings.get("browser_cookies") and settings["browser_cookies"] not in BROWSER_COOKIE_APPS:
        raise HTTPException(400, f"不支持的浏览器: {settings['browser_cookies']}")
    _save_settings(settings)
    return {"ok": True, **settings}


# ---------------------------------------------------------------------------
# SSE (Server-Sent Events) for progress
# ---------------------------------------------------------------------------

@app.get("/api/events")
async def events():
    """SSE endpoint for real-time progress updates."""
    client_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    state.sse_clients.add(client_queue)

    async def generate():
        try:
            while True:
                event = await client_queue.get()
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            state.sse_clients.discard(client_queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Start the VDL Web UI server."""
    import webbrowser

    host = os.environ.get("VDL_HOST", "127.0.0.1")
    port = int(os.environ.get("VDL_PORT", "19002"))

    print(f"\n  VDL Web UI")
    print(f"  http://{host}:{port}")
    print(f"  Press Ctrl+C to stop\n")

    # Open browser after server starts
    loop = asyncio.new_event_loop()
    loop.call_later(1.0, lambda: webbrowser.open(f"http://{host}:{port}"))

    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
