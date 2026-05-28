"""
Browser automation using Playwright for anti-bot detection bypass.
"""

import asyncio
import random
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from .browser_fingerprint import BrowserFingerprint
from .logger import logger


class BrowserAutomation:
    """
    Manages browser automation with stealth features.
    
    Features:
    - Playwright browser management
    - Automation flag hiding
    - Anti-detection script injection
    - Human behavior simulation
    """
    
    def __init__(self, fingerprint: BrowserFingerprint, headless: bool = True):
        """
        Initialize browser automation.
        
        Args:
            fingerprint: BrowserFingerprint instance
            headless: Whether to run browser in headless mode
        """
        self.fingerprint = fingerprint
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
        
        logger.info(f"BrowserAutomation initialized (headless={headless})")
    
    async def launch_browser(self, browser_type: str = 'chromium') -> Browser:
        """
        Launch browser with stealth configuration.
        
        Args:
            browser_type: Browser type ('chromium', 'firefox', 'webkit')
            
        Returns:
            Browser instance
        """
        if self.browser is not None:
            logger.debug("Browser already launched, returning existing instance")
            return self.browser
        
        logger.info(f"Launching {browser_type} browser...")
        
        self.playwright = await async_playwright().start()
        
        # Get browser launcher
        if browser_type == 'chromium':
            browser_launcher = self.playwright.chromium
        elif browser_type == 'firefox':
            browser_launcher = self.playwright.firefox
        elif browser_type == 'webkit':
            browser_launcher = self.playwright.webkit
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        # Launch with stealth arguments
        self.browser = await browser_launcher.launch(
            headless=self.headless,
            args=self._get_launch_args()
        )
        
        logger.info("Browser launched successfully")
        return self.browser
    
    async def create_stealth_page(
        self,
        platform: str = 'douyin',
        context: Optional[BrowserContext] = None
    ) -> Page:
        """
        Create a stealth page with anti-detection measures.
        
        Args:
            platform: Platform name for fingerprint generation
            context: Optional browser context (creates new if not provided)
            
        Returns:
            Configured page instance
        """
        if self.browser is None:
            await self.launch_browser()
        
        # Generate fingerprint for platform
        fp = self.fingerprint.generate_fingerprint(platform)
        
        # Create context if not provided
        if context is None:
            context = await self.browser.new_context(
                user_agent=fp.user_agent,
                viewport={
                    'width': fp.screen_width,
                    'height': fp.screen_height
                },
                locale=fp.language,
                timezone_id=fp.timezone,
                color_scheme='light',
                device_scale_factor=1,
            )
        
        # Create page
        page = await context.new_page()
        
        # Inject stealth scripts
        await self._inject_stealth_scripts(page)
        
        logger.info(f"Created stealth page for platform: {platform}")
        return page
    
    async def navigate_with_delay(
        self,
        page: Page,
        url: str,
        wait_until: str = 'domcontentloaded'
    ) -> None:
        """
        Navigate to URL with human-like delay.
        
        Args:
            page: Page instance
            url: URL to navigate to
            wait_until: Wait condition ('load', 'domcontentloaded', 'networkidle')
        """
        # Random delay before navigation
        delay = random.uniform(0.5, 1.5)
        await asyncio.sleep(delay)
        
        logger.debug(f"Navigating to: {url}")
        await page.goto(url, wait_until=wait_until, timeout=30000)
        
        # Simulate human behavior after page load
        await self.simulate_human_behavior(page)
    
    async def simulate_human_behavior(self, page: Page) -> None:
        """
        Simulate human-like behavior on page.
        
        Args:
            page: Page instance
        """
        # Random delay
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Random mouse movement
        try:
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
        except Exception as e:
            logger.debug(f"Mouse movement failed: {e}")
        
        # Random scroll
        try:
            scroll_amount = random.randint(100, 300)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        except Exception as e:
            logger.debug(f"Scroll failed: {e}")
        
        # Another random delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        logger.debug("Simulated human behavior")
    
    def _get_launch_args(self) -> List[str]:
        """
        Get browser launch arguments for stealth.
        
        Returns:
            List of launch arguments
        """
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
        ]
    
    async def _inject_stealth_scripts(self, page: Page) -> None:
        """
        Inject anti-detection scripts into page.
        
        Args:
            page: Page instance
        """
        stealth_script = """
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Add chrome object
        window.chrome = {
            runtime: {}
        };
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        await page.add_init_script(stealth_script)
        logger.debug("Injected stealth scripts")
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self.browser is not None:
            await self.browser.close()
            self.browser = None
            logger.info("Browser closed")
        
        if self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None
            logger.info("Playwright stopped")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.launch_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
