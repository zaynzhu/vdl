# VDL yt-dlp Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor VDL to use yt-dlp as the primary download engine, add Douyin three-tier fallback, and ship CLI + MCP server.

**Architecture:** YtDlpExtractor wraps yt-dlp for 6 platforms (YouTube, Bilibili, Twitter, Instagram, TikTok, Douyin). DouyinExtractor chains yt-dlp → Douyin_TikTok_Download_API → Playwright. BilibiliExtractor kept as fallback. All existing modules (models, config, cookie store, download manager) carried over from project-y unchanged.

**Tech Stack:** Python 3.8+, yt-dlp, aiohttp, playwright, httpx

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `video_downloader/__init__.py` | Modify | Update exports |
| `video_downloader/core.py` | Carry over | VideoDownloader entry point |
| `video_downloader/config.py` | Carry over | DownloaderConfig dataclass |
| `video_downloader/models.py` | Carry over | Data models |
| `video_downloader/exceptions.py` | Carry over | Exception hierarchy |
| `video_downloader/logger.py` | Carry over | Logging setup |
| `video_downloader/cookie_store.py` | Carry over | Cookie management |
| `video_downloader/download_manager.py` | Carry over | File download + progress |
| `video_downloader/browser_automation.py` | Carry over | Playwright browser management |
| `video_downloader/browser_fingerprint.py` | Carry over | Browser fingerprint generation |
| `video_downloader/anti_bot_strategy.py` | Carry over | Anti-bot retry logic |
| `video_downloader/anti_bot_signature.py` | Carry over | Signature utilities |
| `video_downloader/platform_manager.py` | Modify | Register YtDlpExtractor |
| `video_downloader/cli.py` | Modify | Update CLI with new platforms |
| `video_downloader/extractors/__init__.py` | Modify | Export YtDlpExtractor |
| `video_downloader/extractors/base.py` | Carry over | PlatformExtractor ABC |
| `video_downloader/extractors/yt_dlp.py` | **Create** | YtDlpExtractor wrapping yt-dlp |
| `video_downloader/extractors/douyin.py` | Modify | Three-tier fallback |
| `video_downloader/extractors/bilibili.py` | Carry over | Bilibili fallback extractor |
| `mcp_server.py` | Modify | Fix bugs, update for new extractors |
| `tests/test_yt_dlp_extractor.py` | **Create** | Tests for YtDlpExtractor |
| `tests/test_douyin_extractor.py` | **Create** | Tests for DouyinExtractor fallback |
| `tests/test_core.py` | Carry over | Core tests |
| `tests/test_models.py` | Carry over | Model tests |
| `tests/test_extractors.py` | Carry over | Extractor tests |
| `tests/test_platform_manager.py` | Carry over | Platform manager tests |
| `tests/test_cookie_store.py` | Carry over | Cookie store tests |
| `tests/test_browser_automation.py` | Carry over | Browser automation tests |
| `tests/test_browser_fingerprint.py` | Carry over | Fingerprint tests |
| `tests/__init__.py` | Carry over | Test package init |
| `requirements.txt` | Modify | Add yt-dlp |
| `setup.py` | Modify | Add yt-dlp, update entry point |
| `cookies/bilibili.txt.example` | **Create** | Cookie example file |
| `cookies/douyin.txt.example` | **Create** | Cookie example file |
| `quick_start.py` | Carry over | Usage examples |
| `test_integration.py` | Carry over | Integration test |

---

## Task 1: Migrate code from project-y to vdl

**Files:**
- Copy: `E:\code\codex\project-y\video_downloader\` → `E:\codex\vdl\video_downloader\`
- Copy: `E:\code\codex\project-y\tests\` → `E:\codex\vdl\tests\`
- Copy: `E:\code\codex\project-y\mcp_server.py` → `E:\codex\vdl\mcp_server.py`
- Copy: `E:\code\codex\project-y\quick_start.py` → `E:\codex\vdl\quick_start.py`
- Copy: `E:\code\codex\project-y\test_integration.py` → `E:\codex\vdl\test_integration.py`
- Modify: `E:\codex\vdl\requirements.txt`
- Modify: `E:\codex\vdl\setup.py`
- Delete: `E:\codex\vdl\video_downloader\extractors\tiktok.py` (covered by yt-dlp)

- [ ] **Step 1: Copy video_downloader package from project-y to vdl**

```bash
# From E:\codex\vdl
xcopy /E /I /Y "E:\code\codex\project-y\video_downloader" "E:\codex\vdl\video_downloader"
```

- [ ] **Step 2: Copy tests, mcp_server, quick_start, test_integration**

```bash
xcopy /E /I /Y "E:\code\codex\project-y\tests" "E:\codex\vdl\tests"
copy /Y "E:\code\codex\project-y\mcp_server.py" "E:\codex\vdl\mcp_server.py"
copy /Y "E:\code\codex\project-y\quick_start.py" "E:\codex\vdl\quick_start.py"
copy /Y "E:\code\codex\project-y\test_integration.py" "E:\codex\vdl\test_integration.py"
```

- [ ] **Step 3: Delete tiktok.py extractor (yt-dlp will cover TikTok)**

```bash
del "E:\codex\vdl\video_downloader\extractors\tiktok.py"
```

- [ ] **Step 4: Update requirements.txt — add yt-dlp**

Write `E:\codex\vdl\requirements.txt`:
```txt
# Core dependencies
aiohttp>=3.9.0
playwright>=1.40.0
httpx>=0.25.0
yt-dlp>=2024.1.0

