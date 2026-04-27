#!/usr/bin/env python
"""
Integration test script to verify the video downloader system.
"""

import asyncio
from video_downloader import VideoDownloader, DownloadOptions


async def test_system():
    """Test the video downloader system."""
    print("=" * 60)
    print("Video Downloader System Integration Test")
    print("=" * 60)
    
    # Test 1: Initialize downloader
    print("\n✓ Test 1: Initialize VideoDownloader")
    downloader = VideoDownloader()
    print(f"  Downloader initialized successfully")
    
    # Test 2: List supported platforms
    print("\n✓ Test 2: List supported platforms")
    platforms = downloader.list_supported_platforms()
    print(f"  Supported platforms: {', '.join(platforms)}")
    assert len(platforms) == 3, f"Expected 3 platforms, got {len(platforms)}"
    assert 'bilibili' in platforms
    assert 'douyin' in platforms
    assert 'tiktok' in platforms
    
    # Test 3: URL validation
    print("\n✓ Test 3: URL validation")
    try:
        downloader._validate_url("https://www.bilibili.com/video/BV123")
        print("  Valid URL accepted")
    except Exception as e:
        print(f"  ✗ URL validation failed: {e}")
        return False
    
    try:
        downloader._validate_url("")
        print("  ✗ Empty URL should have been rejected")
        return False
    except Exception:
        print("  Empty URL correctly rejected")
    
    # Test 4: Platform detection
    print("\n✓ Test 4: Platform detection")
    test_urls = {
        'bilibili': 'https://www.bilibili.com/video/BV1xx411c7mD',
        'douyin': 'https://www.douyin.com/video/123456',
        'tiktok': 'https://www.tiktok.com/@user/video/123456',
    }
    
    for platform, url in test_urls.items():
        try:
            extractor = downloader._get_extractor_for_url(url)
            detected_platform = extractor.get_platform_name()
            print(f"  {url[:50]}... -> {detected_platform}")
            assert detected_platform == platform, f"Expected {platform}, got {detected_platform}"
        except Exception as e:
            print(f"  ✗ Platform detection failed for {platform}: {e}")
            return False
    
    # Test 5: Component initialization
    print("\n✓ Test 5: Component initialization")
    assert downloader.platform_manager is not None, "PlatformManager not initialized"
    assert downloader.cookie_store is not None, "CookieStore not initialized"
    assert downloader.fingerprint is not None, "BrowserFingerprint not initialized"
    assert downloader.download_manager is not None, "DownloadManager not initialized"
    print("  All components initialized")
    
    # Test 6: Configuration
    print("\n✓ Test 6: Configuration")
    config = downloader.config
    print(f"  Output dir: {config.output_dir}")
    print(f"  Max retries: {config.max_retries}")
    print(f"  Timeout: {config.timeout}s")
    print(f"  Headless: {config.headless}")
    
    print("\n" + "=" * 60)
    print("✓ All integration tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_system())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
