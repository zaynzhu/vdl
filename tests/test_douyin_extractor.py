"""
Tests for DouyinExtractor with three-tier fallback.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from video_downloader.extractors.douyin import DouyinExtractor
from video_downloader.models import (
    VideoMetadata, QualityOption, ContentType, ImageItem,
    ExtractionContext, Fingerprint,
)
from video_downloader.exceptions import PlatformError, VideoUnavailableError


@pytest.fixture
def extractor():
    """DouyinExtractor instance."""
    return DouyinExtractor()


@pytest.fixture
def context():
    """Minimal ExtractionContext for testing."""
    return ExtractionContext(
        cookies=[],
        fingerprint=Fingerprint(
            user_agent="test-agent",
            platform="Win32",
            screen_width=1920,
            screen_height=1080,
            color_depth=24,
            language="zh-CN",
            timezone="Asia/Shanghai",
            headers={},
        ),
    )


def _make_context_with_browser(browser_automation):
    """Create an ExtractionContext with a mock browser automation."""
    return ExtractionContext(
        cookies=[],
        fingerprint=Fingerprint(
            user_agent="test-agent",
            platform="Win32",
            screen_width=1920,
            screen_height=1080,
            color_depth=24,
            language="zh-CN",
            timezone="Asia/Shanghai",
            headers={},
        ),
        browser_automation=browser_automation,
    )


# ---------------------------------------------------------------------------
# TestDouyinCanHandle — URL matching
# ---------------------------------------------------------------------------

class TestDouyinCanHandle:
    """Test URL matching for video/note/short URLs."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    def test_video_url(self):
        assert self.extractor.can_handle("https://www.douyin.com/video/7123456789012345678")

    def test_note_url(self):
        assert self.extractor.can_handle("https://www.douyin.com/note/7123456789012345678")

    def test_short_url(self):
        assert self.extractor.can_handle("https://v.douyin.com/iABcDeFg/")

    def test_no_www_video_url(self):
        assert self.extractor.can_handle("https://douyin.com/video/7123456789012345678")

    def test_http_video_url(self):
        assert self.extractor.can_handle("http://www.douyin.com/video/7123456789012345678")

    def test_unsupported_url(self):
        assert not self.extractor.can_handle("https://www.bilibili.com/video/BV1xx")

    def test_empty_url(self):
        assert not self.extractor.can_handle("")

    def test_similar_domain_not_matched(self):
        assert not self.extractor.can_handle("https://www.notdouyin.com/video/123")


# ---------------------------------------------------------------------------
# TestDouyinExtractAwemeId — ID extraction from various URL formats
# ---------------------------------------------------------------------------

