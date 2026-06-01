"""
Download manager for handling file downloads with progress tracking and retry logic.
"""

import os
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Callable
from datetime import datetime
from .models import DownloadResult, VideoMetadata
from .config import DownloaderConfig
from .exceptions import (
    DownloadError, NetworkError, RetryableError, 
    NonRetryableError, TimeoutError, RateLimitError
)
from .logger import logger


# Type alias for progress callback
ProgressCallback = Callable[[int, int], None]


class DownloadManager:
    """
    Manages file downloads with progress tracking and retry logic.
    
    Features:
    - HTTP file download with resume support
    - Progress tracking and reporting
    - Automatic retry with exponential backoff
    - Filename sanitization and conflict resolution
    """
    
    def __init__(self, config: DownloaderConfig):
        """
        Initialize download manager.
        
        Args:
            config: Downloader configuration
        """
        self.config = config
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        
        logger.info("DownloadManager initialized")
    
    async def download_file(
        self,
        url: str,
        output_path: str,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> DownloadResult:
        """
        Download a file from URL to output path.
        
        Args:
            url: Download URL
            output_path: Output file path
            headers: Optional HTTP headers
            progress_callback: Optional progress callback function(downloaded, total)
            
        Returns:
            DownloadResult with success status and metadata
        """
        logger.info(f"Starting download: {url}")
        logger.debug(f"Output path: {output_path}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Attempt download with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                result = await self._download_with_resume(
                    url, output_path, headers, progress_callback
                )
                
                logger.info(f"Download completed: {output_path}")
                return result
                
            except NonRetryableError as e:
                # Don't retry non-retryable errors
                logger.error(f"Non-retryable error: {e}")
                raise
                
            except (aiohttp.ClientError, asyncio.TimeoutError, RetryableError) as e:
                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(
                        f"Download failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Download failed after {self.max_retries + 1} attempts")
                    raise NetworkError(f"Failed to download {url}: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error during download: {e}")
                raise DownloadError(f"Download error: {e}")
        
        # Should not reach here
        raise DownloadError("Download failed")

    async def merge_dash_files(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
    ) -> DownloadResult:
        """Merge DASH video and audio streams using ffmpeg.

        Args:
            video_path: Path to downloaded video stream
            audio_path: Path to downloaded audio stream
            output_path: Desired output file path

        Returns:
            DownloadResult with the merged file, or the video-only file on failure
        """
        ffmpeg = self.config.ffmpeg_path
        logger.info(f"Merging DASH streams: {video_path} + {audio_path}")

        try:
            proc = await asyncio.create_subprocess_exec(
                ffmpeg, "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c", "copy",
                output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.warning(f"ffmpeg merge failed (exit {proc.returncode}): {stderr.decode()[:200]}")
                # Fall back to video-only file
                return DownloadResult(
                    success=True,
                    file_path=video_path,
                    file_size=os.path.getsize(video_path),
                )

            # Clean up part files
            for part in (video_path, audio_path):
                if os.path.exists(part) and part != output_path:
                    os.remove(part)

            final_size = os.path.getsize(output_path)
            logger.info(f"DASH merge complete: {output_path} ({final_size} bytes)")
            return DownloadResult(
                success=True,
                file_path=output_path,
                file_size=final_size,
            )

        except FileNotFoundError:
            logger.warning(f"ffmpeg not found at '{ffmpeg}', keeping separate streams")
            return DownloadResult(
                success=True,
                file_path=video_path,
                file_size=os.path.getsize(video_path),
            )
        except Exception as e:
            logger.warning(f"DASH merge error: {e}, keeping video-only file")
            return DownloadResult(
                success=True,
                file_path=video_path,
                file_size=os.path.getsize(video_path),
            )

    async def _download_with_resume(
        self,
        url: str,
        output_path: str,
        headers: Optional[Dict[str, str]],
        progress_callback: Optional[ProgressCallback]
    ) -> DownloadResult:
        """
        Download file with resume support.
        
        Args:
            url: Download URL
            output_path: Output file path
            headers: HTTP headers
            progress_callback: Progress callback
            
        Returns:
            DownloadResult
        """
        # Check if partial file exists
        downloaded_size = 0
        if os.path.exists(output_path):
            downloaded_size = os.path.getsize(output_path)
            logger.debug(f"Resuming download from byte {downloaded_size}")
        
        # Prepare headers with range if resuming
        request_headers = headers.copy() if headers else {}
        if downloaded_size > 0:
            request_headers['Range'] = f'bytes={downloaded_size}-'
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=request_headers) as response:
                # Check response status
                if response.status == 429:
                    # Rate limit
                    raise RateLimitError("Rate limit exceeded")
                elif response.status == 403:
                    # Forbidden - likely anti-bot
                    raise NonRetryableError(f"Access forbidden (403) - possible anti-bot detection")
                elif response.status == 404:
                    # Not found
                    raise NonRetryableError(f"Resource not found (404)")
                elif response.status not in (200, 206):
                    # Other errors
                    raise NetworkError(
                        f"HTTP {response.status}: {response.reason}"
                    )
                
                # Get total file size
                content_length = response.headers.get('Content-Length')
                if content_length:
                    total_size = int(content_length)
                    if response.status == 206:
                        # Partial content, add already downloaded size
                        total_size += downloaded_size
                else:
                    total_size = 0

                logger.debug(f"Total size: {total_size} bytes")

                # If server returned 200 instead of 206, discard partial file
                if response.status == 200 and downloaded_size > 0:
                    downloaded_size = 0

                # Open file for writing (append if resuming partial content)
                mode = 'ab' if response.status == 206 and downloaded_size > 0 else 'wb'
                with open(output_path, mode) as f:
                    chunk_size = 8192
                    current_size = downloaded_size
                    
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)
                        current_size += len(chunk)
                        
                        # Report progress
                        if progress_callback and total_size > 0:
                            progress_callback(current_size, total_size)
                
                # Create result
                final_size = os.path.getsize(output_path)
                return DownloadResult(
                    success=True,
                    file_path=output_path,
                    file_size=final_size,
                    duration=0.0  # TODO: track actual time
                )
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing illegal characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove illegal characters for Windows/Unix
        illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(illegal_chars, '_', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Limit length (255 is common filesystem limit)
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200 - len(ext)] + ext
        
        # Ensure not empty
        if not sanitized:
            sanitized = 'download'
        
        logger.debug(f"Sanitized filename: {filename} -> {sanitized}")
        return sanitized
    
    def generate_filename(
        self,
        template: str,
        metadata: VideoMetadata,
        extension: Optional[str] = None
    ) -> str:
        """
        Generate filename from template and metadata.
        
        Args:
            template: Filename template with placeholders
            metadata: Video metadata
            extension: File extension (optional)
            
        Returns:
            Generated filename
            
        Template placeholders:
            {title} - Video title
            {author} - Author name
            {id} - Video ID
            {date} - Upload date (YYYY-MM-DD)
            {platform} - Platform name
        """
        # Replace placeholders
        filename = template
        filename = filename.replace('{title}', metadata.title or 'untitled')
        filename = filename.replace('{author}', metadata.author or 'unknown')
        # Extract video ID: prefer extractor-provided, fallback to URL parsing
        video_id = metadata.video_id or self._extract_video_id_from_url(metadata.url)
        filename = filename.replace('{id}', video_id)
        filename = filename.replace('{platform}', metadata.platform or 'unknown')
        
        # Format date
        if metadata.upload_date:
            date_str = metadata.upload_date.strftime('%Y-%m-%d')
        else:
            date_str = datetime.now().strftime('%Y-%m-%d')
        filename = filename.replace('{date}', date_str)
        
        # Add extension if provided
        if extension:
            if not extension.startswith('.'):
                extension = '.' + extension
            filename += extension
        
        # Sanitize the result
        return self.sanitize_filename(filename)

    @staticmethod
    def _extract_video_id_from_url(url: str) -> str:
        """Extract a meaningful video ID from a URL.

        Handles YouTube query params (v=xxx), Bilibili/Douyin path segments,
        and generic URLs. Returns 'unknown' as fallback.
        """
        if not url:
            return 'unknown'

        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(url)

        # YouTube-style: ?v=VIDEO_ID
        qs = parse_qs(parsed.query)
        if 'v' in qs:
            return qs['v'][0]

        # Path-based: take last non-empty segment
        segments = [s for s in parsed.path.split('/') if s]
        if segments:
            return segments[-1]

        return 'unknown'

    def resolve_output_path(
        self,
        base_path: str,
        filename: str,
        auto_rename: bool = True
    ) -> str:
        """
        Resolve output path and handle filename conflicts.
        
        Args:
            base_path: Base output directory
            filename: Desired filename
            auto_rename: Whether to auto-rename on conflict
            
        Returns:
            Resolved output path
        """
        # Ensure base path exists
        os.makedirs(base_path, exist_ok=True)
        
        # Construct full path
        output_path = os.path.join(base_path, filename)
        
        # Handle conflicts
        if os.path.exists(output_path) and auto_rename:
            name, ext = os.path.splitext(filename)
            counter = 1
            
            while os.path.exists(output_path):
                new_filename = f"{name}_{counter}{ext}"
                output_path = os.path.join(base_path, new_filename)
                counter += 1
            
            logger.debug(f"Renamed to avoid conflict: {output_path}")
        
        return output_path
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: 2^attempt seconds, max 60 seconds
        delay = min(2 ** attempt, 60)
        return delay
    
    async def download_multiple(
        self,
        downloads: list[tuple[str, str, Optional[Dict[str, str]]]],
        progress_callback: Optional[ProgressCallback] = None
    ) -> list[DownloadResult]:
        """
        Download multiple files concurrently.
        
        Args:
            downloads: List of (url, output_path, headers) tuples
            progress_callback: Optional progress callback
            
        Returns:
            List of DownloadResult
        """
        logger.info(f"Starting batch download of {len(downloads)} files")
        
        tasks = [
            self.download_file(url, path, headers, progress_callback)
            for url, path, headers in downloads
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                url, path, _ = downloads[i]
                logger.error(f"Download failed: {url} - {result}")
                final_results.append(
                    DownloadResult(
                        success=False,
                        file_path=path,
                        error=str(result)
                    )
                )
            else:
                final_results.append(result)
        
        success_count = sum(1 for r in final_results if r.success)
        logger.info(f"Batch download completed: {success_count}/{len(downloads)} successful")
        
        return final_results
