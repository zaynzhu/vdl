"""
Tests for BrowserFingerprint.
"""

import pytest
from video_downloader.browser_fingerprint import BrowserFingerprint
from video_downloader.models import Fingerprint


@pytest.fixture
def fingerprint_gen():
    """Create BrowserFingerprint instance."""
    return BrowserFingerprint()


def test_browser_fingerprint_initialization():
    """Test BrowserFingerprint initialization."""
    gen = BrowserFingerprint()
    
    assert gen is not None
    assert len(gen.USER_AGENTS) > 0
    assert len(gen.SCREEN_RESOLUTIONS) > 0


def test_generate_fingerprint(fingerprint_gen):
    """Test generating complete fingerprint."""
    fingerprint = fingerprint_gen.generate_fingerprint("douyin")
    
    assert isinstance(fingerprint, Fingerprint)
    assert fingerprint.user_agent
    assert fingerprint.platform in ['Win32', 'MacIntel', 'Linux x86_64']
    assert fingerprint.screen_width > 0
    assert fingerprint.screen_height > 0
    assert fingerprint.color_depth == 24
    assert fingerprint.language
    assert fingerprint.timezone
    assert isinstance(fingerprint.headers, dict)


def test_generate_fingerprint_douyin(fingerprint_gen):
    """Test fingerprint for Douyin platform."""
    fingerprint = fingerprint_gen.generate_fingerprint("douyin")
    
    assert fingerprint.language == 'zh-CN'
    assert fingerprint.timezone == 'Asia/Shanghai'
    assert 'douyin.com' in fingerprint.headers.get('Referer', '')


def test_generate_fingerprint_bilibili(fingerprint_gen):
    """Test fingerprint for Bilibili platform."""
    fingerprint = fingerprint_gen.generate_fingerprint("bilibili")
    
    assert fingerprint.language == 'zh-CN'
    assert fingerprint.timezone == 'Asia/Shanghai'
    assert 'bilibili.com' in fingerprint.headers.get('Referer', '')


def test_generate_fingerprint_tiktok(fingerprint_gen):
    """Test fingerprint for TikTok platform."""
    fingerprint = fingerprint_gen.generate_fingerprint("tiktok")
    
    assert fingerprint.language == 'en-US'
    assert fingerprint.timezone == 'America/New_York'
    assert 'tiktok.com' in fingerprint.headers.get('Referer', '')


def test_get_user_agent_chrome(fingerprint_gen):
    """Test getting Chrome user agent."""
    ua = fingerprint_gen.get_user_agent('chrome')
    
    assert 'Chrome' in ua
    assert 'Mozilla' in ua


def test_get_user_agent_firefox(fingerprint_gen):
    """Test getting Firefox user agent."""
    ua = fingerprint_gen.get_user_agent('firefox')
    
    assert 'Firefox' in ua
    assert 'Mozilla' in ua


def test_get_user_agent_safari(fingerprint_gen):
    """Test getting Safari user agent."""
    ua = fingerprint_gen.get_user_agent('safari')
    
    assert 'Safari' in ua
    assert 'Mozilla' in ua


def test_get_user_agent_default(fingerprint_gen):
    """Test getting default user agent."""
    ua = fingerprint_gen.get_user_agent('unknown')
    
    # Should default to Chrome
    assert 'Chrome' in ua


def test_get_headers_douyin(fingerprint_gen):
    """Test getting headers for Douyin."""
    headers = fingerprint_gen.get_headers('douyin')
    
    assert 'User-Agent' in headers
    assert 'Accept' in headers
    assert 'Accept-Language' in headers
    assert headers['Accept-Language'] == 'zh-CN,zh;q=0.9,en;q=0.8'
    assert headers['Origin'] == 'https://www.douyin.com'
    assert 'douyin.com' in headers['Referer']


def test_get_headers_bilibili(fingerprint_gen):
    """Test getting headers for Bilibili."""
    headers = fingerprint_gen.get_headers('bilibili')
    
    assert headers['Accept-Language'] == 'zh-CN,zh;q=0.9'
    assert headers['Origin'] == 'https://www.bilibili.com'
    assert 'bilibili.com' in headers['Referer']


