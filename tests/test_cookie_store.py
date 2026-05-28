"""
Tests for CookieStore.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from video_downloader.cookie_store import CookieStore
from video_downloader.models import Cookie


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def cookie_store(temp_storage):
    """Create CookieStore instance."""
    return CookieStore(temp_storage)


@pytest.fixture
def sample_cookies():
    """Create sample cookies."""
    return [
        Cookie(
            name="sessionid",
            value="abc123",
            domain=".example.com",
            path="/",
            expires=datetime.now() + timedelta(days=30),
            secure=True,
            http_only=True
        ),
        Cookie(
            name="token",
            value="xyz789",
            domain=".example.com",
            path="/",
            expires=None,  # Session cookie
            secure=False,
            http_only=False
        )
    ]


def test_cookie_store_initialization(temp_storage):
    """Test CookieStore initialization."""
    store = CookieStore(temp_storage)
    
    assert store.storage_path == Path(temp_storage)
    assert store.storage_path.exists()
    assert isinstance(store.cookies, dict)


def test_save_and_load_cookies(cookie_store, sample_cookies):
    """Test saving and loading cookies."""
    platform = "test_platform"
    
    # Save cookies
    cookie_store.save_cookies(platform, sample_cookies)
    
    # Load cookies
    loaded = cookie_store.load_cookies(platform)
    
    assert len(loaded) == 2
    assert loaded[0].name == "sessionid"
    assert loaded[0].value == "abc123"
    assert loaded[1].name == "token"


def test_load_nonexistent_cookies(cookie_store):
    """Test loading cookies for non-existent platform."""
    cookies = cookie_store.load_cookies("nonexistent")
    
    assert cookies == []


def test_cookie_caching(cookie_store, sample_cookies):
    """Test that cookies are cached in memory."""
    platform = "test"
    
    cookie_store.save_cookies(platform, sample_cookies)
    
    # First load - from file
    cookies1 = cookie_store.load_cookies(platform)
    
    # Second load - from cache
    cookies2 = cookie_store.load_cookies(platform)
    
    assert cookies1 is cookies2  # Same object reference


def test_validate_cookies_valid(cookie_store, sample_cookies):
    """Test validating valid cookies."""
    assert cookie_store.validate_cookies(sample_cookies) is True


def test_validate_cookies_invalid_type(cookie_store):
    """Test validating invalid cookie type."""
    assert cookie_store.validate_cookies("not a list") is False
    assert cookie_store.validate_cookies([{"name": "test"}]) is False


def test_validate_cookies_missing_fields(cookie_store):
    """Test validating cookies with missing fields."""
    invalid_cookie = Cookie(
        name="",  # Empty name
        value="value",
        domain=".example.com",
        path="/",
        expires=None,
        secure=False,
        http_only=False
    )
    
    assert cookie_store.validate_cookies([invalid_cookie]) is False


def test_is_expired_session_cookie(cookie_store):
    """Test that session cookies never expire."""
    cookie = Cookie(
        name="session",
        value="value",
        domain=".example.com",
        path="/",
        expires=None,
        secure=False,
        http_only=False
    )
    
    assert cookie_store.is_expired(cookie) is False


def test_is_expired_future_cookie(cookie_store):
    """Test cookie with future expiration."""
    cookie = Cookie(
        name="future",
        value="value",
        domain=".example.com",
        path="/",
        expires=datetime.now() + timedelta(days=30),
        secure=False,
        http_only=False
    )
    
    assert cookie_store.is_expired(cookie) is False


def test_is_expired_past_cookie(cookie_store):
    """Test cookie with past expiration."""
    cookie = Cookie(
        name="expired",
        value="value",
        domain=".example.com",
        path="/",
        expires=datetime.now() - timedelta(days=1),
        secure=False,
        http_only=False
    )
    
    assert cookie_store.is_expired(cookie) is True


def test_remove_expired_cookies(cookie_store):
    """Test removing expired cookies."""
    platform = "test"
    
    cookies = [
        Cookie(
            name="valid",
            value="value1",
            domain=".example.com",
            path="/",
            expires=datetime.now() + timedelta(days=30),
            secure=False,
            http_only=False
        ),
        Cookie(
            name="expired",
            value="value2",
            domain=".example.com",
            path="/",
            expires=datetime.now() - timedelta(days=1),
            secure=False,
            http_only=False
        )
    ]
    
    cookie_store.save_cookies(platform, cookies)
    
    removed = cookie_store.remove_expired_cookies(platform)
    
    assert removed == 1
    
    remaining = cookie_store.load_cookies(platform)
    assert len(remaining) == 1
    assert remaining[0].name == "valid"


def test_clear_cookies(cookie_store, sample_cookies):
    """Test clearing all cookies for a platform."""
    platform = "test"
    
    cookie_store.save_cookies(platform, sample_cookies)
    assert len(cookie_store.load_cookies(platform)) == 2
    
    cookie_store.clear_cookies(platform)
    
    assert len(cookie_store.load_cookies(platform)) == 0


def test_get_cookie_dict(cookie_store, sample_cookies):
    """Test getting cookies as dictionary."""
    platform = "test"
    
    cookie_store.save_cookies(platform, sample_cookies)
    
    cookie_dict = cookie_store.get_cookie_dict(platform)
    
    assert cookie_dict == {
        "sessionid": "abc123",
        "token": "xyz789"
    }


def test_get_cookie_string(cookie_store, sample_cookies):
    """Test getting cookies as string."""
    platform = "test"
    
    cookie_store.save_cookies(platform, sample_cookies)
    
    cookie_string = cookie_store.get_cookie_string(platform)
    
    assert "sessionid=abc123" in cookie_string
    assert "token=xyz789" in cookie_string
    assert "; " in cookie_string


def test_import_from_netscape(cookie_store, temp_storage):
    """Test importing cookies from Netscape format."""
    # Create a Netscape format cookie file
    netscape_file = Path(temp_storage) / "cookies.txt"
    
    content = """# Netscape HTTP Cookie File
.example.com\tTRUE\t/\tTRUE\t1735689600\tsessionid\tabc123
.example.com\tTRUE\t/\tFALSE\t0\ttoken\txyz789
"""
    
    netscape_file.write_text(content)
    
    # Import cookies
    cookie_store.import_from_netscape(str(netscape_file), "test")
    
    # Verify imported cookies
    cookies = cookie_store.load_cookies("test")
    
    assert len(cookies) == 2
    assert cookies[0].name == "sessionid"
    assert cookies[0].value == "abc123"
    assert cookies[0].secure is True


def test_import_from_netscape_file_not_found(cookie_store):
    """Test importing from non-existent file."""
    with pytest.raises(FileNotFoundError):
        cookie_store.import_from_netscape("nonexistent.txt", "test")


def test_save_invalid_cookies(cookie_store):
    """Test saving invalid cookies."""
    invalid_cookies = [{"name": "test"}]  # Not Cookie objects
    
    with pytest.raises(ValueError, match="Invalid cookies"):
        cookie_store.save_cookies("test", invalid_cookies)
