"""
Tests for browser automation module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from video_downloader.browser_automation import BrowserAutomation
from video_downloader.browser_fingerprint import BrowserFingerprint


@pytest.fixture
def fingerprint():
    """Create a BrowserFingerprint instance."""
    return BrowserFingerprint()


@pytest.fixture
def browser_automation(fingerprint):
    """Create a BrowserAutomation instance."""
    return BrowserAutomation(fingerprint, headless=True)


class TestBrowserAutomation:
    """Test BrowserAutomation class."""
    
    def test_initialization(self, fingerprint):
        """Test BrowserAutomation initialization."""
        automation = BrowserAutomation(fingerprint, headless=True)
        
        assert automation.fingerprint == fingerprint
        assert automation.headless is True
        assert automation.browser is None
        assert automation.playwright is None
    
    def test_initialization_headless_false(self, fingerprint):
        """Test BrowserAutomation initialization with headless=False."""
        automation = BrowserAutomation(fingerprint, headless=False)
        
        assert automation.headless is False
    
    def test_get_launch_args(self, browser_automation):
        """Test browser launch arguments."""
        args = browser_automation._get_launch_args()
        
        # Check critical stealth arguments are present
        assert '--disable-blink-features=AutomationControlled' in args
        assert '--no-sandbox' in args
        assert '--disable-web-security' in args
        
        # Ensure all args are strings
        assert all(isinstance(arg, str) for arg in args)
    
    @pytest.mark.asyncio
    async def test_launch_browser_chromium(self, browser_automation):
        """Test launching chromium browser."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.chromium = mock_chromium
        
        with patch('video_downloader.browser_automation.async_playwright') as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            
            browser = await browser_automation.launch_browser('chromium')
            
            assert browser == mock_browser
            assert browser_automation.browser == mock_browser
            assert browser_automation.playwright == mock_playwright
            mock_chromium.launch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_launch_browser_firefox(self, browser_automation):
        """Test launching firefox browser."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_firefox = AsyncMock()
        mock_firefox.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.firefox = mock_firefox
        
        with patch('video_downloader.browser_automation.async_playwright') as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            
            browser = await browser_automation.launch_browser('firefox')
            
            assert browser == mock_browser
            mock_firefox.launch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_launch_browser_webkit(self, browser_automation):
        """Test launching webkit browser."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_webkit = AsyncMock()
        mock_webkit.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.webkit = mock_webkit
        
        with patch('video_downloader.browser_automation.async_playwright') as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            
            browser = await browser_automation.launch_browser('webkit')
            
            assert browser == mock_browser
            mock_webkit.launch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_launch_browser_invalid_type(self, browser_automation):
        """Test launching browser with invalid type."""
        mock_playwright = AsyncMock()
        
        with patch('video_downloader.browser_automation.async_playwright') as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            
            with pytest.raises(ValueError, match="Unsupported browser type"):
                await browser_automation.launch_browser('invalid')
    
    @pytest.mark.asyncio
    async def test_launch_browser_already_launched(self, browser_automation):
        """Test launching browser when already launched."""
        mock_browser = AsyncMock()
        browser_automation.browser = mock_browser
        
        browser = await browser_automation.launch_browser()
        
        assert browser == mock_browser
    
    @pytest.mark.asyncio
    async def test_create_stealth_page(self, browser_automation):
        """Test creating stealth page."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        
        browser_automation.browser = mock_browser
        
        with patch.object(browser_automation, '_inject_stealth_scripts', new=AsyncMock()):
            page = await browser_automation.create_stealth_page('douyin')
            
            assert page == mock_page
            mock_browser.new_context.assert_called_once()
            
            # Check context was created with correct parameters
            call_kwargs = mock_browser.new_context.call_args[1]
            assert 'user_agent' in call_kwargs
            assert 'viewport' in call_kwargs
            assert 'locale' in call_kwargs
            assert 'timezone_id' in call_kwargs
    
    @pytest.mark.asyncio
    async def test_create_stealth_page_with_context(self, browser_automation):
        """Test creating stealth page with provided context."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_context.new_page = AsyncMock(return_value=mock_page)
        browser_automation.browser = mock_browser
        
        with patch.object(browser_automation, '_inject_stealth_scripts', new=AsyncMock()):
            page = await browser_automation.create_stealth_page('douyin', context=mock_context)
            
            assert page == mock_page
            mock_browser.new_context.assert_not_called()
            mock_context.new_page.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_inject_stealth_scripts(self, browser_automation):
        """Test stealth script injection."""
        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        
        await browser_automation._inject_stealth_scripts(mock_page)
        
        mock_page.add_init_script.assert_called_once()
        
        # Check script contains critical anti-detection code
        script = mock_page.add_init_script.call_args[0][0]
        assert 'webdriver' in script
        assert 'chrome' in script
        assert 'plugins' in script
        assert 'languages' in script
    
    @pytest.mark.asyncio
    async def test_navigate_with_delay(self, browser_automation):
        """Test navigation with human-like delay."""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        
        with patch.object(browser_automation, 'simulate_human_behavior', new=AsyncMock()):
            with patch('video_downloader.browser_automation.asyncio.sleep', new=AsyncMock()):
                await browser_automation.navigate_with_delay(mock_page, 'https://example.com')
                
                mock_page.goto.assert_called_once_with(
                    'https://example.com',
                    wait_until='domcontentloaded',
                    timeout=30000
                )
    
    @pytest.mark.asyncio
    async def test_navigate_with_delay_custom_wait(self, browser_automation):
        """Test navigation with custom wait condition."""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        
        with patch.object(browser_automation, 'simulate_human_behavior', new=AsyncMock()):
            with patch('video_downloader.browser_automation.asyncio.sleep', new=AsyncMock()):
                await browser_automation.navigate_with_delay(
                    mock_page,
                    'https://example.com',
                    wait_until='networkidle'
                )
                
                call_kwargs = mock_page.goto.call_args[1]
                assert call_kwargs['wait_until'] == 'networkidle'
    
    @pytest.mark.asyncio
    async def test_simulate_human_behavior(self, browser_automation):
        """Test human behavior simulation."""
        mock_page = AsyncMock()
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()
        mock_page.evaluate = AsyncMock()
        
        with patch('video_downloader.browser_automation.asyncio.sleep', new=AsyncMock()):
            with patch('video_downloader.browser_automation.random.uniform', return_value=1.0):
                with patch('video_downloader.browser_automation.random.randint', return_value=100):
                    await browser_automation.simulate_human_behavior(mock_page)
                    
                    # Check mouse movement was called
                    mock_page.mouse.move.assert_called_once()
                    
                    # Check scroll was called
                    mock_page.evaluate.assert_called_once()
                    assert 'scrollBy' in mock_page.evaluate.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_simulate_human_behavior_error_handling(self, browser_automation):
        """Test human behavior simulation handles errors gracefully."""
        mock_page = AsyncMock()
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock(side_effect=Exception("Mouse error"))
        mock_page.evaluate = AsyncMock(side_effect=Exception("Scroll error"))
        
        with patch('video_downloader.browser_automation.asyncio.sleep', new=AsyncMock()):
            # Should not raise exception
            await browser_automation.simulate_human_behavior(mock_page)
    
    @pytest.mark.asyncio
    async def test_close(self, browser_automation):
        """Test closing browser."""
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        mock_playwright = AsyncMock()
        mock_playwright.stop = AsyncMock()
        
        browser_automation.browser = mock_browser
        browser_automation.playwright = mock_playwright
        
        await browser_automation.close()
        
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
        assert browser_automation.browser is None
        assert browser_automation.playwright is None
    
    @pytest.mark.asyncio
    async def test_close_no_browser(self, browser_automation):
        """Test closing when no browser is launched."""
        # Should not raise exception
        await browser_automation.close()
    
    @pytest.mark.asyncio
    async def test_context_manager(self, browser_automation):
        """Test async context manager."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.chromium = mock_chromium
        mock_browser.close = AsyncMock()
        mock_playwright.stop = AsyncMock()
        
        with patch('video_downloader.browser_automation.async_playwright') as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            
            async with browser_automation as ba:
                assert ba.browser == mock_browser
            
            # Check cleanup was called
            mock_browser.close.assert_called_once()
            mock_playwright.stop.assert_called_once()


class TestStealthFeatures:
    """Test stealth and anti-detection features."""
    
    def test_launch_args_disable_automation(self, browser_automation):
        """Test that automation flags are disabled."""
        args = browser_automation._get_launch_args()
        
        # Critical: AutomationControlled should be disabled
        assert any('AutomationControlled' in arg for arg in args)
    
    def test_launch_args_sandbox_disabled(self, browser_automation):
        """Test that sandbox is disabled for compatibility."""
        args = browser_automation._get_launch_args()
        
        assert '--no-sandbox' in args
        assert '--disable-setuid-sandbox' in args
    
    @pytest.mark.asyncio
    async def test_stealth_script_hides_webdriver(self, browser_automation):
        """Test that stealth script hides webdriver property."""
        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        
        await browser_automation._inject_stealth_scripts(mock_page)
        
        script = mock_page.add_init_script.call_args[0][0]
        
        # Check webdriver is hidden
        assert "navigator, 'webdriver'" in script
        assert 'undefined' in script
    
    @pytest.mark.asyncio
    async def test_stealth_script_adds_chrome_object(self, browser_automation):
        """Test that stealth script adds chrome object."""
        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        
        await browser_automation._inject_stealth_scripts(mock_page)
        
        script = mock_page.add_init_script.call_args[0][0]
        
        # Check chrome object is added
        assert 'window.chrome' in script
        assert 'runtime' in script
    
    @pytest.mark.asyncio
    async def test_stealth_script_mocks_plugins(self, browser_automation):
        """Test that stealth script mocks plugins."""
        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        
        await browser_automation._inject_stealth_scripts(mock_page)
        
        script = mock_page.add_init_script.call_args[0][0]
        
        # Check plugins are mocked
        assert "navigator, 'plugins'" in script
    
    @pytest.mark.asyncio
    async def test_fingerprint_applied_to_context(self, browser_automation):
        """Test that fingerprint is applied to browser context."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        
        browser_automation.browser = mock_browser
        
        with patch.object(browser_automation, '_inject_stealth_scripts', new=AsyncMock()):
            await browser_automation.create_stealth_page('douyin')
            
            # Check fingerprint was used
            call_kwargs = mock_browser.new_context.call_args[1]
            assert 'user_agent' in call_kwargs
            assert 'viewport' in call_kwargs
            assert call_kwargs['viewport']['width'] > 0
            assert call_kwargs['viewport']['height'] > 0


