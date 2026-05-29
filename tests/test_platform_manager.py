"""
Tests for PlatformManager.
"""

import pytest
from video_downloader.platform_manager import PlatformManager
from video_downloader.extractors.base import PlatformExtractor
from video_downloader.models import (
    VideoMetadata,
    ExtractionContext,
    ContentType,
)
from datetime import datetime


class MockExtractor(PlatformExtractor):
    """Mock extractor for testing."""
    
    def __init__(self, platform_name: str, url_pattern: str):
        self._platform_name = platform_name
        self._url_pattern = url_pattern
    
    def can_handle(self, url: str) -> bool:
        return self._url_pattern in url
    
    def extract_metadata(self, url: str, context: ExtractionContext) -> VideoMetadata:
        return VideoMetadata(
            url=url,
            platform=self._platform_name,
            title="Mock Video",
            author="Mock Author",
            duration=120,
            thumbnail_url="https://example.com/thumb.jpg",
            description="Mock description",
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO
        )
    
    def get_download_urls(self, metadata: VideoMetadata, quality=None):
        return ["https://example.com/video.mp4"]
    
    def get_platform_name(self) -> str:
        return self._platform_name


def test_platform_manager_initialization():
    """Test PlatformManager initialization."""
    manager = PlatformManager(auto_register_builtins=False)
    
    assert manager is not None
    assert manager.get_extractor_count() == 0


def test_platform_manager_initialization_with_builtins():
    """Test PlatformManager initialization with built-in extractors."""
    manager = PlatformManager(auto_register_builtins=True)
    
    assert manager is not None
    assert manager.get_extractor_count() == 3  # yt_dlp, bilibili, douyin
    assert 'yt_dlp' in manager.list_platforms()
    assert 'bilibili' in manager.list_platforms()
    assert 'douyin' in manager.list_platforms()


def test_register_extractor():
    """Test registering an extractor."""
    manager = PlatformManager(auto_register_builtins=False)
    extractor = MockExtractor("test_platform", "test.com")
    
    manager.register_extractor(extractor)
    
    assert manager.get_extractor_count() == 1
    assert "test_platform" in manager.list_platforms()


def test_register_multiple_extractors():
    """Test registering multiple extractors."""
    manager = PlatformManager(auto_register_builtins=False)
    
    extractor1 = MockExtractor("platform1", "platform1.com")
    extractor2 = MockExtractor("platform2", "platform2.com")
    
    manager.register_extractor(extractor1)
    manager.register_extractor(extractor2)
    
    assert manager.get_extractor_count() == 2
    platforms = manager.list_platforms()
    assert "platform1" in platforms
    assert "platform2" in platforms


def test_register_invalid_extractor():
    """Test registering invalid extractor."""
    manager = PlatformManager(auto_register_builtins=False)
    
    with pytest.raises(ValueError, match="must be an instance of PlatformExtractor"):
        manager.register_extractor("not an extractor")


def test_register_duplicate_platform():
    """Test registering duplicate platform (should replace)."""
    manager = PlatformManager(auto_register_builtins=False)
    
    extractor1 = MockExtractor("test", "test1.com")
    extractor2 = MockExtractor("test", "test2.com")
    
    manager.register_extractor(extractor1)
    manager.register_extractor(extractor2)
    
    # Should have 2 extractors in list but only 1 in map
    assert manager.get_extractor_count() == 2
    
    # The map should have the latest one
    extractor = manager.get_extractor_by_name("test")
    assert extractor.can_handle("https://test2.com/video")


def test_get_extractor_by_url():
    """Test getting extractor by URL."""
    manager = PlatformManager(auto_register_builtins=False)
    
    extractor = MockExtractor("test", "test.com")
    manager.register_extractor(extractor)
    
    found = manager.get_extractor("https://test.com/video/123")
    
    assert found is not None
    assert found.get_platform_name() == "test"


def test_get_extractor_no_match():
    """Test getting extractor with no matching URL."""
    manager = PlatformManager(auto_register_builtins=False)
    
    extractor = MockExtractor("test", "test.com")
    manager.register_extractor(extractor)
    
    found = manager.get_extractor("https://other.com/video/123")
    
    assert found is None


def test_get_extractor_empty_url():
    """Test getting extractor with empty URL."""
    manager = PlatformManager(auto_register_builtins=False)
    
    found = manager.get_extractor("")
    
    assert found is None


def test_get_extractor_by_name():
    """Test getting extractor by platform name."""
    manager = PlatformManager(auto_register_builtins=False)
    
    extractor = MockExtractor("test_platform", "test.com")
    manager.register_extractor(extractor)
    
    found = manager.get_extractor_by_name("test_platform")
    
    assert found is not None
    assert found.get_platform_name() == "test_platform"


def test_get_extractor_by_name_not_found():
    """Test getting extractor by name when not found."""
    manager = PlatformManager(auto_register_builtins=False)
    
    found = manager.get_extractor_by_name("nonexistent")
    
    assert found is None


def test_list_platforms():
    """Test listing all platforms."""
    manager = PlatformManager(auto_register_builtins=False)
    
    manager.register_extractor(MockExtractor("platform1", "p1.com"))
    manager.register_extractor(MockExtractor("platform2", "p2.com"))
    manager.register_extractor(MockExtractor("platform3", "p3.com"))
    
    platforms = manager.list_platforms()
    
    assert len(platforms) == 3
    assert "platform1" in platforms
    assert "platform2" in platforms
    assert "platform3" in platforms


def test_list_platforms_empty():
    """Test listing platforms when none registered."""
    manager = PlatformManager(auto_register_builtins=False)
    
    platforms = manager.list_platforms()
    
    assert platforms == []


def test_unregister_extractor():
    """Test unregistering an extractor."""
    manager = PlatformManager(auto_register_builtins=False)
    
    extractor = MockExtractor("test", "test.com")
    manager.register_extractor(extractor)
    
    assert manager.get_extractor_count() == 1
    
    result = manager.unregister_extractor("test")
    
    assert result is True
    assert manager.get_extractor_count() == 0
    assert "test" not in manager.list_platforms()


def test_unregister_nonexistent_extractor():
    """Test unregistering non-existent extractor."""
    manager = PlatformManager(auto_register_builtins=False)
    
    result = manager.unregister_extractor("nonexistent")
    
    assert result is False


def test_platform_manager_repr():
    """Test PlatformManager string representation."""
    manager = PlatformManager(auto_register_builtins=False)
    
    manager.register_extractor(MockExtractor("test1", "test1.com"))
    manager.register_extractor(MockExtractor("test2", "test2.com"))
    
    repr_str = repr(manager)
    
    assert "PlatformManager" in repr_str
    assert "extractors=2" in repr_str
    assert "test1" in repr_str
    assert "test2" in repr_str


def test_extractor_priority():
    """Test that first matching extractor is returned."""
    manager = PlatformManager(auto_register_builtins=False)
    
    # Register two extractors that can both handle the same URL pattern
    extractor1 = MockExtractor("first", "example.com")
    extractor2 = MockExtractor("second", "example.com")
    
    manager.register_extractor(extractor1)
    manager.register_extractor(extractor2)
    
    # Should return the first one registered
    found = manager.get_extractor("https://example.com/video")
    
    assert found is not None
    assert found.get_platform_name() == "first"
