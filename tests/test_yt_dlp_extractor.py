"""
Tests for YtDlpExtractor.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from video_downloader.extractors.yt_dlp import YtDlpExtractor
from video_downloader.models import (
    VideoMetadata, QualityOption, ContentType,
    ExtractionContext, Fingerprint,
)
from video_downloader.exceptions import PlatformError, VideoUnavailableError


@pytest.fixture
def context():
    """Minimal ExtractionContext for testing."""
    return ExtractionContext(
        cookies=[],
        fingerprint=Fingerprint(
            user_agent="test-agent",
            platform="test",
            screen_width=1920,
            screen_height=1080,
            color_depth=24,
            language="en",
            timezone="UTC",
            headers={},
        ),
    )


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

    def test_get_platform_name(self):
        assert self.extractor.get_platform_name() == "yt_dlp"


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
        assert metadata.content_type == ContentType.VIDEO

    def test_map_video_id(self):
        """_map_metadata should populate video_id from yt-dlp 'id' field."""
        ytdlp_info = {
            'title': 'Test',
            'webpage_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'extractor': 'youtube',
            'id': 'dQw4w9WgXcQ',
            'formats': [],
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        assert metadata.video_id == 'dQw4w9WgXcQ'

    def test_map_video_id_missing(self):
        """_map_metadata should set video_id=None when yt-dlp has no 'id'."""
        ytdlp_info = {
            'title': 'Test',
            'webpage_url': 'https://example.com/video',
            'extractor': 'generic',
            'formats': [],
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        assert metadata.video_id is None

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
        assert metadata.content_type == ContentType.VIDEO

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
        assert len(metadata.quality_options) == 3
        assert metadata.quality_options[0].height == 1080
        assert metadata.quality_options[0].name == "1080p"
        assert metadata.quality_options[0].format == "mp4"

    def test_map_channel_fallback(self):
        """Test 'channel' field used when 'uploader' missing."""
        ytdlp_info = {
            'title': 'Test',
            'channel': 'Channel Name',
            'webpage_url': 'https://www.youtube.com/watch?v=abc',
            'extractor': 'youtube',
            'id': 'abc',
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        assert metadata.author == 'Channel Name'

    def test_map_generic_extractor_resolves_platform(self):
        """Test that generic extractor resolves platform from URL."""
        ytdlp_info = {
            'title': 'Test',
            'extractor': 'generic',
            'webpage_url': 'https://www.bilibili.com/video/BV123',
            'id': 'BV123',
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        assert metadata.platform == 'bilibili'

    def test_map_invalid_upload_date(self):
        """Test that invalid upload_date is handled gracefully."""
        ytdlp_info = {
            'title': 'Test',
            'upload_date': 'not-a-date',
            'webpage_url': 'https://www.youtube.com/watch?v=test',
            'extractor': 'youtube',
            'id': 'test',
        }
        metadata = self.extractor._map_metadata(ytdlp_info)
        # Should still return valid metadata (upload_date defaults to now)
        assert metadata.title == 'Test'


class TestYtDlpMapQuality:
    """Test human-readable quality mapping."""

    def test_1080p(self):
        result = YtDlpExtractor._map_quality("1080p")
        assert "height<=1080" in result

    def test_720p(self):
        result = YtDlpExtractor._map_quality("720p")
        assert "height<=720" in result

    def test_480p(self):
        result = YtDlpExtractor._map_quality("480p")
        assert "height<=480" in result

    def test_passthrough_ytdlp_format(self):
        fmt = "bestvideo[height<=1080]+bestaudio/best"
        assert YtDlpExtractor._map_quality(fmt) == fmt

    def test_passthrough_with_plus(self):
        fmt = "bestvideo+bestaudio"
        assert YtDlpExtractor._map_quality(fmt) == fmt

    def test_bare_digits(self):
        result = YtDlpExtractor._map_quality("1080")
        assert "height<=1080" in result

    def test_uppercase_p(self):
        result = YtDlpExtractor._map_quality("720P")
        assert "height<=720" in result

    def test_unknown_falls_back_to_best(self):
        result = YtDlpExtractor._map_quality("4k")
        assert result == "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"


class TestYtDlpBuildOpts:
    """Test yt-dlp options building."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    def test_default_opts(self):
        opts = self.extractor._build_opts()
        assert opts['quiet'] is True
        assert opts['no_warnings'] is True
        assert 'format' in opts

    def test_nocheckcertificate_removed(self):
        opts = self.extractor._build_opts()
        assert 'nocheckcertificate' not in opts

    def test_cookie_file(self):
        opts = self.extractor._build_opts(cookie_file='/path/to/cookies.txt')
        assert opts['cookiefile'] == '/path/to/cookies.txt'

    def test_proxy(self):
        opts = self.extractor._build_opts(proxy='http://127.0.0.1:7897')
        assert opts['proxy'] == 'http://127.0.0.1:7897'

    def test_quality_format(self):
        opts = self.extractor._build_opts(quality='best[height<=720]')
        assert opts['format'] == 'best[height<=720]'

    def test_quality_mapped(self):
        opts = self.extractor._build_opts(quality='1080p')
        assert "height<=1080" in opts['format']


