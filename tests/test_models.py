"""
Tests for data models.
"""

import pytest
from datetime import datetime
from video_downloader.models import (
    VideoMetadata,
    QualityOption,
    ImageItem,
    DownloadOptions,
    DownloadResult,
    Cookie,
    ContentType,
)


def test_quality_option_creation():
    """Test QualityOption creation."""
    option = QualityOption(
        quality_id="1080p",
        resolution="1080p",
        width=1920,
        height=1080,
        bitrate=5000000,
        file_size_estimate=100000000,
        format="mp4",
        has_audio=True
    )
    
    assert option.resolution == "1080p"
    assert option.width == 1920
    assert option.has_audio is True


def test_video_metadata_creation():
    """Test VideoMetadata creation."""
    metadata = VideoMetadata(
        url="https://example.com/video",
        platform="douyin",
        title="Test Video",
        author="Test Author",
        duration=120,
        thumbnail_url="https://example.com/thumb.jpg",
        description="Test description",
        upload_date=datetime.now(),
        quality_options=[],
        content_type=ContentType.VIDEO
    )
    
    assert metadata.platform == "douyin"
    assert metadata.title == "Test Video"
    assert metadata.content_type == ContentType.VIDEO


def test_image_item_creation():
    """Test ImageItem creation."""
    image = ImageItem(
        url="https://example.com/image.jpg",
        index=1,
        width=1080,
        height=1920,
        format="jpg"
    )
    
    assert image.index == 1
    assert image.format == "jpg"


def test_download_options_defaults():
    """Test DownloadOptions default values."""
    options = DownloadOptions()
    
    assert options.quality is None
    assert options.output_path is None
    assert options.audio_only is False


def test_download_result_success():
    """Test DownloadResult for successful download."""
    result = DownloadResult(
        success=True,
        file_path="/path/to/video.mp4",
        file_size=1000000,
        duration=5.5
    )
    
    assert result.success is True
    assert result.file_path == "/path/to/video.mp4"
    assert result.error is None


def test_download_result_failure():
    """Test DownloadResult for failed download."""
    result = DownloadResult(
        success=False,
        error="Network error"
    )
    
    assert result.success is False
    assert result.error == "Network error"
    assert result.file_path is None


def test_cookie_creation():
    """Test Cookie creation."""
    cookie = Cookie(
        name="sessionid",
        value="abc123",
        domain=".douyin.com",
        path="/",
        expires=datetime(2025, 12, 31),
        secure=True,
        http_only=True
    )
    
    assert cookie.name == "sessionid"
    assert cookie.domain == ".douyin.com"
    assert cookie.secure is True
