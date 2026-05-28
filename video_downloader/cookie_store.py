"""
Cookie management and storage.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from .models import Cookie
from .logger import logger


class CookieStore:
    """
    Manages cookies for different platforms.
    
    Supports:
    - Multi-platform cookie isolation
    - Persistent storage
    - Netscape format import
    - Cookie validation
    """
    
    def __init__(self, storage_path: str):
        """
        Initialize cookie store.
        
        Args:
            storage_path: Directory path for cookie storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cookie cache: {platform: [Cookie]}
        self.cookies: Dict[str, List[Cookie]] = {}
        
        logger.info(f"CookieStore initialized at: {self.storage_path}")
    
    def load_cookies(self, platform: str) -> List[Cookie]:
        """
        Load cookies for a specific platform.
        
        Args:
            platform: Platform name (e.g., "douyin", "bilibili")
            
        Returns:
            List of cookies for the platform
        """
        # Check cache first
        if platform in self.cookies:
            logger.debug(f"Loading cookies from cache for: {platform}")
            return self.cookies[platform]
        
        # Load from file
        cookie_file = self.storage_path / f"{platform}.json"
        
        if not cookie_file.exists():
            logger.debug(f"No cookie file found for: {platform}")
            return []
        
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cookies = []
            for item in data:
                # Parse datetime if present
                expires = None
                if item.get('expires'):
                    try:
                        expires = datetime.fromisoformat(item['expires'])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid expires format: {item.get('expires')}")
                
                cookie = Cookie(
                    name=item['name'],
                    value=item['value'],
                    domain=item['domain'],
                    path=item['path'],
                    expires=expires,
                    secure=item.get('secure', False),
                    http_only=item.get('http_only', False)
                )
                cookies.append(cookie)
            
            # Cache the cookies
            self.cookies[platform] = cookies
            
            logger.info(f"Loaded {len(cookies)} cookies for: {platform}")
            return cookies
            
        except Exception as e:
            logger.error(f"Failed to load cookies for {platform}: {e}")
            return []
    
    def save_cookies(self, platform: str, cookies: List[Cookie]) -> None:
        """
        Save cookies for a specific platform.
        
        Args:
            platform: Platform name
            cookies: List of cookies to save
        """
        if not self.validate_cookies(cookies):
            logger.error(f"Invalid cookies provided for: {platform}")
            raise ValueError("Invalid cookies")
        
        cookie_file = self.storage_path / f"{platform}.json"
        
        try:
            # Convert cookies to dict
            data = []
            for cookie in cookies:
                item = {
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'expires': cookie.expires.isoformat() if cookie.expires else None,
                    'secure': cookie.secure,
                    'http_only': cookie.http_only
                }
                data.append(item)
            
            # Save to file
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Update cache
            self.cookies[platform] = cookies
            
            logger.info(f"Saved {len(cookies)} cookies for: {platform}")
            
        except Exception as e:
            logger.error(f"Failed to save cookies for {platform}: {e}")
            raise
    
    def import_from_netscape(self, file_path: str, platform: str) -> None:
        """
        Import cookies from Netscape format file.
        
        Args:
            file_path: Path to Netscape format cookie file
            platform: Platform name to associate cookies with
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Cookie file not found: {file_path}")
        
        cookies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse Netscape format
                    # Format: domain flag path secure expiration name value
                    parts = line.split('\t')
                    
                    if len(parts) < 7:
                        logger.warning(f"Invalid cookie line: {line}")
                        continue
                    
                    domain, flag, path, secure, expiration, name, value = parts[:7]
                    
                    # Parse expiration
                    expires = None
                    try:
                        if expiration and expiration != '0':
                            expires = datetime.fromtimestamp(int(expiration))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid expiration: {expiration}")
                    
                    cookie = Cookie(
                        name=name,
                        value=value,
                        domain=domain,
                        path=path,
                        expires=expires,
                        secure=(secure.upper() == 'TRUE'),
                        http_only=False  # Not specified in Netscape format
                    )
                    
                    cookies.append(cookie)
            
            # Save the imported cookies
            self.save_cookies(platform, cookies)
            
            logger.info(
                f"Imported {len(cookies)} cookies from Netscape format for: {platform}"
            )
            
        except Exception as e:
            logger.error(f"Failed to import cookies from {file_path}: {e}")
            raise
    
    def validate_cookies(self, cookies: List[Cookie]) -> bool:
        """
        Validate cookie format and required fields.
        
        Args:
            cookies: List of cookies to validate
            
        Returns:
            True if all cookies are valid, False otherwise
        """
        if not isinstance(cookies, list):
            return False
        
        for cookie in cookies:
            if not isinstance(cookie, Cookie):
                logger.warning(f"Invalid cookie type: {type(cookie)}")
                return False
            
            # Check required fields
            if not cookie.name or not cookie.value:
                logger.warning("Cookie missing name or value")
                return False
            
            if not cookie.domain:
                logger.warning("Cookie missing domain")
                return False
        
        return True
    
    def is_expired(self, cookie: Cookie) -> bool:
        """
        Check if a cookie is expired.
        
        Args:
            cookie: Cookie to check
            
        Returns:
            True if expired, False otherwise
        """
        if cookie.expires is None:
            # Session cookie, never expires
            return False
        
        return datetime.now() > cookie.expires
    
    def remove_expired_cookies(self, platform: str) -> int:
        """
        Remove expired cookies for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Number of cookies removed
        """
        cookies = self.load_cookies(platform)
        
        if not cookies:
            return 0
        
        valid_cookies = [c for c in cookies if not self.is_expired(c)]
        removed_count = len(cookies) - len(valid_cookies)
        
        if removed_count > 0:
            self.save_cookies(platform, valid_cookies)
            logger.info(f"Removed {removed_count} expired cookies for: {platform}")
        
        return removed_count
    
    def clear_cookies(self, platform: str) -> None:
        """
        Clear all cookies for a platform.
        
        Args:
            platform: Platform name
        """
        cookie_file = self.storage_path / f"{platform}.json"
        
        if cookie_file.exists():
            cookie_file.unlink()
        
        if platform in self.cookies:
            del self.cookies[platform]
        
        logger.info(f"Cleared all cookies for: {platform}")
    
    def get_cookie_dict(self, platform: str) -> Dict[str, str]:
        """
        Get cookies as a dictionary for HTTP headers.
        
        Args:
            platform: Platform name
            
        Returns:
            Dictionary of cookie name-value pairs
        """
        cookies = self.load_cookies(platform)
        
        # Filter out expired cookies
        valid_cookies = [c for c in cookies if not self.is_expired(c)]
        
        return {c.name: c.value for c in valid_cookies}
    
    def get_cookie_string(self, platform: str) -> str:
        """
        Get cookies as a string for Cookie header.
        
        Args:
            platform: Platform name
            
        Returns:
            Cookie string (e.g., "name1=value1; name2=value2")
        """
        cookie_dict = self.get_cookie_dict(platform)
        return "; ".join(f"{name}={value}" for name, value in cookie_dict.items())
