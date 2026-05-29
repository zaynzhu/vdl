"""
Tests for DownloadManager — TDD regression tests for field-name bugs.
"""

import os
import pytest
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from video_downloader.download_manager import DownloadManager
from video_downloader.models import (
    DownloadResult, DownloadOptions, VideoMetadata,
    QualityOption, ContentType, ExtractionContext,
    Fingerprint, Cookie,
)
from video_downloader.config import DownloaderConfig


@pytest.fixture
def config():
    return DownloaderConfig(
        output_dir='./downloads',
        filename_template='{title}',
        timeout=30,
        max_retries=3,
    )


@pytest.fixture
def manager(config):
    return DownloadManager(config)


@pytest.fixture
def sample_metadata():
    return VideoMetadata(
        url='https://www.bilibili.com/video/BV1xx411c7mD',
        platform='bilibili',
        title='Test Video',
        author='Test Author',
        duration=120,
        thumbnail_url='https://example.com/thumb.jpg',
        description='A test video',
        upload_date=datetime(2026, 1, 15),
        quality_options=[],
        content_type=ContentType.VIDEO,
    )


# --- DownloadResult field tests (Bug 4 & 5 regression) ---

class TestDownloadResultFields:
    """Verify DownloadResult uses correct field names."""

    def test_success_result_has_duration_field(self):
        """DownloadResult uses 'duration', not 'download_time' (Bug 4)."""
        result = DownloadResult(
            success=True,
            file_path='/tmp/test.mp4',
            file_size=1024,
            duration=5.0,
        )
        assert result.duration == 5.0
        assert result.error is None

    def test_error_result_has_error_field(self):
        """DownloadResult uses 'error', not 'error_message' (Bug 5)."""
        result = DownloadResult(
            success=False,
            file_path='/tmp/test.mp4',
            error='Connection refused',
        )
        assert result.error == 'Connection refused'
        assert result.duration == 0.0

    def test_default_values(self):
        result = DownloadResult(success=True)
        assert result.file_path is None
        assert result.file_size == 0
        assert result.duration == 0.0
        assert result.error is None


# --- generate_filename tests (Bug 6 regression) ---

class TestGenerateFilename:
    """Verify generate_filename uses metadata.url, not video_id."""

    def test_title_placeholder(self, manager, sample_metadata):
        filename = manager.generate_filename('{title}', sample_metadata, '.mp4')
        assert filename == 'Test Video.mp4'

    def test_author_placeholder(self, manager, sample_metadata):
        filename = manager.generate_filename('{author}', sample_metadata, '.mp4')
        assert filename == 'Test Author.mp4'

    def test_id_from_url(self, manager, sample_metadata):
        """{id} extracts video ID from URL path, not from nonexistent video_id field."""
        filename = manager.generate_filename('{id}', sample_metadata, '.mp4')
        assert filename == 'BV1xx411c7mD.mp4'

    def test_id_from_url_with_query(self, manager):
        metadata = VideoMetadata(
            url='https://www.bilibili.com/video/BV1xx?p=1',
            platform='bilibili',
            title='Test',
            author='Author',
            duration=60,
            thumbnail_url='',
            description='',
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO,
        )
        filename = manager.generate_filename('{id}', metadata, '.mp4')
        assert filename == 'BV1xx.mp4'

    def test_platform_placeholder(self, manager, sample_metadata):
        filename = manager.generate_filename('{platform}', sample_metadata, '.mp4')
        assert filename == 'bilibili.mp4'

    def test_date_placeholder(self, manager, sample_metadata):
        filename = manager.generate_filename('{date}', sample_metadata, '.mp4')
        assert filename == '2026-01-15.mp4'

    def test_combined_template(self, manager, sample_metadata):
        filename = manager.generate_filename('{title}_{author}', sample_metadata)
        assert filename == 'Test Video_Test Author'

    def test_empty_url_gives_unknown_id(self, manager):
        metadata = VideoMetadata(
            url='',
            platform='test',
            title='T',
            author='A',
            duration=0,
            thumbnail_url='',
            description='',
            upload_date=datetime.now(),
            quality_options=[],
            content_type=ContentType.VIDEO,
        )
        filename = manager.generate_filename('{id}', metadata)
        assert 'unknown' in filename


# --- sanitize_filename tests ---

class TestSanitizeFilename:

    def test_removes_illegal_chars(self, manager):
        assert manager.sanitize_filename('file<>:"/\\|?*.mp4') == 'file_________.mp4'

    def test_strips_leading_trailing_dots(self, manager):
        assert manager.sanitize_filename('..file..') == 'file'

    def test_strips_leading_trailing_spaces(self, manager):
        assert manager.sanitize_filename('  file  ') == 'file'

    def test_long_filename_truncated(self, manager):
        long_name = 'a' * 300
        result = manager.sanitize_filename(long_name)
        assert len(result) <= 200

    def test_empty_filename_gives_download(self, manager):
        assert manager.sanitize_filename('') == 'download'

    def test_preserves_normal_filename(self, manager):
        assert manager.sanitize_filename('my_video.mp4') == 'my_video.mp4'


# --- resolve_output_path tests ---

class TestResolveOutputPath:

    def test_returns_path_when_no_conflict(self, manager, tmp_path):
        result = manager.resolve_output_path(str(tmp_path), 'test.mp4')
        assert result == os.path.join(str(tmp_path), 'test.mp4')

    def test_auto_renames_on_conflict(self, manager, tmp_path):
        # Create existing file
        existing = tmp_path / 'test.mp4'
        existing.write_text('old')
        result = manager.resolve_output_path(str(tmp_path), 'test.mp4')
        assert 'test_1.mp4' in result

    def test_no_rename_when_auto_rename_false(self, manager, tmp_path):
        existing = tmp_path / 'test.mp4'
        existing.write_text('old')
        result = manager.resolve_output_path(str(tmp_path), 'test.mp4', auto_rename=False)
        assert result.endswith('test.mp4')


# --- backoff delay tests ---

class TestBackoffDelay:

    def test_first_attempt(self, manager):
        assert manager._calculate_backoff_delay(0) == 1

    def test_second_attempt(self, manager):
        assert manager._calculate_backoff_delay(1) == 2

    def test_max_delay_60(self, manager):
        assert manager._calculate_backoff_delay(10) == 60


# --- download_multiple result construction (Bug 5 regression) ---

class TestDownloadMultiple:

    @pytest.mark.asyncio
    async def test_failed_download_uses_error_field(self, manager, tmp_path):
        """download_multiple must use 'error' field, not 'error_message'."""
        # Create a download that will fail (bad URL)
        downloads = [
            ('http://localhost:1/nonexistent', str(tmp_path / 'fail.mp4'), None),
        ]

        with patch.object(manager, 'download_file', side_effect=Exception('Connection refused')):
            results = await manager.download_multiple(downloads)

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error == 'Connection refused'
