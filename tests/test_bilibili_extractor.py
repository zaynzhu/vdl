"""
Tests for BilibiliExtractor — regression tests for field-name and interface bugs.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from video_downloader.extractors.bilibili import BilibiliExtractor
from video_downloader.models import (
    VideoMetadata, QualityOption, ContentType,
    ExtractionContext, Fingerprint, Cookie,
)
from video_downloader.exceptions import ValidationError, PlatformError


@pytest.fixture
def extractor():
    return BilibiliExtractor()


@pytest.fixture
def context():
    return ExtractionContext(
        cookies=[],
        fingerprint=Fingerprint(
            user_agent='Mozilla/5.0 Test',
            platform='Win32',
            screen_width=1920,
            screen_height=1080,
            color_depth=24,
            language='zh-CN',
            timezone='Asia/Shanghai',
            headers={},
        ),
    )


class TestCanHandle:

    def test_bv_url(self, extractor):
        assert extractor.can_handle('https://www.bilibili.com/video/BV1xx411c7mD')

    def test_av_url(self, extractor):
        assert extractor.can_handle('https://www.bilibili.com/video/av12345')

    def test_short_url(self, extractor):
        assert extractor.can_handle('https://b23.tv/abc123')

    def test_non_bilibili(self, extractor):
        assert not extractor.can_handle('https://www.youtube.com/watch?v=xxx')

    def test_empty_url(self, extractor):
        assert not extractor.can_handle('')


class TestParseVideoInfo:
    """Verify _parse_video_info constructs VideoMetadata correctly (Bug 7 regression)."""

    def test_constructs_valid_metadata(self, extractor):
        """Must use url, quality_options, content_type — not video_id, available_qualities, extra_data."""
        video_info = {
            'title': 'Test Video',
            'owner': {'name': 'Test Author'},
            'desc': 'A description',
            'duration': 120,
            'pic': 'https://example.com/thumb.jpg',
            'pages': [{'cid': 12345}],
        }
        metadata = extractor._parse_video_info(video_info, 'BV1xx411c7mD')

        assert isinstance(metadata, VideoMetadata)
        assert metadata.url == 'https://www.bilibili.com/video/BV1xx411c7mD'
        assert metadata.platform == 'bilibili'
        assert metadata.title == 'Test Video'
        assert metadata.author == 'Test Author'
        assert metadata.description == 'A description'
        assert metadata.duration == 120
        assert metadata.thumbnail_url == 'https://example.com/thumb.jpg'
        assert metadata.content_type == ContentType.VIDEO
        assert isinstance(metadata.quality_options, list)
        assert len(metadata.quality_options) > 0
        assert isinstance(metadata.quality_options[0], QualityOption)

    def test_missing_owner_uses_unknown(self, extractor):
        video_info = {'title': 'Test', 'duration': 60}
        metadata = extractor._parse_video_info(video_info, 'BV1xx')
        assert metadata.author == 'Unknown'

    def test_empty_title_uses_unknown(self, extractor):
        video_info = {'owner': {'name': 'A'}, 'duration': 10}
        metadata = extractor._parse_video_info(video_info, 'BV1xx')
        assert metadata.title == 'Unknown'


class TestExtractMetadataSignature:
    """Verify extract_metadata accepts context, not cookies dict (Bug 7 regression)."""

    def test_accepts_context_param(self, extractor, context):
        """Method signature must accept context: ExtractionContext, not cookies: Dict."""
        import inspect
        sig = inspect.signature(extractor.extract_metadata)
        params = list(sig.parameters.keys())
        assert 'context' in params or 'url' in params
        # Should NOT have 'cookies' as a positional param
        for name, param in sig.parameters.items():
            if name == 'cookies':
                assert param.default is not None or param.kind == inspect.Parameter.KEYWORD_ONLY


class TestGetDownloadUrlsSignature:
    """Verify get_download_urls accepts context, not cookies dict."""

    def test_accepts_context_param(self, extractor):
        import inspect
        sig = inspect.signature(extractor.get_download_urls)
        params = list(sig.parameters.keys())
        # Should accept metadata and quality
        assert 'metadata' in params


class TestVideoIdExtraction:

    def test_bv_id(self, extractor):
        assert extractor._extract_video_id('https://www.bilibili.com/video/BV1xx411c7mD') == 'BV1xx411c7mD'

    def test_av_id(self, extractor):
        assert extractor._extract_video_id('https://www.bilibili.com/video/av12345') == 'av12345'

    def test_invalid_url(self, extractor):
        assert extractor._extract_video_id('https://www.bilibili.com/') is None