class TestHumanBehaviorSimulation:
    """Test human behavior simulation features."""
    
    @pytest.mark.asyncio
    async def test_random_delays_applied(self, browser_automation):
        """Test that random delays are applied."""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        
        sleep_calls = []
        
        async def mock_sleep(duration):
            sleep_calls.append(duration)
        
        with patch.object(browser_automation, 'simulate_human_behavior', new=AsyncMock()):
            with patch('video_downloader.browser_automation.asyncio.sleep', new=mock_sleep):
                await browser_automation.navigate_with_delay(mock_page, 'https://example.com')
                
                # Check that sleep was called (delay before navigation)
                assert len(sleep_calls) > 0
    
    @pytest.mark.asyncio
    async def test_mouse_movement_simulated(self, browser_automation):
        """Test that mouse movement is simulated."""
        mock_page = AsyncMock()
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()
        mock_page.evaluate = AsyncMock()
        
        with patch('video_downloader.browser_automation.asyncio.sleep', new=AsyncMock()):
            await browser_automation.simulate_human_behavior(mock_page)
            
            # Check mouse was moved
            mock_page.mouse.move.assert_called_once()
            
            # Check coordinates are reasonable
            x, y = mock_page.mouse.move.call_args[0]
            assert 0 <= x <= 1000
            assert 0 <= y <= 1000
    
    @pytest.mark.asyncio
    async def test_scroll_simulated(self, browser_automation):
        """Test that scrolling is simulated."""
        mock_page = AsyncMock()
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()
        mock_page.evaluate = AsyncMock()
        
        with patch('video_downloader.browser_automation.asyncio.sleep', new=AsyncMock()):
            await browser_automation.simulate_human_behavior(mock_page)
            
            # Check scroll was executed
            mock_page.evaluate.assert_called_once()
            script = mock_page.evaluate.call_args[0][0]
            assert 'scrollBy' in script
