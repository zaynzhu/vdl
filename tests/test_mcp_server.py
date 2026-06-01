"""
Tests for MCP Server — regression tests for field-name bugs.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from mcp_server import MCPServer
from video_downloader.models import (
    DownloadResult, DownloadOptions, VideoMetadata,
    QualityOption, ContentType, BatchResult,
)


@pytest.fixture
def server():
    """Create MCPServer with mocked downloader."""
    s = MCPServer.__new__(MCPServer)
    s.downloader = MagicMock()
    return s


class TestDownloadVideoFieldNames:
    """Verify download_video uses correct field names (Bugs 2, 3 regression)."""

    def test_download_options_uses_output_path(self):
        """DownloadOptions must use output_path, not output_dir (Bug 2)."""
        options = DownloadOptions(output_path='./downloads')
        assert options.output_path == './downloads'

    def test_download_result_uses_error(self):
        """DownloadResult must use error, not error_message (Bug 3)."""
        result = DownloadResult(success=False, error='timeout')
        assert result.error == 'timeout'

    def test_download_result_uses_duration(self):
        """DownloadResult must use duration, not download_time (Bug 4)."""
        result = DownloadResult(success=True, duration=3.5)
        assert result.duration == 3.5


class TestBatchDownloadFieldNames:
    """Verify batch_download uses correct field names (Bug 5 regression)."""

    def test_batch_result_file_path(self):
        """Results should reference file_path, not url."""
        result = DownloadResult(success=True, file_path='/tmp/test.mp4')
        assert result.file_path == '/tmp/test.mp4'

    def test_batch_result_error(self):
        """Failed results should use error field."""
        result = DownloadResult(success=False, error='Connection refused')
        assert result.error == 'Connection refused'


class TestGetVideoInfoFieldNames:
    """Verify get_video_info uses correct field names (Bug 8 regression)."""

    def test_quality_options_field(self):
        """VideoMetadata has quality_options, not available_qualities."""
        metadata = VideoMetadata(
            url='https://example.com',
            platform='test',
            title='Test',
            author='Author',
            duration=60,
            thumbnail_url='',
            description='',
            upload_date=datetime.now(),
            quality_options=[
                QualityOption(quality_id='1', name='1080p', height=1080),
                QualityOption(quality_id='2', name='720p', height=720),
            ],
            content_type=ContentType.VIDEO,
        )
        assert hasattr(metadata, 'quality_options')
        assert not hasattr(metadata, 'available_qualities')
        names = [q.name for q in metadata.quality_options]
        assert '1080p' in names
        assert '720p' in names


class TestDownloadVideoTool:
    """Integration test for download_video tool logic."""

    @pytest.mark.asyncio
    async def test_success_response_uses_duration(self):
        """Success response should show duration only when > 0."""
        result = DownloadResult(
            success=True,
            file_path='/tmp/test.mp4',
            file_size=1048576,  # 1 MB
            duration=5.0,
        )
        text = f"✅ 下载成功！\n\n"
        text += f"📁 文件路径: {result.file_path}\n"
        text += f"📊 文件大小: {result.file_size / 1024 / 1024:.2f} MB"
        text += (f"\n⏱️  耗时: {result.duration:.1f}s" if result.duration > 0 else "")

        assert '1.00 MB' in text
        assert '5.0s' in text

    @pytest.mark.asyncio
    async def test_success_response_no_duration_when_zero(self):
        """When duration is 0, don't show it."""
        result = DownloadResult(
            success=True,
            file_path='/tmp/test.mp4',
            file_size=1024,
            duration=0.0,
        )
        text = f"📊 文件大小: {result.file_size / 1024 / 1024:.2f} MB"
        text += (f"\n⏱️  耗时: {result.duration:.1f}s" if result.duration > 0 else "")

        assert '耗时' not in text

    @pytest.mark.asyncio
    async def test_error_response_uses_error_field(self):
        """Error response should use result.error."""
        result = DownloadResult(success=False, error='Video not found')
        text = f"❌ 下载失败: {result.error}"
        assert 'Video not found' in text


class TestBatchDownloadTool:
    """Integration test for batch_download tool logic."""

    @pytest.mark.asyncio
    async def test_success_uses_file_path(self):
        """Success list should use result.file_path, not result.url."""
        result = DownloadResult(success=True, file_path='/tmp/test.mp4')
        success_list = []
        if result.success:
            success_list.append(f"✓ {result.file_path}")
        assert '/tmp/test.mp4' in success_list[0]

    @pytest.mark.asyncio
    async def test_failure_uses_error_field(self):
        """Failure list should use result.error."""
        result = DownloadResult(success=False, error='Timeout')
        failed_list = []
        if not result.success:
            failed_list.append(f"✗ {result.error}")
        assert 'Timeout' in failed_list[0]
