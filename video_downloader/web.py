"""
VDL Web UI — local web server for video downloading.

Usage:
    python -m video_downloader.web
    vdl-web
"""

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from .config import DownloaderConfig
from .core import VideoDownloader
from .models import DownloadOptions, ContentType
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
# App state
# ---------------------------------------------------------------------------

class AppState:
    def __init__(self):
        self.downloader = VideoDownloader()
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

    try:
        metadata = await state.downloader.extract_metadata(url)
        return {
            "title": metadata.title,
            "author": metadata.author,
            "duration": metadata.duration,
            "thumbnail": metadata.thumbnail_url,
            "platform": metadata.platform,
            "url": metadata.url,
            "qualities": [
                {"id": q.quality_id, "name": q.name}
                for q in (metadata.quality_options or [])
            ],
            "content_type": metadata.content_type.value,
        }
    except Exception as e:
        raise HTTPException(400, str(e))


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
        _validate_cookie_path(cookie_name)

    task_id = str(uuid.uuid4())[:8]
    task = DownloadTask(id=task_id, url=url, quality=quality or "")
    state.tasks[task_id] = task

    # Start download in background, store reference for cancellation
    async_task = asyncio.create_task(_run_download(task, cookie_name))
    state.async_tasks[task_id] = async_task

    return {"id": task_id, "status": task.status}


async def _run_download(task: DownloadTask, cookie_name: Optional[str] = None):
    """Execute download in background."""
    try:
        task.status = TaskStatus.DOWNLOADING
        await state.emit({"type": "status", "id": task.id, "status": "downloading"})

        # Configure cookies if specified
        config = DownloaderConfig()
        if cookie_name:
            cookie_path = state.cookie_dir / cookie_name
            if cookie_path.exists():
                config.cookie_file = str(cookie_path)

        # Reuse the shared downloader (only override config for cookies)
        downloader = state.downloader if not cookie_name else VideoDownloader(config)

        # Extract metadata once, reuse for preview + download
        metadata = None
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

        # Check cancellation before download
        if task.status == TaskStatus.CANCELLED:
            return

        # Download
        options = DownloadOptions(quality=task.quality or None)
        result = await downloader.download(task.url, options)

        # Check cancellation after download
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

    print(f"\n  🎬 VDL Web UI")
    print(f"  http://{host}:{port}")
    print(f"  Press Ctrl+C to stop\n")

    # Open browser after server starts
    loop = asyncio.new_event_loop()
    loop.call_later(1.0, lambda: webbrowser.open(f"http://{host}:{port}"))

    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