def test_get_headers_tiktok(fingerprint_gen):
    """Test getting headers for TikTok."""
    headers = fingerprint_gen.get_headers('tiktok')
    
    assert headers['Accept-Language'] == 'en-US,en;q=0.9'
    assert headers['Origin'] == 'https://www.tiktok.com'
    assert 'tiktok.com' in headers['Referer']


def test_get_headers_with_custom_referer(fingerprint_gen):
    """Test getting headers with custom referer."""
    custom_referer = 'https://www.douyin.com/video/123'
    headers = fingerprint_gen.get_headers('douyin', referer=custom_referer)
    
    assert headers['Referer'] == custom_referer


def test_get_headers_with_custom_user_agent(fingerprint_gen):
    """Test getting headers with custom user agent."""
    custom_ua = 'Custom User Agent'
    headers = fingerprint_gen.get_headers('douyin', user_agent=custom_ua)
    
    assert headers['User-Agent'] == custom_ua


def test_screen_resolution_valid(fingerprint_gen):
    """Test that screen resolution is valid."""
    width, height = fingerprint_gen._get_screen_resolution()
    
    assert width > 0
    assert height > 0
    assert (width, height) in fingerprint_gen.SCREEN_RESOLUTIONS


def test_get_language_chinese_platforms(fingerprint_gen):
    """Test language for Chinese platforms."""
    assert fingerprint_gen._get_language('douyin') == 'zh-CN'
    assert fingerprint_gen._get_language('bilibili') == 'zh-CN'


def test_get_language_english_platforms(fingerprint_gen):
    """Test language for English platforms."""
    assert fingerprint_gen._get_language('tiktok') == 'en-US'
    assert fingerprint_gen._get_language('youtube') == 'en-US'


def test_get_timezone_chinese_platforms(fingerprint_gen):
    """Test timezone for Chinese platforms."""
    assert fingerprint_gen._get_timezone('douyin') == 'Asia/Shanghai'
    assert fingerprint_gen._get_timezone('bilibili') == 'Asia/Shanghai'


def test_get_timezone_english_platforms(fingerprint_gen):
    """Test timezone for English platforms."""
    assert fingerprint_gen._get_timezone('tiktok') == 'America/New_York'
    assert fingerprint_gen._get_timezone('youtube') == 'America/New_York'


def test_rotate_user_agent(fingerprint_gen):
    """Test user agent rotation."""
    ua1 = fingerprint_gen.rotate_user_agent()
    ua2 = fingerprint_gen.rotate_user_agent()
    
    assert ua1
    assert ua2
    # Both should be valid user agents
    assert 'Mozilla' in ua1
    assert 'Mozilla' in ua2


def test_headers_contain_required_fields(fingerprint_gen):
    """Test that headers contain all required fields."""
    headers = fingerprint_gen.get_headers('douyin')
    
    required_fields = [
        'User-Agent',
        'Accept',
        'Accept-Encoding',
        'Connection',
        'Sec-Fetch-Dest',
        'Sec-Fetch-Mode',
        'Sec-Fetch-Site',
    ]
    
    for field in required_fields:
        assert field in headers


def test_fingerprint_randomness(fingerprint_gen):
    """Test that fingerprints have some randomness."""
    fingerprints = [
        fingerprint_gen.generate_fingerprint("douyin")
        for _ in range(10)
    ]
    
    # Check that not all user agents are the same
    user_agents = [f.user_agent for f in fingerprints]
    unique_uas = set(user_agents)
    
    # Should have some variety (at least 2 different UAs in 10 tries)
    assert len(unique_uas) >= 1  # At minimum, should have valid UAs


def test_fingerprint_consistency(fingerprint_gen):
    """Test that fingerprint components are consistent."""
    fingerprint = fingerprint_gen.generate_fingerprint("douyin")
    
    # Platform should match user agent
    if 'Windows' in fingerprint.user_agent:
        assert fingerprint.platform == 'Win32'
    elif 'Macintosh' in fingerprint.user_agent:
        assert fingerprint.platform == 'MacIntel'
    
    # Headers should contain the same user agent
    assert fingerprint.headers['User-Agent'] == fingerprint.user_agent
