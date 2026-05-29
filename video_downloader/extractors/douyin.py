"""
Douyin platform extractor with three-tier fallback.

Fallback chain:
  1. yt-dlp (fast, may break on signature changes)
  2. Direct API (community-maintained signing)
  3. Playwright browser automation (slow, most reliable)
"""

import re
import json
import asyncio
from typing import List, Optional, Dict
from datetime import datetime

import httpx

from ..models import (
    VideoMetadata, QualityOption, ContentType, ImageItem,
    ExtractionContext,
)
from ..exceptions import PlatformError, VideoUnavailableError, ValidationError
from ..logger import logger
from .base import PlatformExtractor


class DouyinExtractor(PlatformExtractor):
    """
    Douyin (抖音) video and image gallery extractor with three-tier fallback.

    Supports:
    - Regular videos (aweme_type != 68)
    - Image galleries / notes (aweme_type == 68)
    - Short URL resolution (v.douyin.com)
    - Configurable skip flags per fallback level
    """

    PLATFORM_NAME = "douyin"

    # URL patterns — each group captures the relevant ID segment
    URL_PATTERNS = [
        r"https?://(?:www\.)?douyin\.com/video/(\d+)",
        r"https?://(?:www\.)?douyin\.com/note/(\d+)",
        r"https?://v\.douyin\.com/(\w+)",
    ]

    # API endpoint (Level 2)
    API_VIDEO_DETAIL = "https://www.douyin.com/aweme/v1/web/aweme/detail/"

    # Timeout per fallback level (seconds)
    TIMEOUT_YTDLP = 30.0
    TIMEOUT_API = 15.0
    TIMEOUT_PLAYWRIGHT = 60.0

    def __init__(self):
        super().__init__()
        logger.info("DouyinExtractor initialized")

    # ------------------------------------------------------------------
    # PlatformExtractor ABC
    # ------------------------------------------------------------------

    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the URL."""
        if not url:
            return False
        return any(re.search(p, url) for p in self.URL_PATTERNS)

    def validate_url(self, url: str) -> bool:
        """Validate Douyin URL format."""
        if not self.can_handle(url):
            return False
        aweme_id = self._extract_aweme_id(url)
        return aweme_id is not None

    def requires_browser_automation(self) -> bool:
        return True

    def get_platform_name(self) -> str:
        return self.PLATFORM_NAME

    async def extract_metadata(
        self,
        url: str,
        context: ExtractionContext,
        *,
        skip_ytdlp: bool = False,
        skip_api: bool = False,
        skip_playwright: bool = False,
        cookie_file: Optional[str] = None,
        proxy: Optional[str] = None,
        **kwargs,
    ) -> VideoMetadata:
        """
        Extract video/gallery metadata from Douyin using three-tier fallback.

        Args:
            url: Video/gallery/short URL
            context: Extraction context (cookies, fingerprint, browser automation)
            skip_ytdlp: Skip Level 1 (yt-dlp)
            skip_api: Skip Level 2 (direct API)
            skip_playwright: Skip Level 3 (Playwright)

        Returns:
            VideoMetadata

        Raises:
            PlatformError: If all attempted levels fail
            ValidationError: If URL is invalid
        """
        logger.info(f"[douyin] Extracting metadata: {url}")

        errors: List[str] = []

        # --- Level 1: yt-dlp ---
        if not skip_ytdlp:
            try:
                return await asyncio.wait_for(
                    self._extract_via_ytdlp(
                        url, context,
                        cookie_file=cookie_file, proxy=proxy,
                    ),
                    timeout=self.TIMEOUT_YTDLP,
                )
            except Exception as e:
                logger.warning(f"[douyin] Level 1 (yt-dlp) failed: {e}")
                errors.append(f"yt-dlp: {e}")
        else:
            logger.debug("[douyin] Level 1 (yt-dlp) skipped")

        # --- Level 2: Direct API ---
        if not skip_api:
            try:
                return await asyncio.wait_for(
                    self._extract_via_api(url, context),
                    timeout=self.TIMEOUT_API,
                )
            except Exception as e:
                logger.warning(f"[douyin] Level 2 (API) failed: {e}")
                errors.append(f"API: {e}")
        else:
            logger.debug("[douyin] Level 2 (API) skipped")

        # --- Level 3: Playwright ---
        if not skip_playwright:
            try:
                return await asyncio.wait_for(
                    self._extract_via_playwright(url, context),
                    timeout=self.TIMEOUT_PLAYWRIGHT,
                )
            except Exception as e:
                logger.warning(f"[douyin] Level 3 (Playwright) failed: {e}")
                errors.append(f"Playwright: {e}")
        else:
            logger.debug("[douyin] Level 3 (Playwright) skipped")

        raise PlatformError(
            f"All Douyin extraction levels failed: {'; '.join(errors)}"
        )

    async def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """
        Get download URLs for video or images.

        Args:
            metadata: Video metadata
            quality: Desired quality (ignored for Douyin)

        Returns:
            List of download URLs
        """
        logger.info(f"[douyin] Getting download URLs for: {metadata.url}")

        if metadata.content_type == ContentType.GALLERY and metadata.gallery_images:
            urls = [img.url for img in metadata.gallery_images]
            logger.info(f"[douyin] Found {len(urls)} image URLs")
            return urls

        # For video, re-extract via yt-dlp to get a fresh download URL
        # (Douyin play_addr URLs are ephemeral)
        from .yt_dlp import YtDlpExtractor
        ytdlp = YtDlpExtractor()
        try:
            fresh_urls = await ytdlp.get_download_urls(metadata, quality)
            if fresh_urls:
                return fresh_urls
        except Exception:
            pass
        logger.warning("[douyin] Could not get video download URL")
        return []

    # ------------------------------------------------------------------
    # Level 1 — yt-dlp
    # ------------------------------------------------------------------

    async def _extract_via_ytdlp(
        self, url: str, context: ExtractionContext,
        *, cookie_file: Optional[str] = None, proxy: Optional[str] = None,
    ) -> VideoMetadata:
        """Level 1: Use YtDlpExtractor for metadata extraction."""
        from .yt_dlp import YtDlpExtractor

        extractor = YtDlpExtractor()
        if not extractor.can_handle(url):
            raise PlatformError(f"yt-dlp cannot handle Douyin URL: {url}")

        return await extractor.extract_metadata(
            url, context, cookie_file=cookie_file, proxy=proxy,
        )

    # ------------------------------------------------------------------
    # Level 2 — Direct API
    # ------------------------------------------------------------------

    async def _extract_via_api(
        self, url: str, context: ExtractionContext
    ) -> VideoMetadata:
        """Level 2: Use Douyin's internal API to fetch aweme detail."""
        resolved_url = await self._resolve_short_url(url)
        aweme_id = self._extract_aweme_id(resolved_url)
        if not aweme_id:
            raise ValidationError(f"Cannot extract aweme ID from: {resolved_url}")

        headers = {
            "User-Agent": context.fingerprint.user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.API_VIDEO_DETAIL,
                    params={"aweme_id": aweme_id},
                    headers=headers,
                    timeout=self.TIMEOUT_API,
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise PlatformError(f"Douyin API HTTP error: {e}")

        try:
            data = response.json()
        except Exception as e:
            raise PlatformError(f"Douyin API invalid JSON: {e}")

        if data.get("status_code") != 0:
            error_msg = data.get("status_msg", "Unknown error")
            raise PlatformError(f"Douyin API error: {error_msg}")

        aweme_detail = data.get("aweme_detail")
        if not aweme_detail:
            raise VideoUnavailableError(f"Aweme not found: {aweme_id}")

        return self._parse_aweme_data(aweme_detail, aweme_id)

    # ------------------------------------------------------------------
    # Level 3 — Playwright browser automation
    # ------------------------------------------------------------------

    async def _extract_via_playwright(
        self, url: str, context: ExtractionContext
    ) -> VideoMetadata:
        """Level 3: Use Playwright to load the page and extract RENDER_DATA."""
        resolved_url = await self._resolve_short_url(url)
        aweme_id = self._extract_aweme_id(resolved_url)
        if not aweme_id:
            raise ValidationError(f"Cannot extract aweme ID from: {resolved_url}")

        # Get BrowserAutomation from context or create a new one
        browser_automation = getattr(context, "browser_automation", None)
        own_browser = False

        if browser_automation is None:
            from ..browser_fingerprint import BrowserFingerprint
            from ..browser_automation import BrowserAutomation

            fingerprint = BrowserFingerprint()
            browser_automation = BrowserAutomation(fingerprint, headless=True)
            own_browser = True

        try:
            page = await browser_automation.create_stealth_page(platform="douyin")
            await browser_automation.navigate_with_delay(page, resolved_url)

            # Extract RENDER_DATA from the DOM
            render_data_raw = await page.evaluate(
                "document.getElementById('RENDER_DATA')?.textContent"
            )

            if not render_data_raw:
                raise PlatformError("RENDER_DATA not found in page DOM")

            from urllib.parse import unquote
            render_data = json.loads(unquote(render_data_raw))

            # Find the aweme detail by ID in the nested RENDER_DATA structure
            aweme_detail = None
            for _key, value in render_data.items():
                if isinstance(value, dict):
                    detail = (
                        value.get("aweme", {}).get("detail")
                        or value.get("awemeDetail", {})
                    )
                    if detail and str(detail.get("aweme_id", "")) == str(aweme_id):
                        aweme_detail = detail
                        break
                    # Deep search one more level
                    for _sub_key, sub_value in value.items():
                        if isinstance(sub_value, dict):
                            detail = sub_value.get("aweme", {}).get(
                                "detail"
                            ) or sub_value.get("awemeDetail", {})
                            if detail and str(detail.get("aweme_id", "")) == str(
                                aweme_id
                            ):
                                aweme_detail = detail
                                break
                    if aweme_detail:
                        break

            if not aweme_detail:
                raise VideoUnavailableError(
                    f"Aweme {aweme_id} not found in RENDER_DATA"
                )

            return self._parse_aweme_data(aweme_detail, aweme_id)

        finally:
            if own_browser:
                await browser_automation.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_short_url(self, url: str) -> str:
        """Resolve v.douyin.com short URL to full URL via redirect following."""
        if "v.douyin.com" not in url:
            return url

        logger.debug(f"[douyin] Resolving short URL: {url}")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=10.0)
            resolved = str(response.url)
            logger.debug(f"[douyin] Resolved to: {resolved}")
            return resolved

    def _extract_aweme_id(self, url: str) -> Optional[str]:
        """Extract aweme ID from a full Douyin URL.

        For v.douyin.com short URLs the returned value is the short path,
        not the aweme numeric ID — the caller must resolve the short URL first.
        """
        match = re.search(r"/video/(\d+)", url)
        if match:
            return match.group(1)

        match = re.search(r"/note/(\d+)", url)
        if match:
            return match.group(1)

        match = re.search(r"v\.douyin\.com/(\w+)", url)
        if match:
            return match.group(1)

        return None

    def _parse_aweme_data(self, aweme_data: Dict, aweme_id: str) -> VideoMetadata:
        """Parse Douyin aweme API response into VideoMetadata."""
        desc = aweme_data.get("desc", "")
        author_info = aweme_data.get("author", {})
        author = author_info.get("nickname", "Unknown")

        aweme_type = aweme_data.get("aweme_type", 0)
        is_gallery = aweme_type == 68

        duration = 0
        thumbnail = ""
        gallery_images: Optional[List[ImageItem]] = None

        if is_gallery:
            title = desc or "Douyin Gallery"
            images_data = aweme_data.get("images") or []
            gallery_images = []
            for idx, img_data in enumerate(images_data):
                url_list = img_data.get("url_list") or []
                if url_list:
                    gallery_images.append(
                        ImageItem(
                            url=url_list[0],
                            index=idx,
                            width=img_data.get("width", 0),
                            height=img_data.get("height", 0),
                        )
                    )
            if gallery_images:
                thumbnail = gallery_images[0].url
        else:
            title = desc or "Douyin Video"
            video_info = aweme_data.get("video", {})
            duration = video_info.get("duration", 0) // 1000  # ms -> seconds

            cover = video_info.get("cover", {})
            cover_urls = cover.get("url_list") or []
            if cover_urls:
                thumbnail = cover_urls[0]

        return VideoMetadata(
            url=f"https://www.douyin.com/video/{aweme_id}"
            if not is_gallery
            else f"https://www.douyin.com/note/{aweme_id}",
            platform=self.PLATFORM_NAME,
            title=title,
            author=author,
            duration=duration,
            thumbnail_url=thumbnail,
            description=desc,
            upload_date=datetime.now(),
            quality_options=[],  # Douyin doesn't expose quality options
            content_type=ContentType.GALLERY if is_gallery else ContentType.VIDEO,
            gallery_images=gallery_images,
        )
