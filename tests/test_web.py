"""
Tests for VDL Web UI API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from video_downloader.models import (
    VideoMetadata, QualityOption, ContentType,
    DownloadResult, BatchResult,
)


@pytest.fixture
def app():
    from video_downloader.web import app, state
    # Reset state
    state.tasks.clear()
    return app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestPreview:

    def test_preview_returns_metadata(self, client):
        metadata = VideoMetadata(
            url='https://www.bilibili.com/video/BV1xx',
            platform='bilibili', title='Test Video', author='Author',
            duration=120, thumbnail_url='https://example.com/thumb.jpg',
            description='desc', upload_date=datetime.now(),
            quality_options=[
                QualityOption(quality_id='80', name='1080P'),
                QualityOption(quality_id='64', name='720P'),
            ],
            content_type=ContentType.VIDEO,
        )
        with patch('video_downloader.web.YtDlpExtractor') as mock_extractor_cls:
            mock_extractor = mock_extractor_cls.return_value
            mock_extractor.get_platform_name_for_url.return_value = 'bilibili'
            mock_extractor.extract_metadata = AsyncMock(return_value=metadata)
            resp = client.post('/api/preview', json={'url': 'https://www.bilibili.com/video/BV1xx'})

        assert resp.status_code == 200
        data = resp.json()
        assert data['title'] == 'Test Video'
        assert data['platform'] == 'bilibili'
        assert len(data['qualities']) == 2

    def test_preview_empty_url_returns_400(self, client):
        resp = client.post('/api/preview', json={'url': ''})
        assert resp.status_code == 400

    def test_preview_no_url_returns_400(self, client):
        resp = client.post('/api/preview', json={})
        assert resp.status_code == 400


class TestDownload:

    def test_download_returns_task_id(self, client):
        with patch('video_downloader.web._run_download'):
            resp = client.post('/api/download', json={'url': 'https://example.com/video'})

        assert resp.status_code == 200
        data = resp.json()
        assert 'id' in data
        assert data['status'] == 'pending'

    def test_download_empty_url_returns_400(self, client):
        resp = client.post('/api/download', json={'url': ''})
        assert resp.status_code == 400


class TestQueue:

    def test_queue_starts_empty(self, client):
        resp = client.get('/api/queue')
        assert resp.status_code == 200
        assert resp.json() == []

    def test_queue_shows_tasks(self, client):
        from video_downloader.web import state, DownloadTask, TaskStatus
        state.tasks['test1'] = DownloadTask(
            id='test1', url='https://example.com', title='Test',
            status=TaskStatus.COMPLETED,
        )
        resp = client.get('/api/queue')
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 1
        assert tasks[0]['id'] == 'test1'

    def test_cancel_nonexistent_returns_404(self, client):
        resp = client.delete('/api/queue/nonexistent')
        assert resp.status_code == 404

    def test_cancel_completed_returns_400(self, client):
        from video_downloader.web import state, DownloadTask, TaskStatus
        state.tasks['done'] = DownloadTask(
            id='done', url='https://example.com',
            status=TaskStatus.COMPLETED,
        )
        resp = client.delete('/api/queue/done')
        assert resp.status_code == 400


class TestCookies:

    def test_list_cookies_empty(self, client):
        resp = client.get('/api/cookies')
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_upload_and_delete_cookie(self, client, tmp_path):
        # Upload
        resp = client.post(
            '/api/cookies',
            files={'file': ('test.txt', b'# Netscape\n.example.com\tTRUE\t/\tFALSE\t0\tsess\tabc', 'text/plain')},
        )
        assert resp.status_code == 200
        assert resp.json()['name'] == 'test.txt'

        # List
        resp = client.get('/api/cookies')
        assert resp.status_code == 200
        names = [c['name'] for c in resp.json()]
        assert 'test.txt' in names

        # Delete
        resp = client.delete('/api/cookies/test.txt')
        assert resp.status_code == 200

    def test_delete_nonexistent_cookie_returns_404(self, client):
        resp = client.delete('/api/cookies/nope.txt')
        assert resp.status_code == 404

    def test_upload_path_traversal_rejected(self, client):
        """Filename with path traversal should be sanitized."""
        resp = client.post(
            '/api/cookies',
            files={'file': ('../../etc/passwd', b'evil', 'text/plain')},
        )
        # Should either reject or sanitize to 'passwd'
        if resp.status_code == 200:
            assert resp.json()['name'] == 'passwd'
        else:
            assert resp.status_code == 400

    def test_delete_path_traversal_rejected(self, client):
        """DELETE with path traversal should return 400."""
        resp = client.delete('/api/cookies/../../etc/passwd')
        assert resp.status_code in (400, 404)


class TestIndex:

    def test_index_returns_html(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert 'VDL' in resp.text


class TestSettings:

    def test_get_and_update_settings(self, client, tmp_path):
        from video_downloader import web
        with patch.object(web, 'SETTINGS_PATH', tmp_path / 'settings.json'):
            resp = client.get('/api/settings')
            assert resp.status_code == 200
            data = resp.json()
            assert 'download_dir' in data
            assert 'effective_proxy' in data

            resp = client.post('/api/settings', json={
                'proxy': 'http://127.0.0.1:7897',
                'download_dir': '/tmp/vdl-test',
            })
            assert resp.status_code == 200
            assert resp.json()['proxy'] == 'http://127.0.0.1:7897'
            # 落盘核验
            assert (tmp_path / 'settings.json').exists()

    def test_invalid_browser_rejected(self, client, tmp_path):
        from video_downloader import web
        with patch.object(web, 'SETTINGS_PATH', tmp_path / 'settings.json'):
            resp = client.post('/api/settings', json={'browser_cookies': 'nosuch'})
            assert resp.status_code == 400


class TestFormatSelector:

    def test_empty_is_highest(self):
        from video_downloader.web import _build_format_selector
        assert _build_format_selector(None) == 'bv*+ba/b'
        assert _build_format_selector('') == 'bv*+ba/b'

    def test_format_id_direct(self):
        from video_downloader.web import _build_format_selector
        s = _build_format_selector('313')
        assert s.startswith('313+bestaudio')
        assert 'bv*+ba/b' in s

    def test_height_bounded(self):
        from video_downloader.web import _build_format_selector
        s = _build_format_selector('2160p')
        assert 'height<=2160' in s


class TestCookieSource:

    def test_browser_prefix(self):
        from video_downloader.web import _resolve_cookie_source
        cookie_file, browser = _resolve_cookie_source('browser:chrome', {})
        assert cookie_file is None
        assert browser == ('chrome',)

    def test_unknown_browser_ignored(self):
        from video_downloader.web import _resolve_cookie_source
        cookie_file, browser = _resolve_cookie_source('browser:nosuch', {})
        assert cookie_file is None and browser is None

    def test_file_cookie(self):
        from video_downloader.web import _resolve_cookie_source, state
        (state.cookie_dir / 'ck_src.txt').write_text('# Netscape')
        cookie_file, browser = _resolve_cookie_source('ck_src.txt', {})
        assert cookie_file and cookie_file.endswith('ck_src.txt') and browser is None
        (state.cookie_dir / 'ck_src.txt').unlink()
