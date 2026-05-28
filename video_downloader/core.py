"""
Core VideoDownloader class - main entry point.
"""

from typing import List, Optional, Dict
from .config import DownloaderConfig
from .models import (
    DownloadOptions,
    DownloadResult,
    VideoMetadata,
    BatchResult,
)
from .exceptions import (
    ValidationError,
    UnsupportedPlatformError,
    DownloadError,
)
from .platform_manager import PlatformManager
from .cookie_store import CookieStore
from .browser_fingerprint import BrowserFingerprint
from .download_manager import DownloadManager
from .logger import logger


class VideoDownloader:
    """
    Main video downloader class.
    
    Provides unified interface for downloading videos from multiple platforms.
    """
    
    def __init__(self, config: Optional[DownloaderConfig] = None):
        """
        Initialize VideoDownloader.
        
        Args:
            config: Optional configuration. Uses default if not provided.
        """
        self.config = config or DownloaderConfig()
        logger.info("VideoDownloader initialized with config: %s", self.config)
        
        # Initialize platform manager
        self.platform_manager = PlatformManager()
        
        # Initialize cookie store
        self.cookie_store = CookieStore(self.config.cookie_file)
        
        # Initialize browser fingerprint
        self.fingerprint = BrowserFingerprint()
        
        # Initialize download manager
        self.download_manager = DownloadManager(self.config)
    
    def _validate_url(self, url: str) -> None:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError("URL cannot be empty")
        
        if not isinstance(url, str):
            raise ValidationError("URL must be a string")
        
        if not url.startswith(('http://', 'https://')):
            raise ValidationError("URL must start with http:// or https://")
        
        logger.debug(f"URL validation passed: {url}")
    
    def _get_extractor_for_url(self, url: str):
        """
        Get the appropriate extractor for the given URL.
        
        Args:
            url: Video URL
            
        Returns:
            Platform extractor instance
            
        Raises:
            UnsupportedPlatformError: If platform is not supported
        """
        if self.platform_manager is None:
            raise DownloadError("Platform manager not initialized")
        
        extractor = self.platform_manager.get_extractor(url)
        
        if extractor is None:
            supported = self.list_supported_platforms()
            raise UnsupportedPlatformError(
                f"Platform not supported for URL: {url}. "
                f"Supported platforms: {', '.join(supported)}"
            )
        
        logger.debug(f"Selected extractor: {extractor}")
        return extractor
    
    async def download(self, url: str, options: Optional[DownloadOptions] = None) -> DownloadResult:
        """
        Download a single video or gallery.
        
        Args:
            url: Video URL
            options: Download options
            
        Returns:
            Download result
            
        Raises:
            ValidationError: If URL is invalid
            UnsupportedPlatformError: If platform is not supported
            DownloadError: If download fails
        """
        options = options or DownloadOptions()
        
        try:
            # Validate URL
            self._validate_url(url)
            logger.info(f"Starting download: {url}")
            
            # Get appropriate extractor
            extractor = self._get_extractor_for_url(url)
            platform = extractor.get_platform_name()
            
            # Load cookies for platform
            cookies = self.cookie_store.load_cookies(platform)
            cookie_dict = self.cookie_store.get_cookie_dict(cookies)
            
            # Extract metadata
            logger.info("Extracting metadata...")
            metadata = await extractor.extract_metadata(url, cookie_dict)
            
            # Determine quality
            quality = options.quality or self._select_default_quality(metadata)
            
            # Get download URLs
            logger.info("Getting download URLs...")
            download_urls = await extractor.get_download_urls(metadata, quality, cookie_dict)
            
            if not download_urls:
                raise DownloadError("No download URLs found")
            
            # Generate output filename
            output_dir = options.output_dir or self.config.output_dir
            filename = self.download_manager.generate_filename(
                options.filename_template or self.config.filename_template,
                metadata,
                extension='mp4'  # Default extension
            )
            
            # Resolve output path
            output_path = self.download_manager.resolve_output_path(
                output_dir,
                filename,
                auto_rename=True
            )
            
            # Get headers for download
            headers = self.fingerprint.get_headers(platform)
            
            # Download file(s)
            logger.info(f"Downloading to: {output_path}")
            
            if len(download_urls) == 1:
                # Single file download
                result = await self.download_manager.download_file(
                    download_urls[0],
                    output_path,
                    headers
                )
            else:
                # Multiple files (e.g., video + audio or image gallery)
                results = []
                for idx, dl_url in enumerate(download_urls):
                    # Generate unique filename for each part
                    part_filename = f"{filename}_part{idx}"
                    part_path = self.download_manager.resolve_output_path(
                        output_dir,
                        part_filename,
                        auto_rename=True
                    )
                    
                    result = await self.download_manager.download_file(
                        dl_url,
                        part_path,
                        headers
                    )
                    results.append(result)
                
                # Return result of first file (main video/image)
                result = results[0]
            
            logger.info(f"Download completed: {result.file_path}")
            return result
            
        except (ValidationError, UnsupportedPlatformError) as e:
            logger.error(f"Download failed: {e}")
            return DownloadResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.exception(f"Unexpected error during download: {e}")
            return DownloadResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def batch_download(
        self,
        urls: List[str],
        options: Optional[DownloadOptions] = None
    ) -> BatchResult:
        """
        Download multiple videos.
        
        Args:
            urls: List of video URLs
            options: Download options
            
        Returns:
            Batch download result
        """
        options = options or DownloadOptions()
        logger.info(f"Starting batch download: {len(urls)} URLs")
        
        results = []
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}: {url}")
            
            try:
                result = await self.download(url, options)
                results.append(result)
                
                if result.success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")
                results.append(DownloadResult(
                    success=False,
                    error_message=str(e)
                ))
                failed += 1
        
        logger.info(
            f"Batch download complete: {successful} successful, {failed} failed"
        )
        
        return BatchResult(
            total=len(urls),
            successful=successful,
            failed=failed,
            results=results
        )
    
    async def extract_metadata(self, url: str) -> VideoMetadata:
        """
        Extract video metadata without downloading.
        
        Args:
            url: Video URL
            
        Returns:
            Video metadata
            
        Raises:
            ValidationError: If URL is invalid
            UnsupportedPlatformError: If platform is not supported
        """
        # Validate URL
        self._validate_url(url)
        logger.info(f"Extracting metadata: {url}")
        
        # Get appropriate extractor
        extractor = self._get_extractor_for_url(url)
        platform = extractor.get_platform_name()
        
        # Load cookies for platform
        cookies = self.cookie_store.load_cookies(platform)
        cookie_dict = self.cookie_store.get_cookie_dict(cookies)
        
        # Extract metadata
        metadata = await extractor.extract_metadata(url, cookie_dict)
        
        logger.info(f"Metadata extracted: {metadata.title}")
        return metadata
    
    def _select_default_quality(self, metadata: VideoMetadata) -> Optional[str]:
        """
        Select default quality based on available options.
        
        Args:
            metadata: Video metadata
            
        Returns:
            Quality ID or None
        """
        if not metadata.available_qualities:
            return None
        
        # Try to find 1080P or highest available
        for quality in metadata.available_qualities:
            if '1080' in quality.name:
                return quality.quality_id
        
        # Return first (usually highest) quality
        return metadata.available_qualities[0].quality_id
    
    def list_supported_platforms(self) -> List[str]:
        """
        List all supported platforms.
        
        Returns:
            List of platform names
        """
        if self.platform_manager is None:
            logger.warning("Platform manager not initialized")
            return []
        
        return self.platform_manager.list_platforms()