class TestYtDlpExtractMetadata:
    """Test extract_metadata async method."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    @pytest.mark.asyncio
    @patch.object(YtDlpExtractor, '_extract_info')
    async def test_extract_metadata_success(self, mock_extract, context):
        mock_extract.return_value = {
            'title': 'Test Video',
            'uploader': 'Author',
            'duration': 60,
            'thumbnail': 'https://example.com/thumb.jpg',
            'description': 'Desc',
            'upload_date': '20260101',
            'webpage_url': 'https://www.youtube.com/watch?v=abc',
            'extractor': 'youtube',
            'id': 'abc',
            'formats': [],
        }
        metadata = await self.extractor.extract_metadata("https://www.youtube.com/watch?v=abc", context)
        assert metadata.title == 'Test Video'
        assert metadata.platform == 'youtube'

    @pytest.mark.asyncio
    @patch.object(YtDlpExtractor, '_extract_info')
    async def test_extract_metadata_unavailable(self, mock_extract, context):
        import yt_dlp
        mock_extract.side_effect = yt_dlp.utils.DownloadError('Private video')
        with pytest.raises(VideoUnavailableError):
            await self.extractor.extract_metadata("https://www.youtube.com/watch?v=private", context)

    @pytest.mark.asyncio
    @patch.object(YtDlpExtractor, '_extract_info')
    async def test_extract_metadata_none_result(self, mock_extract, context):
        mock_extract.return_value = None
        with pytest.raises(VideoUnavailableError):
            await self.extractor.extract_metadata("https://www.youtube.com/watch?v=none", context)


class TestYtDlpGetDownloadUrls:
    """Test get_download_urls async method."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    @pytest.mark.asyncio
    @patch.object(YtDlpExtractor, '_extract_info')
    async def test_get_download_urls_from_url_field(self, mock_extract):
        mock_extract.return_value = {
            'url': 'https://example.com/video.mp4',
        }
        metadata = VideoMetadata(
            url='https://www.youtube.com/watch?v=abc',
            platform='youtube',
            title='Test',
            author='Author',
            duration=60,
            thumbnail_url='',
            description='',
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO,
        )
        urls = await self.extractor.get_download_urls(metadata)
        assert urls == ['https://example.com/video.mp4']

    @pytest.mark.asyncio
    @patch.object(YtDlpExtractor, '_extract_info')
    async def test_get_download_urls_from_formats(self, mock_extract):
        mock_extract.return_value = {
            'formats': [
                {'url': 'https://example.com/low.mp4'},
                {'url': 'https://example.com/best.mp4'},
            ],
        }
        metadata = VideoMetadata(
            url='https://www.youtube.com/watch?v=abc',
            platform='youtube',
            title='Test',
            author='Author',
            duration=60,
            thumbnail_url='',
            description='',
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO,
        )
        urls = await self.extractor.get_download_urls(metadata)
        assert urls == ['https://example.com/best.mp4']

    @pytest.mark.asyncio
    @patch.object(YtDlpExtractor, '_extract_info')
    async def test_get_download_urls_none_raises(self, mock_extract):
        mock_extract.return_value = None
        metadata = VideoMetadata(
            url='https://www.youtube.com/watch?v=abc',
            platform='youtube',
            title='Test',
            author='Author',
            duration=60,
            thumbnail_url='',
            description='',
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO,
        )
        with pytest.raises(PlatformError):
            await self.extractor.get_download_urls(metadata)

    @pytest.mark.asyncio
    async def test_get_download_urls_accepts_context(self):
        """get_download_urls should accept context keyword arg."""
        import inspect
        sig = inspect.signature(self.extractor.get_download_urls)
        assert 'context' in sig.parameters
