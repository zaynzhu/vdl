"""
Tests for platform extractors.
"""

import pytest
from video_downloader.extractors.base import PlatformExtractor
from video_downloader.models import (
    VideoMetadata,
    ExtractionContext,
    AntiBotStrategy,
    ContentType,
)
from datetime import datetime


class MockExtractor(PlatformExtractor):
    """Mock extractor for testing."""
    
    def can_handle(self, url: str) -> bool:
        return "mock.com" in url
    
    def extract_metadata(self, url: str, context: ExtractionContext) -> VideoMetadata:
        return VideoMetadata(
            url=url,
            platform="mock",
            title="Mock Video",
            author="Mock Author",
            duration=120,
            thumbnail_url="https://mock.com/thumb.jpg",
            description="Mock description",
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO
        )
    
    def get_download_urls(self, metadata: VideoMetadata, quality=None):
        return ["https://mock.com/video.mp4"]
    
    def get_platform_name(self) -> str:
        return "mock"


def test_extractor_can_handle():
    """Test extractor URL handling."""
    extractor = MockExtractor()
    
    assert extractor.can_handle("https://mock.com/video/123") is True
    assert extractor.can_handle("https://other.com/video/123") is False


def test_extractor_validate_url():
    """Test extractor URL validation."""
    extractor = MockExtractor()
    
    assert extractor.validate_url("https://mock.com/video/123") is True
    assert extractor.validate_url("https://other.com/video/123") is False
    assert extractor.validate_url("") is False
    assert extractor.validate_url("ftp://mock.com/video") is False


def test_extractor_requires_browser_automation_default():
    """Test default browser automation requirement."""
    extractor = MockExtractor()
    
    assert extractor.requires_browser_automation() is False


def test_extractor_get_anti_bot_strategy_default():
    """Test default anti-bot strategy."""
    extractor = MockExtractor()
    
    assert extractor.get_anti_bot_strategy() == AntiBotStrategy.NONE


def test_extractor_repr():
    """Test extractor string representation."""
    extractor = MockExtractor()
    
    repr_str = repr(extractor)
    
    assert "MockExtractor" in repr_str
    assert "platform=mock" in repr_str


def test_extractor_get_platform_name():
    """Test getting platform name."""
    extractor = MockExtractor()
    
    assert extractor.get_platform_name() == "mock"
