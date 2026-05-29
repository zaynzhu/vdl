# VDL Usage Guide

## Basic Download

```bash
# Download a video (default: ./downloads directory, original quality)
vdl https://www.bilibili.com/video/BV1xx411c7mD

# Download a YouTube video
vdl https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Quality Selection

```bash
# Download at 1080p
vdl https://www.bilibili.com/video/BV1xx411c7mD -q 1080p

# Download at 720p
vdl https://www.youtube.com/watch?v=xxx -q 720p
```

## Output Directory

```bash
# Save to a specific directory
vdl https://www.bilibili.com/video/BV1xx411c7mD -o ./my_videos
```

## Custom Filenames

```bash
# Use author and title
vdl URL -f "{author}_{title}"

# Organize by platform and date
vdl URL -f "{platform}/{date}_{title}"
```

Available template variables: `{title}`, `{author}`, `{id}`, `{date}`, `{platform}`

## Batch Download

```bash
# Download multiple videos in one command
vdl url1 url2 url3
```

## Metadata Extraction

```bash
# View video info without downloading
vdl --metadata-only https://www.douyin.com/video/123456
```

## Using Cookies

For platforms that require authentication (e.g., Bilibili HD quality):

```bash
vdl https://www.bilibili.com/video/BV1xx411c7mD -c cookies/bilibili.txt
```

Cookie files must be in Netscape format. See `cookies/` directory for `.example` files.

## Platform-Specific Notes

### Bilibili
- Supports 4K, 1080P, 720P, 480P
- HD quality requires cookies from a logged-in session
- Uses yt-dlp with a custom Bilibili extractor as fallback

### Douyin
- Uses a 3-tier fallback: yt-dlp -> direct API -> Playwright browser
- Supports both videos and image galleries
- Playwright must be installed for the fallback chain (`playwright install chromium`)

### YouTube, Twitter/X, Instagram, TikTok
- Handled entirely by yt-dlp
- No special setup required

## List Supported Platforms

```bash
vdl --list-platforms
```

## Verbose Output

```bash
# See detailed download progress and debug info
vdl URL -v

# Suppress all output except errors
vdl URL --quiet
```

## Proxy

Set environment variables before running:

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
vdl https://www.youtube.com/watch?v=xxx
```

## Python API

```python
import asyncio
from video_downloader import VideoDownloader
from video_downloader.models import DownloadOptions

async def main():
    downloader = VideoDownloader()

    # Simple download
    result = await downloader.download("https://www.bilibili.com/video/BV1xx411c7mD")

    # With options
    options = DownloadOptions(
        output_dir="./downloads",
        quality="1080p",
    )
    result = await downloader.download("https://www.youtube.com/watch?v=xxx", options)

    if result.success:
        print(f"Saved to: {result.file_path}")
    else:
        print(f"Failed: {result.error_message}")

    # Extract metadata only
    metadata = await downloader.extract_metadata("https://www.douyin.com/video/123")
    print(f"Title: {metadata.title}")
    print(f"Author: {metadata.author}")

asyncio.run(main())
```
