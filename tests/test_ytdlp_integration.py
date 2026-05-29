"""
Integration tests for yt-dlp based extraction.
These tests make real network calls — skip in CI with: pytest -m "not integration"
"""

import pytest
from video_downloader.extractors.yt_dlp import YtDlpExtractor
from video_downloader.models import ExtractionContext


@pytest.fixture
def context():
    return ExtractionContext()


@pytest.mark.integration
class TestYtDlpIntegration:
    """Real network tests for YtDlpExtractor."""

    def setup_method(self):
        self.extractor = YtDlpExtractor()

    @pytest.mark.asyncio
    async def test_youtube_metadata(self, context):
        """Test extracting metadata from a real YouTube video."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        metadata = await self.extractor.extract_metadata(url, context)
        assert metadata.title
        assert metadata.platform == 'youtube'
        assert metadata.duration > 0

    @pytest.mark.asyncio
    async def test_bilibili_metadata(self, context):
        """Test extracting metadata from a real Bilibili video."""
        url = "https://www.bilibili.com/video/BV1GJ411x7h7"
        metadata = await self.extractor.extract_metadata(url, context)
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