class TestDouyinExtractAwemeId:
    """Test aweme ID extraction from various URL formats."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    def test_video_url_id(self):
        url = "https://www.douyin.com/video/7123456789012345678"
        assert self.extractor._extract_aweme_id(url) == "7123456789012345678"

    def test_note_url_id(self):
        url = "https://www.douyin.com/note/7123456789012345678"
        assert self.extractor._extract_aweme_id(url) == "7123456789012345678"

    def test_short_url_id(self):
        """Short URL returns the short_id (not the aweme ID)."""
        url = "https://v.douyin.com/iABcDeFg/"
        assert self.extractor._extract_aweme_id(url) == "iABcDeFg"

    def test_no_match(self):
        assert self.extractor._extract_aweme_id("https://www.douyin.com/user/123") is None

    def test_empty_string(self):
        assert self.extractor._extract_aweme_id("") is None

    def test_video_url_with_query_params(self):
        url = "https://www.douyin.com/video/7123456789012345678?previous_page=main"
        assert self.extractor._extract_aweme_id(url) == "7123456789012345678"


# ---------------------------------------------------------------------------
# TestDouyinFallbackChain — mock each level, verify fallback behavior
# ---------------------------------------------------------------------------

class TestDouyinFallbackChain:
    """Test the three-tier fallback chain."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    def _mock_metadata(self):
        """Return a valid VideoMetadata for mocking."""
        return VideoMetadata(
            url="https://www.douyin.com/video/123",
            platform="douyin",
            title="Test Video",
            author="Test Author",
            duration=60,
            thumbnail_url="https://example.com/thumb.jpg",
            description="Test desc",
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO,
        )

    @pytest.mark.asyncio
    async def test_ytdlp_success_skips_rest(self, extractor, context):
        """When yt-dlp succeeds, API and Playwright are never called."""
        expected = self._mock_metadata()

        with patch.object(extractor, '_extract_via_ytdlp', new_callable=AsyncMock, return_value=expected) as mock_ytdlp, \
             patch.object(extractor, '_extract_via_api', new_callable=AsyncMock) as mock_api, \
             patch.object(extractor, '_extract_via_playwright', new_callable=AsyncMock) as mock_pw:

            result = await extractor.extract_metadata("https://www.douyin.com/video/123", context)

            assert result == expected
            mock_ytdlp.assert_called_once()
            mock_api.assert_not_called()
            mock_pw.assert_not_called()

    @pytest.mark.asyncio
    async def test_ytdlp_fail_tries_api(self, extractor, context):
        """When yt-dlp fails, falls back to API."""
        expected = self._mock_metadata()

        with patch.object(extractor, '_extract_via_ytdlp', new_callable=AsyncMock, side_effect=PlatformError("ytdlp fail")), \
             patch.object(extractor, '_extract_via_api', new_callable=AsyncMock, return_value=expected) as mock_api, \
             patch.object(extractor, '_extract_via_playwright', new_callable=AsyncMock) as mock_pw:

            result = await extractor.extract_metadata("https://www.douyin.com/video/123", context)

            assert result == expected
            mock_api.assert_called_once()
            mock_pw.assert_not_called()

    @pytest.mark.asyncio
    async def test_ytdlp_and_api_fail_tries_playwright(self, extractor, context):
        """When yt-dlp and API both fail, falls back to Playwright."""
        expected = self._mock_metadata()

        with patch.object(extractor, '_extract_via_ytdlp', new_callable=AsyncMock, side_effect=PlatformError("ytdlp fail")), \
             patch.object(extractor, '_extract_via_api', new_callable=AsyncMock, side_effect=PlatformError("api fail")), \
             patch.object(extractor, '_extract_via_playwright', new_callable=AsyncMock, return_value=expected) as mock_pw:

            result = await extractor.extract_metadata("https://www.douyin.com/video/123", context)

            assert result == expected
            mock_pw.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_fail_raises_platform_error(self, extractor, context):
        """When all three levels fail, raises PlatformError."""

        with patch.object(extractor, '_extract_via_ytdlp', new_callable=AsyncMock, side_effect=PlatformError("ytdlp fail")), \
             patch.object(extractor, '_extract_via_api', new_callable=AsyncMock, side_effect=PlatformError("api fail")), \
             patch.object(extractor, '_extract_via_playwright', new_callable=AsyncMock, side_effect=PlatformError("pw fail")):

            with pytest.raises(PlatformError):
                await extractor.extract_metadata("https://www.douyin.com/video/123", context)

    @pytest.mark.asyncio
    async def test_skip_ytdlp_flag(self, extractor, context):
        """When skip_ytdlp=True, yt-dlp is skipped."""
        expected = self._mock_metadata()

        with patch.object(extractor, '_extract_via_ytdlp', new_callable=AsyncMock) as mock_ytdlp, \
             patch.object(extractor, '_extract_via_api', new_callable=AsyncMock, return_value=expected) as mock_api:

            result = await extractor.extract_metadata(
                "https://www.douyin.com/video/123", context, skip_ytdlp=True
            )

            assert result == expected
            mock_ytdlp.assert_not_called()
            mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_api_flag(self, extractor, context):
        """When skip_api=True, API is skipped."""
        expected = self._mock_metadata()

        with patch.object(extractor, '_extract_via_ytdlp', new_callable=AsyncMock, side_effect=PlatformError("fail")), \
             patch.object(extractor, '_extract_via_api', new_callable=AsyncMock) as mock_api, \
             patch.object(extractor, '_extract_via_playwright', new_callable=AsyncMock, return_value=expected) as mock_pw:

            result = await extractor.extract_metadata(
                "https://www.douyin.com/video/123", context, skip_api=True
            )

            mock_api.assert_not_called()
            mock_pw.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_all_but_playwright(self, extractor, context):
        """When skip_ytdlp=True and skip_api=True, goes directly to Playwright."""
        expected = self._mock_metadata()

        with patch.object(extractor, '_extract_via_ytdlp', new_callable=AsyncMock) as mock_ytdlp, \
             patch.object(extractor, '_extract_via_api', new_callable=AsyncMock) as mock_api, \
             patch.object(extractor, '_extract_via_playwright', new_callable=AsyncMock, return_value=expected) as mock_pw:

            result = await extractor.extract_metadata(
                "https://www.douyin.com/video/123", context, skip_ytdlp=True, skip_api=True
            )

            mock_ytdlp.assert_not_called()
            mock_api.assert_not_called()
            mock_pw.assert_called_once()


