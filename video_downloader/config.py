"""
Configuration management for video-downloader-skill.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Type, Dict
from pathlib import Path


@dataclass
class DownloaderConfig:
    """Configuration for VideoDownloader."""
    
    # Basic configuration
    cookie_path: str = str(Path.home() / ".video-downloader" / "cookies")
    cookie_file: str = "./cookies.txt"
    output_dir: str = "./downloads"
    filename_template: str = "{title}"
    
    # Network configuration
    timeout: int = 30
    max_retries: int = 3
    proxy: Optional[str] = None
    
    # Browser configuration
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    
    # Anti-scraping configuration
    enable_stealth: bool = True
    random_delay_range: Tuple[float, float] = (1.0, 3.0)
    rotate_user_agent: bool = True
    
    # Download configuration
    chunk_size: int = 1024 * 1024  # 1MB
    enable_resume: bool = True
    
    # Extension configuration
    custom_extractors: List[Type] = field(default_factory=list)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure directories exist."""
        Path(self.cookie_path).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
