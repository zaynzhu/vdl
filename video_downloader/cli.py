"""
Command-line interface for video-downloader-skill.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional
from .core import VideoDownloader
from .config import DownloaderConfig
from .models import DownloadOptions
from .logger import logger, setup_logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='vdl - Multi-platform video downloader powered by yt-dlp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a video
  vdl download https://www.bilibili.com/video/BV1xx411c7mD

  # Download with quality and output dir
  vdl download https://www.youtube.com/watch?v=xxx -q 1080p -o ./videos

  # Download multiple videos
  vdl download url1 url2 url3

  # Extract metadata only
  vdl info https://www.douyin.com/video/123456

  # List supported platforms
  vdl platforms

  # Use cookies for authenticated download
  vdl download https://www.bilibili.com/video/BV1xx --cookies ./cookies/bilibili.txt
        """
    )
    
    # Positional arguments
    parser.add_argument(
        'urls',
        nargs='*',  # Changed from '+' to '*' to allow zero URLs
        help='Video URL(s) to download'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        default='./downloads',
        help='Output directory (default: ./downloads)'
    )
    
    parser.add_argument(
        '-f', '--filename',
        dest='filename_template',
        default='{title}',
        help='Filename template (default: {title}). Available: {title}, {author}, {id}, {date}, {platform}'
    )
    
    # Quality options
    parser.add_argument(
        '-q', '--quality',
        dest='quality',
        help='Video quality (e.g., 1080P, 720P)'
    )
    
    # Cookie options
    parser.add_argument(
        '-c', '--cookies',
        dest='cookie_file',
        help='Path to Netscape format cookie file'
    )
    
    # Metadata only
    parser.add_argument(
        '--metadata-only',
        action='store_true',
        help='Extract metadata only, do not download'
    )
    
    # Verbose logging
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Quiet mode
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    # List platforms
    parser.add_argument(
        '--list-platforms',
        action='store_true',
        help='List supported platforms and exit'
    )
    
    return parser.parse_args()


async def download_video(downloader: VideoDownloader, url: str, options: DownloadOptions):
    """Download a single video."""
    print(f"\n📥 Downloading: {url}")
    
    try:
        result = await downloader.download(url, options)
        
        if result.success:
            print(f"✅ Success: {result.file_path}")
            if result.file_size:
                size_mb = result.file_size / (1024 * 1024)
                print(f"   Size: {size_mb:.2f} MB")
        else:
            print(f"❌ Failed: {result.error_message}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception(f"Download failed: {e}")
        return False


async def extract_metadata_only(downloader: VideoDownloader, url: str):
    """Extract and display metadata only."""
    print(f"\n📋 Extracting metadata: {url}")
    
    try:
        metadata = await downloader.extract_metadata(url)
        
        print(f"\n{'='*60}")
        print(f"Title:    {metadata.title}")
        print(f"Author:   {metadata.author}")
        print(f"Platform: {metadata.platform}")
        print(f"ID:       {metadata.video_id}")
        
        if metadata.duration:
            minutes = metadata.duration // 60
            seconds = metadata.duration % 60
            print(f"Duration: {minutes}:{seconds:02d}")
        
        if metadata.description:
            desc = metadata.description[:100]
            if len(metadata.description) > 100:
                desc += "..."
            print(f"Description: {desc}")
        
        if metadata.available_qualities:
            qualities = ", ".join(q.name for q in metadata.available_qualities)
            print(f"Qualities: {qualities}")
        
        # Check if it's an image gallery
        is_gallery = metadata.extra_data.get('is_gallery', False)
        if is_gallery:
            images = metadata.extra_data.get('images', [])
            print(f"Type: Image Gallery ({len(images)} images)")
        
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception(f"Metadata extraction failed: {e}")
        return False


async def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Setup logging
    if args.verbose:
        setup_logger('DEBUG')
    elif args.quiet:
        setup_logger('ERROR')
    else:
        setup_logger('INFO')
    
    # Create config
    config = DownloaderConfig(
        output_dir=args.output_dir,
        filename_template=args.filename_template,
        cookie_file=args.cookie_file or './cookies.txt'
    )
    
    # Create downloader
    downloader = VideoDownloader(config)
    
    # List platforms
    if args.list_platforms:
        platforms = downloader.list_supported_platforms()
        print("\n📺 Supported Platforms:")
        for platform in platforms:
            print(f"  • {platform}")
        print("\nPowered by yt-dlp (YouTube, Bilibili, Twitter, Instagram, TikTok)")
        print("Douyin: yt-dlp → API → Playwright fallback chain")
        print()
        return 0
    
    # Check if URLs provided
    if not args.urls:
        print("❌ Error: No URLs provided")
        print("Use --help for usage information")
        return 1
    
    # Create download options
    options = DownloadOptions(
        output_dir=args.output_dir,
        filename_template=args.filename_template,
        quality=args.quality
    )
    
    # Process URLs
    urls = args.urls
    success_count = 0
    fail_count = 0
    
    print(f"\n🚀 Video Downloader")
    print(f"{'='*60}")
    
    if args.metadata_only:
        # Metadata extraction mode
        for url in urls:
            if await extract_metadata_only(downloader, url):
                success_count += 1
            else:
                fail_count += 1
    else:
        # Download mode
        for url in urls:
            if await download_video(downloader, url, options):
                success_count += 1
            else:
                fail_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Summary: {success_count} successful, {fail_count} failed")
    print(f"{'='*60}\n")
    
    return 0 if fail_count == 0 else 1


def cli_entry():
    """Entry point for console script."""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.exception("Fatal error in CLI")
        sys.exit(1)


if __name__ == '__main__':
    cli_entry()