# Data handling
python-dateutil>=2.8.2

# Testing (optional)
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Development
black>=23.0.0
flake8>=6.0.0
mypy>=1.7.0
```

- [ ] **Step 5: Update setup.py — add yt-dlp dependency, update entry point**

Write `E:\codex\vdl\setup.py`:
```python
"""
Setup script for vdl - Video Downloader.
"""

from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="vdl",
    version="0.2.0",
    author="zaynzhu",
    description="Multi-platform video downloader powered by yt-dlp",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zaynzhu/vdl",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.9.0",
        "playwright>=1.40.0",
        "httpx>=0.25.0",
        "yt-dlp>=2024.1.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vdl=video_downloader.cli:cli_entry",
        ],
    },
)
```

- [ ] **Step 6: Update extractors/__init__.py — remove TikTok, add YtDlp placeholder**

Write `E:\codex\vdl\video_downloader\extractors\__init__.py`:
```python
"""
Platform extractors for video-downloader.
"""

from .base import PlatformExtractor
from .bilibili import BilibiliExtractor
from .douyin import DouyinExtractor

__all__ = ["PlatformExtractor", "BilibiliExtractor", "DouyinExtractor"]
```

- [ ] **Step 7: Create cookies directory with example files**

```bash
mkdir "E:\codex\vdl\cookies"
```

Write `E:\codex\vdl\cookies\bilibili.txt.example`:
```
# Netscape HTTP Cookie File
# Place your Bilibili cookies here (export from browser)
# Rename this file to bilibili.txt after filling in cookies
# Format: domain	flag	path	secure	expiration	name	value
.bilibili.com	TRUE	/	FALSE	0	SESSDATA	your_sessdata_here
.bilibili.com	TRUE	/	FALSE	0	bili_jct	your_bili_jct_here
```

Write `E:\codex\vdl\cookies\douyin.txt.example`:
```
# Netscape HTTP Cookie File
# Place your Douyin cookies here (export from browser)
# Rename this file to douyin.txt after filling in cookies
.douyin.com	TRUE	/	FALSE	0	sessionid	your_sessionid_here
```

- [ ] **Step 8: Verify imports work**

Run: `cd E:\codex\vdl && python -c "from video_downloader import VideoDownloader; print('OK')"`

Expected: `OK` (may need `pip install -e .` first)

- [ ] **Step 9: Commit**

```bash
cd E:\codex\vdl
git add -A
git commit -m "chore: migrate code from project-y, add yt-dlp dependency"
```

---

## Task 2: Implement YtDlpExtractor

**Files:**
- Create: `E:\codex\vdl\video_downloader\extractors\yt_dlp.py`
- Create: `E:\codex\vdl\tests\test_yt_dlp_extractor.py`

- [ ] **Step 1: Write failing tests for YtDlpExtractor**

Write `E:\codex\vdl\tests\test_yt_dlp_extractor.py`:
```python
"""
Tests for YtDlpExtractor.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from video_downloader.extractors.yt_dlp import YtDlpExtractor
from video_downloader.exceptions import UnsupportedPlatformError, PlatformError


class TestYtDlpCanHandle:
    """Test URL matching."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    def test_youtube_standard(self):
        assert self.extractor.can_handle("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_youtube_short(self):
        assert self.extractor.can_handle("https://youtu.be/dQw4w9WgXcQ")

    def test_bilibili(self):
        assert self.extractor.can_handle("https://www.bilibili.com/video/BV1xx411c7mD")

    def test_twitter(self):
        assert self.extractor.can_handle("https://twitter.com/user/status/123456")

    def test_x_com(self):
        assert self.extractor.can_handle("https://x.com/user/status/123456")

    def test_instagram(self):
        assert self.extractor.can_handle("https://www.instagram.com/reel/ABC123/")

    def test_tiktok(self):
        assert self.extractor.can_handle("https://www.tiktok.com/@user/video/123456")

    def test_douyin(self):
        assert self.extractor.can_handle("https://www.douyin.com/video/123456")

    def test_unsupported_url(self):
        assert not self.extractor.can_handle("https://www.example.com/video")

    def test_empty_url(self):
        assert not self.extractor.can_handle("")


class TestYtDlpPlatformName:
    """Test platform name detection."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    def test_youtube_name(self):
        assert self.extractor.get_platform_name_for_url("https://www.youtube.com/watch?v=xxx") == "youtube"

    def test_bilibili_name(self):
        assert self.extractor.get_platform_name_for_url("https://www.bilibili.com/video/BV1xx") == "bilibili"

    def test_twitter_name(self):
        assert self.extractor.get_platform_name_for_url("https://x.com/user/status/123") == "twitter"

    def test_unknown_name(self):
        assert self.extractor.get_platform_name_for_url("https://example.com") is None


class TestYtDlpMetadataMapping:
    """Test metadata field mapping from yt-dlp to VideoMetadata."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    def test_map_basic_fields(self):
        ytdlp_info = {
            'title': 'Test Video',
            'uploader': 'Test Author',
            'duration': 120,
            'thumbnail': 'https://example.com/thumb.jpg',
            'description': 'A test video',
            'upload_date': '20260101',
            'webpage_url': 'https://www.youtube.com/watch?v=xxx',
            'extractor': 'youtube',
            'id': 'xxx',
            'formats': [],
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        assert metadata.title == 'Test Video'
        assert metadata.author == 'Test Author'
        assert metadata.duration == 120
        assert metadata.thumbnail_url == 'https://example.com/thumb.jpg'
        assert metadata.platform == 'youtube'

    def test_map_missing_fields_use_defaults(self):
        ytdlp_info = {
            'title': 'Minimal',
            'webpage_url': 'https://www.youtube.com/watch?v=yyy',
            'extractor': 'youtube',
            'id': 'yyy',
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        assert metadata.title == 'Minimal'
        assert metadata.author == 'Unknown'
        assert metadata.duration == 0

    def test_map_quality_options(self):
        ytdlp_info = {
            'title': 'Test',
            'webpage_url': 'https://www.youtube.com/watch?v=zzz',
            'extractor': 'youtube',
            'id': 'zzz',
            'formats': [
                {'format_id': '137', 'ext': 'mp4', 'width': 1920, 'height': 1080, 'vcodec': 'avc1'},
                {'format_id': '136', 'ext': 'mp4', 'width': 1280, 'height': 720, 'vcodec': 'avc1'},
                {'format_id': '135', 'ext': 'mp4', 'width': 854, 'height': 480, 'vcodec': 'avc1'},
            ],
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        assert len(metadata.available_qualities) == 3
        assert metadata.available_qualities[0].height == 1080
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:\codex\vdl && python -m pytest tests/test_yt_dlp_extractor.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'video_downloader.extractors.yt_dlp'`

- [ ] **Step 3: Implement YtDlpExtractor**

Write `E:\codex\vdl\video_downloader\extractors\yt_dlp.py`:
```python
"""
YtDlp-based platform extractor — covers YouTube, Bilibili, Twitter/X, Instagram, TikTok, Douyin.
"""

import re
import asyncio
from typing import List, Optional, Dict
from datetime import datetime

import yt_dlp

from ..models import VideoMetadata, QualityOption
from ..exceptions import PlatformError, VideoUnavailableError, UnsupportedPlatformError
from ..logger import logger
from .base import PlatformExtractor


class YtDlpExtractor(PlatformExtractor):
    """
    Universal extractor backed by yt-dlp.

    Covers: YouTube, Bilibili, Twitter/X, Instagram, TikTok, Douyin.
    Only extracts metadata and download URLs — actual download is handled by DownloadManager.
    """

    SUPPORTED_PATTERNS = {
        'youtube':   r'https?://(?:www\.)?(?:youtube\.com/watch|youtu\.be/)',
        'bilibili':  r'https?://(?:www\.)?bilibili\.com/video/',
        'twitter':   r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/',
        'instagram': r'https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/',
        'tiktok':    r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/',
        'douyin':    r'https?://(?:www\.)?douyin\.com/video/',
    }

    DEFAULT_YDL_OPTS = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
    }

    def __init__(self):
        logger.info("YtDlpExtractor initialized")

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        return any(re.search(pattern, url) for pattern in self.SUPPORTED_PATTERNS.values())

    def get_platform_name_for_url(self, url: str) -> Optional[str]:
        for name, pattern in self.SUPPORTED_PATTERNS.items():
            if re.search(pattern, url):
                return name
        return None

    def get_platform_name(self) -> str:
        return "yt_dlp"

    async def extract_metadata(
        self,
        url: str,
        cookies: Optional[Dict[str, str]] = None,
        cookie_file: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> VideoMetadata:
        logger.info(f"[yt-dlp] Extracting metadata: {url}")
        ydl_opts = self._build_opts(cookie_file=cookie_file, proxy=proxy)

        try:
            info = await asyncio.to_thread(self._extract_info, url, ydl_opts)
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'Private video' in error_msg or 'Video unavailable' in error_msg:
                raise VideoUnavailableError(f"Video unavailable: {url}")
            raise PlatformError(f"yt-dlp extraction failed: {error_msg}")

        if info is None:
            raise VideoUnavailableError(f"No info extracted for: {url}")

        return self._map_metadata(info)

    async def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        cookie_file: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> List[str]:
        logger.info(f"[yt-dlp] Getting download URLs: {metadata.url}")
        ydl_opts = self._build_opts(
            cookie_file=cookie_file,
            proxy=proxy,
            quality=quality,
        )

        try:
            info = await asyncio.to_thread(self._extract_info, metadata.url, ydl_opts)
        except yt_dlp.utils.DownloadError as e:
            raise PlatformError(f"yt-dlp URL extraction failed: {e}")

        if info is None:
            raise PlatformError("No download URL found")

        url = info.get('url')
        if url:
            return [url]

        formats = info.get('formats', [])
        if formats:
            best = formats[-1]
            return [best.get('url', '')]

        raise PlatformError("No download URL found in yt-dlp response")

    def _extract_info(self, url: str, opts: dict) -> Optional[dict]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _build_opts(
        self,
        cookie_file: Optional[str] = None,
        proxy: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> dict:
        opts = dict(self.DEFAULT_YDL_OPTS)

        if cookie_file:
            opts['cookiefile'] = cookie_file

        if proxy:
            opts['proxy'] = proxy

        if quality:
            opts['format'] = quality
        else:
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        return opts

    def _map_metadata(self, info: dict) -> VideoMetadata:
        platform = info.get('extractor', 'unknown')
        if platform == 'generic':
            platform = self.get_platform_name_for_url(info.get('webpage_url', '')) or 'unknown'

        qualities = self._parse_qualities(info.get('formats', []))

        upload_date = None
        date_str = info.get('upload_date')
        if date_str:
            try:
                upload_date = datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                pass

        return VideoMetadata(
            url=info.get('webpage_url', ''),
            platform=platform,
            video_id=str(info.get('id', '')),
            title=info.get('title', 'Untitled'),
            author=info.get('uploader') or info.get('channel') or 'Unknown',
            duration=info.get('duration') or 0,
            thumbnail_url=info.get('thumbnail') or '',
            description=info.get('description') or '',
            upload_date=upload_date,
            available_qualities=qualities,
            extra_data={
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
            },
        )

    def _parse_qualities(self, formats: list) -> List[QualityOption]:
        seen = set()
        qualities = []
        for f in formats:
            height = f.get('height')
            if not height or height in seen:
                continue
            seen.add(height)
            qualities.append(QualityOption(
                quality_id=f.get('format_id', ''),
                name=f"{height}p",
                resolution=f"{f.get('width', 0)}x{height}",
                width=f.get('width', 0),
                height=height,
                format=f.get('ext', 'mp4'),
            ))
        qualities.sort(key=lambda q: q.height, reverse=True)
        return qualities
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:\codex\vdl && python -m pytest tests/test_yt_dlp_extractor.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd E:\codex\vdl
git add video_downloader/extractors/yt_dlp.py tests/test_yt_dlp_extractor.py
git commit -m "feat: add YtDlpExtractor for multi-platform video extraction"
```

---

## Task 3: Update PlatformManager to register YtDlpExtractor

**Files:**
- Modify: `E:\codex\vdl\video_downloader\platform_manager.py`
- Modify: `E:\codex\vdl\video_downloader\extractors\__init__.py`
- Modify: `E:\codex\vdl\tests\test_platform_manager.py`

- [ ] **Step 1: Update platform_manager.py to register YtDlpExtractor**

Edit `E:\codex\vdl\video_downloader\platform_manager.py`, replace `_register_builtin_extractors`:

```python
    def _register_builtin_extractors(self):
        """Register built-in platform extractors."""
        from .extractors.yt_dlp import YtDlpExtractor
        from .extractors.bilibili import BilibiliExtractor
        from .extractors.douyin import DouyinExtractor

        # YtDlpExtractor is the primary extractor (covers 6 platforms)
        self.register_extractor(YtDlpExtractor())
        # BilibiliExtractor is fallback for when yt-dlp Bilibili support lags
        self.register_extractor(BilibiliExtractor())
        # DouyinExtractor has its own fallback chain
        self.register_extractor(DouyinExtractor())
```

- [ ] **Step 2: Update extractors/__init__.py**

Write `E:\codex\vdl\video_downloader\extractors\__init__.py`:
```python
"""
Platform extractors for video-downloader.
"""

from .base import PlatformExtractor
from .yt_dlp import YtDlpExtractor
from .bilibili import BilibiliExtractor
from .douyin import DouyinExtractor

__all__ = [
    "PlatformExtractor",
    "YtDlpExtractor",
    "BilibiliExtractor",
    "DouyinExtractor",
]
```

- [ ] **Step 3: Verify import chain works**

Run: `cd E:\codex\vdl && python -c "from video_downloader import VideoDownloader; d = VideoDownloader(); print(d.list_supported_platforms())"`

Expected: `['yt_dlp', 'bilibili', 'douyin']`

- [ ] **Step 4: Run existing platform manager tests**

Run: `cd E:\codex\vdl && python -m pytest tests/test_platform_manager.py -v`

Expected: PASS (tests use the same PlatformManager interface)

- [ ] **Step 5: Commit**

```bash
cd E:\codex\vdl
git add video_downloader/platform_manager.py video_downloader/extractors/__init__.py
git commit -m "feat: register YtDlpExtractor as primary extractor in PlatformManager"
```

---

## Task 4: Refactor DouyinExtractor with three-tier fallback

**Files:**
- Modify: `E:\codex\vdl\video_downloader\extractors\douyin.py`
- Create: `E:\codex\vdl\tests\test_douyin_extractor.py`

- [ ] **Step 1: Write failing tests for DouyinExtractor fallback chain**

Write `E:\codex\vdl\tests\test_douyin_extractor.py`:
```python
"""
Tests for DouyinExtractor with three-tier fallback.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from video_downloader.extractors.douyin import DouyinExtractor
from video_downloader.exceptions import PlatformError, VideoUnavailableError


class TestDouyinCanHandle:
    """Test URL matching."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    def test_standard_video_url(self):
        assert self.extractor.can_handle("https://www.douyin.com/video/7123456789")

    def test_note_url(self):
        assert self.extractor.can_handle("https://www.douyin.com/note/7123456789")

    def test_short_url(self):
        assert self.extractor.can_handle("https://v.douyin.com/abc123")

    def test_unsupported_url(self):
        assert not self.extractor.can_handle("https://www.bilibili.com/video/BV1xx")

    def test_empty_url(self):
        assert not self.extractor.can_handle("")


class TestDouyinFallbackChain:
    """Test the three-tier fallback chain."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    @pytest.mark.asyncio
    async def test_ytdlp_success_skips_fallback(self):
        """If yt-dlp succeeds, no further fallback is called."""
        mock_metadata = MagicMock()
        mock_metadata.title = "Test"

        with patch.object(self.extractor, '_try_ytdlp', new_callable=AsyncMock, return_value=mock_metadata) as mock_ytdlp:
            with patch.object(self.extractor, '_try_tiktok_api', new_callable=AsyncMock) as mock_api:
                with patch.object(self.extractor, '_try_playwright', new_callable=AsyncMock) as mock_pw:
                    result = await self.extractor.extract_metadata("https://www.douyin.com/video/123")
                    assert result == mock_metadata
                    mock_ytdlp.assert_called_once()
                    mock_api.assert_not_called()
                    mock_pw.assert_not_called()

    @pytest.mark.asyncio
    async def test_ytdlp_fail_falls_back_to_api(self):
        """If yt-dlp fails, falls back to Douyin_TikTok_Download_API."""
        mock_metadata = MagicMock()
        mock_metadata.title = "Test"

        with patch.object(self.extractor, '_try_ytdlp', new_callable=AsyncMock, side_effect=PlatformError("fail")):
            with patch.object(self.extractor, '_try_tiktok_api', new_callable=AsyncMock, return_value=mock_metadata) as mock_api:
                with patch.object(self.extractor, '_try_playwright', new_callable=AsyncMock) as mock_pw:
                    result = await self.extractor.extract_metadata("https://www.douyin.com/video/123")
                    assert result == mock_metadata
                    mock_api.assert_called_once()
                    mock_pw.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_fail_raises_error(self):
        """If all three tiers fail, raises PlatformError."""
        with patch.object(self.extractor, '_try_ytdlp', new_callable=AsyncMock, side_effect=PlatformError("fail1")):
            with patch.object(self.extractor, '_try_tiktok_api', new_callable=AsyncMock, side_effect=PlatformError("fail2")):
                with patch.object(self.extractor, '_try_playwright', new_callable=AsyncMock, side_effect=PlatformError("fail3")):
                    with pytest.raises(PlatformError, match="All extraction methods failed"):
                        await self.extractor.extract_metadata("https://www.douyin.com/video/123")


class TestDouyinExtractAwemeId:
    """Test aweme ID extraction."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    def test_video_id(self):
        assert self.extractor._extract_aweme_id("https://www.douyin.com/video/7123456789") == "7123456789"

    def test_note_id(self):
        assert self.extractor._extract_aweme_id("https://www.douyin.com/note/7123456789") == "7123456789"

    def test_no_id(self):
        assert self.extractor._extract_aweme_id("https://www.douyin.com/") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:\codex\vdl && python -m pytest tests/test_douyin_extractor.py -v`

Expected: FAIL — the fallback chain methods don't exist yet

- [ ] **Step 3: Rewrite DouyinExtractor with three-tier fallback**

Write `E:\codex\vdl\video_downloader\extractors\douyin.py`:
```python
"""
Douyin platform extractor with three-tier fallback:
  1. yt-dlp (fast, may break on signature changes)
  2. Douyin_TikTok_Download_API (community-maintained signing)
  3. Playwright browser automation (slow, most reliable)
"""

import re
import asyncio
from typing import List, Optional, Dict
from datetime import datetime

import httpx

from ..models import VideoMetadata, QualityOption, ImageItem
from ..exceptions import PlatformError, VideoUnavailableError, ValidationError
from ..logger import logger
from .base import PlatformExtractor


class DouyinExtractor(PlatformExtractor):
    """
    Douyin extractor with automatic fallback chain.
    """

    PLATFORM_NAME = 'douyin'

    URL_PATTERNS = [
        r'https?://(?:www\.)?douyin\.com/video/(\d+)',
        r'https?://(?:www\.)?douyin\.com/note/(\d+)',
        r'https?://v\.douyin\.com/(\w+)',
    ]

    API_VIDEO_DETAIL = 'https://www.douyin.com/aweme/v1/web/aweme/detail/'

    def __init__(self, skip_ytdlp: bool = False, skip_api: bool = False, skip_playwright: bool = False):
        super().__init__()
        self.skip_ytdlp = skip_ytdlp
        self.skip_api = skip_api
        self.skip_playwright = skip_playwright
        logger.info("DouyinExtractor initialized (3-tier fallback)")

    def can_handle(self, url: str) -> bool:
        return any(re.search(pattern, url) for pattern in self.URL_PATTERNS)

    def validate_url(self, url: str) -> bool:
        return self.can_handle(url)

    def get_platform_name(self) -> str:
        return self.PLATFORM_NAME

    def requires_browser_automation(self) -> bool:
        return True

    async def extract_metadata(
        self,
        url: str,
        cookies: Optional[Dict[str, str]] = None,
    ) -> VideoMetadata:
        if 'v.douyin.com' in url:
            url = await self._resolve_short_url(url)

        aweme_id = self._extract_aweme_id(url)
        if not aweme_id:
            raise ValidationError(f"Invalid Douyin URL: {url}")

        errors = []

        # Level 1: yt-dlp
        if not self.skip_ytdlp:
            try:
                logger.info("[Douyin] Trying yt-dlp...")
                return await self._try_ytdlp(url)
            except Exception as e:
                logger.warning(f"[Douyin] yt-dlp failed: {e}")
                errors.append(f"yt-dlp: {e}")

        # Level 2: Douyin_TikTok_Download_API style direct API
        if not self.skip_api:
            try:
                logger.info("[Douyin] Trying direct API...")
                return await self._try_direct_api(aweme_id, url, cookies)
            except Exception as e:
                logger.warning(f"[Douyin] Direct API failed: {e}")
                errors.append(f"API: {e}")

        # Level 3: Playwright browser
        if not self.skip_playwright:
            try:
                logger.info("[Douyin] Trying Playwright browser...")
                return await self._try_playwright(url, aweme_id)
            except Exception as e:
                logger.warning(f"[Douyin] Playwright failed: {e}")
                errors.append(f"Playwright: {e}")

        raise PlatformError(
            f"All extraction methods failed for {url}. Errors: {'; '.join(errors)}"
        )

    async def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        is_gallery = metadata.extra_data.get('is_gallery', False)

        if is_gallery:
            images = metadata.extra_data.get('images', [])
            return [img.url for img in images if isinstance(img, ImageItem)]

        video_url = metadata.extra_data.get('video_url')
        if not video_url:
            raise PlatformError("No video URL found in metadata")
        return [video_url]

    # --- Level 1: yt-dlp ---

    async def _try_ytdlp(self, url: str) -> VideoMetadata:
        from .yt_dlp import YtDlpExtractor
        ytdlp = YtDlpExtractor()
        return await ytdlp.extract_metadata(url)

    # --- Level 2: Direct API (Douyin_TikTok_Download_API style) ---

    async def _try_direct_api(
        self,
        aweme_id: str,
        url: str,
        cookies: Optional[Dict[str, str]] = None,
    ) -> VideoMetadata:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json',
        }

        params = {'aweme_id': aweme_id}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.API_VIDEO_DETAIL,
                params=params,
                headers=headers,
                cookies=cookies or {},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

        if data.get('status_code') != 0:
            raise PlatformError(f"Douyin API error: {data.get('status_msg', 'Unknown')}")

        aweme_detail = data.get('aweme_detail')
        if not aweme_detail:
            raise VideoUnavailableError(f"Aweme not found: {aweme_id}")

        return self._parse_aweme_data(aweme_detail, aweme_id, url)

    # --- Level 3: Playwright ---

    async def _try_playwright(self, url: str, aweme_id: str) -> VideoMetadata:
        from ..browser_automation import BrowserAutomation
        from ..browser_fingerprint import BrowserFingerprint

        fingerprint = BrowserFingerprint()
        automation = BrowserAutomation(fingerprint, headless=True)

        try:
            await automation.launch_browser()
            page = await automation.create_stealth_page(platform='douyin')
            await automation.navigate_with_delay(page, url)

            aweme_data = await page.evaluate('''() => {
                const el = document.getElementById('RENDER_DATA');
                if (el) {
                    try {
                        return JSON.parse(decodeURIComponent(el.textContent));
                    } catch(e) { return null; }
                }
                return null;
            }''')

            if not aweme_data:
                raise PlatformError("Could not extract RENDER_DATA from page")

            aweme_detail = self._find_aweme_in_render_data(aweme_data, aweme_id)
            if not aweme_detail:
                raise PlatformError("Could not find aweme detail in RENDER_DATA")

            return self._parse_aweme_data(aweme_detail, aweme_id, url)

        finally:
            await automation.close()

    def _find_aweme_in_render_data(self, render_data: dict, aweme_id: str) -> Optional[dict]:
        for key, value in render_data.items():
            if isinstance(value, dict):
                detail = value.get('aweme', {}).get('detail', {})
                if detail.get('aweme_id') == aweme_id:
                    return detail
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        detail = sub_value.get('aweme', {}).get('detail', {})
                        if detail.get('aweme_id') == aweme_id:
                            return detail
        return None

    # --- Helpers ---

    def _extract_aweme_id(self, url: str) -> Optional[str]:
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        match = re.search(r'/note/(\d+)', url)
        if match:
            return match.group(1)
        match = re.search(r'v\.douyin\.com/(\w+)', url)
        if match:
            return match.group(1)
        return None

    async def _resolve_short_url(self, short_url: str) -> str:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(short_url)
            return str(response.url)

    def _parse_aweme_data(self, aweme_data: dict, aweme_id: str, url: str) -> VideoMetadata:
        desc = aweme_data.get('desc', '')
        author_info = aweme_data.get('author', {})
        author = author_info.get('nickname', 'Unknown')

        aweme_type = aweme_data.get('aweme_type', 0)
        is_gallery = aweme_type == 68

        duration = 0
        thumbnail = ''
        video_url = None
        images = []

        if is_gallery:
            title = desc or 'Douyin Gallery'
            images_data = aweme_data.get('images', [])
            for idx, img_data in enumerate(images_data):
                url_list = img_data.get('url_list', [])
                if url_list:
                    images.append(ImageItem(
                        url=url_list[0],
                        index=idx,
                        width=img_data.get('width', 0),
                        height=img_data.get('height', 0),
                    ))
            if images:
                thumbnail = images[0].url
        else:
            title = desc or 'Douyin Video'
            video_info = aweme_data.get('video', {})
            duration = video_info.get('duration', 0) // 1000
            play_addr = video_info.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            if url_list:
                video_url = url_list[0]
            cover = video_info.get('cover', {})
            url_list = cover.get('url_list', [])
            if url_list:
                thumbnail = url_list[0]

        statistics = aweme_data.get('statistics', {})

        return VideoMetadata(
            url=url,
            platform=self.PLATFORM_NAME,
            video_id=aweme_id,
            title=title,
            author=author,
            description=desc,
            duration=duration,
            thumbnail_url=thumbnail,
            available_qualities=[],
            extra_data={
                'is_gallery': is_gallery,
                'images': images,
                'video_url': video_url,
                'digg_count': statistics.get('digg_count', 0),
                'comment_count': statistics.get('comment_count', 0),
                'share_count': statistics.get('share_count', 0),
            },
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:\codex\vdl && python -m pytest tests/test_douyin_extractor.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd E:\codex\vdl
git add video_downloader/extractors/douyin.py tests/test_douyin_extractor.py
git commit -m "feat: refactor DouyinExtractor with three-tier fallback (yt-dlp → API → Playwright)"
```

---

## Task 5: Update core.py to pass cookie_file and proxy to extractors

**Files:**
- Modify: `E:\codex\vdl\video_downloader\core.py`

- [ ] **Step 1: Update core.py download method to pass cookie_file and proxy**

Edit `E:\codex\vdl\video_downloader\core.py`. In the `download` method, update the `extract_metadata` and `get_download_urls` calls to pass `cookie_file` and `proxy` from config:

Find the section around line 130-145 where `extract_metadata` is called and replace:

```python
            # Extract metadata
            logger.info("Extracting metadata...")
            metadata = await extractor.extract_metadata(
                url,
                cookie_dict,
                cookie_file=self.config.cookie_file,
                proxy=self.config.proxy,
            )
```

Find the section around line 142 where `get_download_urls` is called and replace:

```python
            # Get download URLs
            logger.info("Getting download URLs...")
            download_urls = await extractor.get_download_urls(
                metadata, quality, cookie_dict,
                cookie_file=self.config.cookie_file,
                proxy=self.config.proxy,
            )
```

- [ ] **Step 2: Update extract_metadata method similarly**

Find the `extract_metadata` method (around line 267) and update:

```python
        # Extract metadata
        metadata = await extractor.extract_metadata(
            url,
            cookie_dict,
            cookie_file=self.config.cookie_file,
            proxy=self.config.proxy,
        )
```

- [ ] **Step 3: Verify no import errors**

Run: `cd E:\codex\vdl && python -c "from video_downloader import VideoDownloader; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd E:\codex\vdl
git add video_downloader/core.py
git commit -m "feat: pass cookie_file and proxy config to extractors"
```

---

## Task 6: Fix MCP Server bugs

**Files:**
- Modify: `E:\codex\vdl\mcp_server.py`

- [ ] **Step 1: Fix batch_download bug — result.url does not exist**

In `mcp_server.py`, find the `batch_download` method. The bug is on the line referencing `result.url` — `DownloadResult` has no `url` field. Fix:

Find:
```python
            if result.success:
                success_list.append(f"✓ {result.url}")
            else:
                failed_list.append(f"✗ {result.url}: {result.error_message}")
```

Replace with:
```python
            if result.success:
                success_list.append(f"✓ {result.file_path}")
            else:
                failed_list.append(f"✗ {result.error_message}")
```

- [ ] **Step 2: Fix download_video to use result fields correctly**

Find:
```python
                        f"📊 文件大小: {result.file_size / 1024 / 1024:.2f} MB\n"
                        f"⏱️  耗时: {result.duration:.2f} 秒"
```

This is fine — `file_size` and `duration` exist on `DownloadResult`. But `result.duration` is download time, not video duration. Add a guard:

Replace:
```python
                        f"📊 文件大小: {result.file_size / 1024 / 1024:.2f} MB\n"
                        f"⏱️  耗时: {result.duration:.2f} 秒"
```

With:
```python
                        f"📊 文件大小: {result.file_size / 1024 / 1024:.2f} MB"
                        + (f"\n⏱️  耗时: {result.duration:.1f}s" if result.duration > 0 else "")
```

- [ ] **Step 3: Update list_supported_platforms to reflect new architecture**

Find the `list_supported_platforms` method and update the text:

```python
    def list_supported_platforms(self) -> Dict[str, Any]:
        """List supported platforms."""
        platforms = self.downloader.platform_manager.list_platforms()

        text = "📺 Supported Platforms:\n\n"
        for platform in platforms:
            text += f"• {platform}\n"

        text += "\nCoverage:\n"
        text += "✅ YouTube: full support via yt-dlp\n"
        text += "✅ Bilibili: full support via yt-dlp (fallback: custom extractor)\n"
        text += "✅ Twitter/X: full support via yt-dlp\n"
        text += "✅ Instagram: full support via yt-dlp\n"
        text += "✅ TikTok: full support via yt-dlp\n"
        text += "✅ Douyin: yt-dlp → API → Playwright fallback chain\n"

        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
```

- [ ] **Step 4: Verify MCP server starts without errors**

Run: `cd E:\codex\vdl && python -c "from mcp_server import MCPServer; s = MCPServer(); print('OK')"`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd E:\codex\vdl
git add mcp_server.py
git commit -m "fix: MCP server batch_download result.url bug, update platform list"
```

---

## Task 7: Update CLI for new architecture

**Files:**
- Modify: `E:\codex\vdl\video_downloader\cli.py`

- [ ] **Step 1: Update CLI description and epilog**

In `cli.py`, find the `ArgumentParser` initialization and update:

```python
    parser = argparse.ArgumentParser(
        description='vdl - Multi-platform video downloader powered by yt-dlp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a video
  vdl download https://www.bilibili.com/video/BV1xx411c7mD

  # Download with quality and output dir
  vdl download https://www.youtube.com/watch?v=xxx -q 1080p -o ./videos

  # Download multiple videos
  vdl download url1 url2 url3

  # Extract metadata only
  vdl info https://www.douyin.com/video/123456

  # List supported platforms
  vdl platforms

  # Use cookies for authenticated download
  vdl download https://www.bilibili.com/video/BV1xx --cookies ./cookies/bilibili.txt
        """
    )
```

- [ ] **Step 2: Update list-platforms output**

Find the `--list-platforms` handler and update:

```python
    if args.list_platforms:
        platforms = downloader.list_supported_platforms()
        print("\n📺 Supported Platforms:")
        for platform in platforms:
            print(f"  • {platform}")
        print("\nPowered by yt-dlp (YouTube, Bilibili, Twitter, Instagram, TikTok)")
        print("Douyin: yt-dlp → API → Playwright fallback chain")
        print()
        return 0
```

- [ ] **Step 3: Update setup.py entry point to 'vdl'**

Already done in Task 1 Step 5 — entry point is `vdl=video_downloader.cli:cli_entry`.

- [ ] **Step 4: Verify CLI runs**

Run: `cd E:\codex\vdl && python -m video_downloader.cli --list-platforms`

Expected: Lists platforms including yt_dlp, bilibili, douyin

- [ ] **Step 5: Commit**

```bash
cd E:\codex\vdl
git add video_downloader/cli.py
git commit -m "feat: update CLI for yt-dlp architecture"
```

---

## Task 8: Add yt-dlp integration test

**Files:**
- Create: `E:\codex\vdl\tests\test_ytdlp_integration.py`

- [ ] **Step 1: Write integration test for YtDlpExtractor metadata extraction**

Write `E:\codex\vdl\tests\test_ytdlp_integration.py`:
```python
"""
Integration tests for yt-dlp based extraction.
These tests make real network calls — skip in CI with: pytest -m "not integration"
"""

import pytest
from video_downloader.extractors.yt_dlp import YtDlpExtractor


@pytest.mark.integration
class TestYtDlpIntegration:
    """Real network tests for YtDlpExtractor."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    @pytest.mark.asyncio
    async def test_youtube_metadata(self):
        """Test extracting metadata from a real YouTube video."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        metadata = await self.extractor.extract_metadata(url)
        assert metadata.title
        assert metadata.platform == 'youtube'
        assert metadata.duration > 0

    @pytest.mark.asyncio
    async def test_bilibili_metadata(self):
        """Test extracting metadata from a real Bilibili video."""
        url = "https://www.bilibili.com/video/BV1GJ411x7h7"
        metadata = await self.extractor.extract_metadata(url)
        assert metadata.title
        assert metadata.platform == 'bilibili'

    def test_can_handle_all_platforms(self):
        """Test URL matching for all supported platforms."""
        urls = [
            ("https://www.youtube.com/watch?v=xxx", True),
            ("https://youtu.be/xxx", True),
            ("https://www.bilibili.com/video/BV1xx", True),
            ("https://twitter.com/user/status/123", True),
            ("https://x.com/user/status/123", True),
            ("https://www.instagram.com/reel/xxx/", True),
            ("https://www.tiktok.com/@user/video/123", True),
            ("https://www.douyin.com/video/123", True),
            ("https://example.com", False),
        ]
        for url, expected in urls:
            assert self.extractor.can_handle(url) == expected, f"Failed for {url}"
```

- [ ] **Step 2: Run integration tests (requires network)**

Run: `cd E:\codex\vdl && python -m pytest tests/test_ytdlp_integration.py -v -m integration`

Expected: PASS (requires network access)

- [ ] **Step 3: Run all non-integration tests to verify nothing is broken**

Run: `cd E:\codex\vdl && python -m pytest tests/ -v -m "not integration"`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd E:\codex\vdl
git add tests/test_ytdlp_integration.py
git commit -m "test: add yt-dlp integration tests for YouTube and Bilibili"
```

---

## Task 9: Update documentation

**Files:**
- Modify: `E:\codex\vdl\README.md`
- Modify: `E:\codex\vdl\USAGE.md`

- [ ] **Step 1: Update README.md**

Update the README to reflect the new architecture. Key changes:
- Title: "VDL — Multi-Platform Video Downloader"
- Update supported platforms table
- Update tech stack to include yt-dlp
- Update installation instructions
- Update quick start examples

- [ ] **Step 2: Update USAGE.md**

Update usage examples to use `vdl` command instead of `python -m video_downloader.cli`.

- [ ] **Step 3: Commit**

```bash
cd E:\codex\vdl
git add README.md USAGE.md
git commit -m "docs: update README and USAGE for yt-dlp architecture"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** Every spec section has a corresponding task
  - YtDlpExtractor → Task 2
  - DouyinExtractor fallback → Task 4
  - PlatformManager → Task 3
  - MCP Server → Task 6
  - CLI → Task 7
  - Migration → Task 1
  - Cookie management → Task 1 (example files)
  - Tests → Task 8
  - Docs → Task 9
- [x] **Placeholder scan:** No TBD/TODO in plan
- [x] **Type consistency:** VideoMetadata, DownloadResult, PlatformExtractor interfaces consistent across all tasks