# ---------------------------------------------------------------------------
# TestDouyinAwemeDataParsing — metadata mapping
# ---------------------------------------------------------------------------

class TestDouyinAwemeDataParsing:
    """Test parsing aweme API response into VideoMetadata."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    def test_parse_video_aweme(self):
        """Parse a video-type aweme (aweme_type != 68)."""
        data = {
            "desc": "Test video description",
            "author": {"nickname": "TestUser"},
            "aweme_type": 0,
            "video": {
                "duration": 15000,
                "play_addr": {"url_list": ["https://example.com/video.mp4"]},
                "cover": {"url_list": ["https://example.com/cover.jpg"]},
            },
            "statistics": {
                "digg_count": 100,
                "comment_count": 50,
                "share_count": 10,
            },
        }

        metadata = self.extractor._parse_aweme_data(data, "123456")

        assert metadata.title == "Test video description"
        assert metadata.author == "TestUser"
        assert metadata.platform == "douyin"
        assert metadata.duration == 15  # 15000ms -> 15s
        assert metadata.thumbnail_url == "https://example.com/cover.jpg"
        assert metadata.content_type == ContentType.VIDEO
        assert metadata.gallery_images is None

    def test_parse_gallery_aweme(self):
        """Parse a gallery-type aweme (aweme_type == 68)."""
        data = {
            "desc": "Image gallery post",
            "author": {"nickname": "GalleryUser"},
            "aweme_type": 68,
            "images": [
                {"url_list": ["https://example.com/img1.jpg"], "width": 1080, "height": 1920},
                {"url_list": ["https://example.com/img2.jpg"], "width": 1080, "height": 1920},
                {"url_list": ["https://example.com/img3.jpg"], "width": 720, "height": 1280},
            ],
            "statistics": {},
        }

        metadata = self.extractor._parse_aweme_data(data, "789")

        assert metadata.title == "Image gallery post"
        assert metadata.content_type == ContentType.GALLERY
        assert metadata.gallery_images is not None
        assert len(metadata.gallery_images) == 3
        assert metadata.gallery_images[0].url == "https://example.com/img1.jpg"
        assert metadata.gallery_images[0].index == 0
        assert metadata.gallery_images[0].width == 1080
        assert metadata.gallery_images[0].height == 1920
        assert metadata.duration == 0
        assert metadata.thumbnail_url == "https://example.com/img1.jpg"

    def test_parse_empty_desc_uses_default(self):
        """When desc is empty, a default title is used."""
        data = {
            "desc": "",
            "author": {"nickname": "User"},
            "aweme_type": 0,
            "video": {"duration": 5000, "play_addr": {"url_list": []}, "cover": {"url_list": []}},
            "statistics": {},
        }

        metadata = self.extractor._parse_aweme_data(data, "111")
        assert metadata.title == "Douyin Video"

    def test_parse_gallery_empty_desc_default(self):
        """Gallery with empty desc gets 'Douyin Gallery' title."""
        data = {
            "desc": "",
            "author": {"nickname": "User"},
            "aweme_type": 68,
            "images": [],
            "statistics": {},
        }

        metadata = self.extractor._parse_aweme_data(data, "222")
        assert metadata.title == "Douyin Gallery"

    def test_parse_missing_author(self):
        """When author info is missing, defaults to 'Unknown'."""
        data = {
            "desc": "Test",
            "author": {},
            "aweme_type": 0,
            "video": {"duration": 0, "play_addr": {"url_list": []}, "cover": {"url_list": []}},
            "statistics": {},
        }

        metadata = self.extractor._parse_aweme_data(data, "333")
        assert metadata.author == "Unknown"


# ---------------------------------------------------------------------------
# TestDouyinResolveShortUrl — short URL resolution
# ---------------------------------------------------------------------------

class TestDouyinResolveShortUrl:
    """Test short URL resolution via redirect following."""

    @pytest.mark.asyncio
    async def test_resolve_short_url(self, extractor):
        """Resolves v.douyin.com short URL to full URL."""
        mock_response = MagicMock()
        mock_response.url = "https://www.douyin.com/video/7123456789012345678"

        with patch("video_downloader.extractors.douyin.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await extractor._resolve_short_url("https://v.douyin.com/iABcDeFg/")
            assert result == "https://www.douyin.com/video/7123456789012345678"


# ---------------------------------------------------------------------------
# TestDouyinGetProperty — interface compliance
# ---------------------------------------------------------------------------

class TestDouyinInterfaceCompliance:
    """Test that DouyinExtractor conforms to PlatformExtractor ABC."""

    def setup_method(self):
        self.extractor = DouyinExtractor()

    def test_get_platform_name(self):
        assert self.extractor.get_platform_name() == "douyin"

    def test_requires_browser_automation(self):
        assert self.extractor.requires_browser_automation() is True

    def test_validate_url_valid(self):
        assert self.extractor.validate_url("https://www.douyin.com/video/123") is True

    def test_validate_url_invalid(self):
        assert self.extractor.validate_url("https://www.example.com") is False

    def test_validate_url_empty(self):
        assert self.extractor.validate_url("") is False


# ---------------------------------------------------------------------------
# TestDouyinGetDownloadUrls — context parameter and error handling
# ---------------------------------------------------------------------------

class TestDouyinGetDownloadUrls:
    """Test get_download_urls context parameter and error logging."""

    @pytest.mark.asyncio
    async def test_accepts_context_keyword(self, extractor):
        """get_download_urls should accept context as keyword-only arg."""
        import inspect
        sig = inspect.signature(extractor.get_download_urls)
        assert 'context' in sig.parameters

    @pytest.mark.asyncio
    async def test_gallery_returns_image_urls(self, extractor, context):
        """Gallery content returns image URLs directly."""
        metadata = VideoMetadata(
            url='https://www.douyin.com/note/123',
            platform='douyin', title='Gallery', author='A', duration=0,
            thumbnail_url='', description='', upload_date=datetime.now(),
            quality_options=[], content_type=ContentType.GALLERY,
            video_id='123',
            gallery_images=[
                ImageItem(url='http://img1.jpg', index=0),
                ImageItem(url='http://img2.jpg', index=1),
            ],
        )
        urls = await extractor.get_download_urls(metadata, context=context)
        assert urls == ['http://img1.jpg', 'http://img2.jpg']

    @pytest.mark.asyncio
    async def test_video_delegates_to_ytdlp(self, extractor, context):
        """Video content delegates to YtDlpExtractor for fresh URLs."""
        metadata = VideoMetadata(
            url='https://www.douyin.com/video/7123456789',
            platform='douyin', title='Video', author='A', duration=10,
            thumbnail_url='', description='', upload_date=datetime.now(),
            quality_options=[], content_type=ContentType.VIDEO,
            video_id='7123456789',
        )
        mock_ytdlp = AsyncMock()
        mock_ytdlp.get_download_urls.return_value = ['http://example.com/video.mp4']

        with patch('video_downloader.extractors.yt_dlp.YtDlpExtractor', return_value=mock_ytdlp):
            urls = await extractor.get_download_urls(metadata, context=context)

        assert urls == ['http://example.com/video.mp4']

    @pytest.mark.asyncio
    async def test_video_ytdlp_failure_logs_warning(self, extractor, context, caplog):
        """When yt-dlp fails, the error should be logged (not silently swallowed)."""
        metadata = VideoMetadata(
            url='https://www.douyin.com/video/7123456789',
            platform='douyin', title='Video', author='A', duration=10,
            thumbnail_url='', description='', upload_date=datetime.now(),
            quality_options=[], content_type=ContentType.VIDEO,
            video_id='7123456789',
        )
        mock_ytdlp = AsyncMock()
        mock_ytdlp.get_download_urls.side_effect = Exception('yt-dlp signature error')

        import logging
        with caplog.at_level(logging.WARNING):
            with patch('video_downloader.extractors.yt_dlp.YtDlpExtractor', return_value=mock_ytdlp):
                urls = await extractor.get_download_urls(metadata, context=context)

        assert urls == []
        assert 'yt-dlp signature error' in caplog.text

    @pytest.mark.asyncio
    async def test_video_forwards_cookie_file_to_ytdlp(self, extractor, context):
        """cookie_file from kwargs should be forwarded to YtDlpExtractor."""
        metadata = VideoMetadata(
            url='https://www.douyin.com/video/7123456789',
            platform='douyin', title='Video', author='A', duration=10,
            thumbnail_url='', description='', upload_date=datetime.now(),
            quality_options=[], content_type=ContentType.VIDEO,
            video_id='7123456789',
        )
        mock_ytdlp = AsyncMock()
        mock_ytdlp.get_download_urls.return_value = ['http://example.com/v.mp4']

        with patch('video_downloader.extractors.yt_dlp.YtDlpExtractor', return_value=mock_ytdlp):
            await extractor.get_download_urls(
                metadata, context=context,
                cookie_file='/path/to/cookies.txt', proxy='http://proxy:8080',
            )

        mock_ytdlp.get_download_urls.assert_called_once()
        call_kwargs = mock_ytdlp.get_download_urls.call_args
        assert call_kwargs[1].get('cookie_file') == '/path/to/cookies.txt'
        assert call_kwargs[1].get('proxy') == 'http://proxy:8080'


# ---------------------------------------------------------------------------
# TestDouyinParseAwemeData — video_id population
# ---------------------------------------------------------------------------

class TestDouyinParseAwemeData:
    """Test _parse_aweme_data populates video_id."""

    def test_video_populates_video_id(self, extractor):
        aweme = {
            'desc': 'Test video',
            'author': {'nickname': 'User'},
            'aweme_type': 0,
            'video': {'duration': 5000, 'cover': {'url_list': ['http://thumb.jpg']}},
        }
        metadata = extractor._parse_aweme_data(aweme, '7123456789')
        assert metadata.video_id == '7123456789'

    def test_gallery_populates_video_id(self, extractor):
        aweme = {
            'desc': 'Test gallery',
            'author': {'nickname': 'User'},
            'aweme_type': 68,
            'images': [{'url_list': ['http://img.jpg'], 'width': 100, 'height': 100}],
        }
        metadata = extractor._parse_aweme_data(aweme, '9876543210')
        assert metadata.video_id == '9876543210'
