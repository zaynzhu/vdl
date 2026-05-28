"""
Tests for YtDlpExtractor.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from video_downloader.extractors.yt_dlp import YtDlpExtractor
from video_downloader.models import VideoMetadata, QualityOption, ContentType
from video_downloader.exceptions import PlatformError, VideoUnavailableError


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


class TestYtDlpBuildOpts:
    """Test yt-dlp options building."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    def test_default_opts(self):
        opts = self.extractor._build_opts()
        assert opts['quiet'] is True
        assert opts['no_warnings'] is True
        assert 'format' in opts

    def test_cookie_file(self):
        opts = self.extractor._build_opts(cookie_file='/path/to/cookies.txt')
        assert opts['cookiefile'] == '/path/to/cookies.txt'

    def test_proxy(self):
        opts = self.extractor._build_opts(proxy='http://127.0.0.1:7897')
        assert opts['proxy'] == 'http://127.0.0.1:7897'

    def test_quality_format(self):
        opts = self.extractor._build_opts(quality='best[height<=720]')
        assert opts['format'] == 'best[height<=720]'


class TestYtDlpExtractMetadata:
    """Test extract_metadata async method."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    @patch.object(YtDlpExtractor, '_extract_info')
    def test_extract_metadata_success(self, mock_extract):
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
        import asyncio
        metadata = asyncio.get_event_loop().run_until_complete(
            self.extractor.extract_metadata("https://www.youtube.com/watch?v=abc")
        )
        assert metadata.title == 'Test Video'
        assert metadata.platform == 'youtube'

    @patch.object(YtDlpExtractor, '_extract_info')
    def test_extract_metadata_unavailable(self, mock_extract):
        import yt_dlp
        mock_extract.side_effect = yt_dlp.utils.DownloadError('Private video')
        import asyncio
        with pytest.raises(VideoUnavailableError):
            asyncio.get_event_loop().run_until_complete(
                self.extractor.extract_metadata("https://www.youtube.com/watch?v=private")
            )

    @patch.object(YtDlpExtractor, '_extract_info')
    def test_extract_metadata_none_result(self, mock_extract):
        mock_extract.return_value = None
        import asyncio
        with pytest.raises(VideoUnavailableError):
            asyncio.get_event_loop().run_until_complete(
                self.extractor.extract_metadata("https://www.youtube.com/watch?v=none")
            )


class TestYtDlpGetDownloadUrls:
    """Test get_download_urls async method."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    @patch.object(YtDlpExtractor, '_extract_info')
    def test_get_download_urls_from_url_field(self, mock_extract):
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
        import asyncio
        urls = asyncio.get_event_loop().run_until_complete(
            self.extractor.get_download_urls(metadata)
        )
        assert urls == ['https://example.com/video.mp4']

    @patch.object(YtDlpExtractor, '_extract_info')
    def test_get_download_urls_from_formats(self, mock_extract):
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
        import asyncio
        urls = asyncio.get_event_loop().run_until_complete(
            self.extractor.get_download_urls(metadata)
        )
        assert urls == ['https://example.com/best.mp4']

    @patch.object(YtDlpExtractor, '_extract_info')
    def test_get_download_urls_none_raises(self, mock_extract):
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
        import asyncio
        with pytest.raises(PlatformError):
            asyncio.get_event_loop().run_until_complete(
                self.extractor.get_download_urls(metadata)
            )
