"""
Browser fingerprint generation and management.
"""

import random
from typing import Dict, Tuple
from .models import Fingerprint
from .logger import logger


class BrowserFingerprint:
    """
    Generates realistic browser fingerprints to avoid detection.
    
    Provides:
    - User-Agent generation and rotation
    - Screen resolution simulation
    - Platform-specific headers
    - Complete fingerprint generation
    """
    
    # Common User-Agent strings for different browsers
    USER_AGENTS = {
        'chrome_windows': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        ],
        'chrome_mac': [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        ],
        'firefox_windows': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        ],
        'safari_mac': [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ],
    }
    
    # Common screen resolutions
    SCREEN_RESOLUTIONS = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (2560, 1440),
    ]
    
    def __init__(self):
        """Initialize browser fingerprint generator."""
        logger.info("BrowserFingerprint initialized")
    
    def generate_fingerprint(self, platform: str = "douyin") -> Fingerprint:
        """
        Generate a complete browser fingerprint for a platform.
        
        Args:
            platform: Platform name (e.g., "douyin", "bilibili", "tiktok")
            
        Returns:
            Complete fingerprint object
        """
        user_agent = self.get_user_agent()
        screen_width, screen_height = self._get_screen_resolution()
        
        # Determine platform string from user agent
        if "Windows" in user_agent:
            platform_str = "Win32"
        elif "Macintosh" in user_agent:
            platform_str = "MacIntel"
        else:
            platform_str = "Linux x86_64"
        
        # Get language based on platform
        language = self._get_language(platform)
        
        # Get timezone
        timezone = self._get_timezone(platform)
        
        # Generate headers
        headers = self.get_headers(platform, user_agent=user_agent)
        
        fingerprint = Fingerprint(
            user_agent=user_agent,
            platform=platform_str,
            screen_width=screen_width,
            screen_height=screen_height,
            color_depth=24,
            language=language,
            timezone=timezone,
            headers=headers
        )
        
        logger.debug(f"Generated fingerprint for {platform}: {user_agent[:50]}...")
        return fingerprint
    
    def get_user_agent(self, browser_type: str = 'chrome') -> str:
        """
        Get a realistic User-Agent string.
        
        Args:
            browser_type: Browser type ('chrome', 'firefox', 'safari')
            
        Returns:
            User-Agent string
        """
        # Select appropriate user agent pool
        if browser_type == 'chrome':
            pool = self.USER_AGENTS['chrome_windows'] + self.USER_AGENTS['chrome_mac']
        elif browser_type == 'firefox':
            pool = self.USER_AGENTS['firefox_windows']
        elif browser_type == 'safari':
            pool = self.USER_AGENTS['safari_mac']
        else:
            # Default to Chrome
            pool = self.USER_AGENTS['chrome_windows']
        
        return random.choice(pool)
    
    def get_headers(
        self,
        platform: str,
        referer: str = None,
        user_agent: str = None
    ) -> Dict[str, str]:
        """
        Generate complete HTTP headers for a platform.
        
        Args:
            platform: Platform name
            referer: Optional referer URL
            user_agent: Optional user agent (generated if not provided)
            
        Returns:
            Dictionary of HTTP headers
        """
        if user_agent is None:
            user_agent = self.get_user_agent()
        
        # Base headers common to all platforms
        headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        # Platform-specific headers
        if platform == 'douyin':
            headers.update({
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Origin': 'https://www.douyin.com',
                'Referer': referer or 'https://www.douyin.com/',
            })
        elif platform == 'bilibili':
            headers.update({
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Origin': 'https://www.bilibili.com',
                'Referer': referer or 'https://www.bilibili.com/',
            })
        elif platform == 'tiktok':
            headers.update({
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://www.tiktok.com',
                'Referer': referer or 'https://www.tiktok.com/',
            })
        else:
            # Generic headers
            headers.update({
                'Accept-Language': 'en-US,en;q=0.9',
            })
        
        return headers
    
    def _get_screen_resolution(self) -> Tuple[int, int]:
        """
        Get a realistic screen resolution.
        
        Returns:
            Tuple of (width, height)
        """
        return random.choice(self.SCREEN_RESOLUTIONS)
    
    def _get_language(self, platform: str) -> str:
        """
        Get appropriate language for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Language code
        """
        if platform in ['douyin', 'bilibili']:
            return 'zh-CN'
        else:
            return 'en-US'
    
    def _get_timezone(self, platform: str) -> str:
        """
        Get appropriate timezone for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Timezone string
        """
        if platform in ['douyin', 'bilibili']:
            return 'Asia/Shanghai'
        else:
            return 'America/New_York'
    
    def rotate_user_agent(self) -> str:
        """
        Get a new random user agent (for rotation).
        
        Returns:
            New User-Agent string
        """
        all_agents = []
        for agents in self.USER_AGENTS.values():
            all_agents.extend(agents)
        
        return random.choice(all_agents)
