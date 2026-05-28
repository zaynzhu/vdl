"""
Tests for VideoDownloader core functionality.
"""

import pytest
from video_downloader import VideoDownloader, DownloadOptions
from video_downloader.exceptions import ValidationError
from video_downloader.config import DownloaderConfig


def test_video_downloader_initialization():
    """Test VideoDownloader initialization."""
    downloader = VideoDownloader()
    
    assert downloader.config is not None
    assert isinstance(downloader.config, DownloaderConfig)


def test_video_downloader_with_custom_config():
    """Test VideoDownloader with custom configuration."""
    config = DownloaderConfig(
        output_dir="./custom_downloads",
        max_retries=5
    )
    
    downloader = VideoDownloader(config)
    
    assert downloader.config.output_dir == "./custom_downloads"
    assert downloader.config.max_retries == 5


def test_validate_url_empty():
    """Test URL validation with empty URL."""
    downloader = VideoDownloader()
    
    with pytest.raises(ValidationError, match="URL cannot be empty"):
        downloader._validate_url("")


def test_validate_url_invalid_type():
    """Test URL validation with invalid type."""
    downloader = VideoDownloader()
    
    with pytest.raises(ValidationError, match="URL must be a string"):
        downloader._validate_url(123)


def test_validate_url_invalid_protocol():
    """Test URL validation with invalid protocol."""
    downloader = VideoDownloader()
    
    with pytest.raises(ValidationError, match="URL must start with"):
        downloader._validate_url("ftp://example.com/video")


def test_validate_url_valid():
    """Test URL validation with valid URL."""
    downloader = VideoDownloader()
    
    # Should not raise exception
    downloader._validate_url("https://www.douyin.com/video/123")
    downloader._validate_url("http://www.bilibili.com/video/BV123")


def test_list_supported_platforms():
    """Test listing supported platforms."""
    downloader = VideoDownloader()
    
    platforms = downloader.list_supported_platforms()
    
    # Should have built-in platforms registered
    assert len(platforms) > 0
    assert 'bilibili' in platforms
    assert 'douyin' in platforms


@pytest.mark.asyncio
async def test_batch_download_empty_list():
    """Test batch download with empty URL list."""
    downloader = VideoDownloader()
    
    result = await downloader.batch_download([])
    
    assert result.total == 0
    assert result.successful == 0
    assert result.failed == 0
    assert len(result.results) == 0
