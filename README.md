# VDL -- Multi-Platform Video Downloader

A multi-platform video downloader powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp). Supports YouTube, Bilibili, Douyin, Twitter/X, Instagram, and TikTok with a unified CLI interface.

## Supported Platforms

| Platform | Engine | Notes |
|----------|--------|-------|
| YouTube | yt-dlp | All formats and qualities |
| Bilibili | yt-dlp + custom extractor fallback | 4K/1080P/720P, cookie support for HD |
| Douyin | 3-tier fallback (yt-dlp -> API -> Playwright) | Videos and image galleries |
| Twitter/X | yt-dlp | Videos and images |
| Instagram | yt-dlp | Reels, posts, IGTV |
| TikTok | yt-dlp | Videos |

## Installation

### From source (recommended)

```bash
git clone https://github.com/zaynzhu/vdl.git
cd vdl
pip install -e .
```

### Dependencies

- Python 3.8+
- yt-dlp (primary download engine)
- Playwright (optional, for Douyin fallback)

```bash
# Install yt-dlp
pip install yt-dlp

# Install Playwright browser (only needed for Douyin fallback)
playwright install chromium
```

## Quick Start

```bash
# Download a Bilibili video
vdl https://www.bilibili.com/video/BV1xx411c7mD

# Download a YouTube video at 1080p
vdl https://www.youtube.com/watch?v=xxx -q 1080p

# Download to a specific directory
vdl https://www.bilibili.com/video/BV1xx411c7mD -o ./my_videos

# Extract video info without downloading
vdl --metadata-only https://www.douyin.com/video/123456

# List supported platforms
vdl --list-platforms

# Download multiple videos at once
vdl url1 url2 url3

# Use cookies for authenticated downloads (HD quality)
vdl https://www.bilibili.com/video/BV1xx411c7mD -c cookies/bilibili.txt
```

## Cookie Setup

Some platforms require cookies for HD quality or authenticated content. Cookie files should be in Netscape format.

The `cookies/` directory contains `.example` files showing the expected format:

```
cookies/
  bilibili.txt.example
  douyin.txt.example
```

To use cookies:

1. Copy the example file and rename it (e.g., `cp cookies/bilibili.txt.example cookies/bilibili.txt`)
2. Export cookies from your browser using a plugin like "Get cookies.txt"
3. Replace the example content with your real cookies
4. Pass the cookie file with `-c cookies/bilibili.txt`

## CLI Reference

```
vdl [URLs...] [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--output DIR` | `-o` | Output directory (default: `./downloads`) |
| `--filename TEMPLATE` | `-f` | Filename template (default: `{title}`) |
| `--quality QUALITY` | `-q` | Video quality (e.g., `1080p`, `720p`) |
| `--cookies FILE` | `-c` | Path to Netscape format cookie file |
| `--metadata-only` | | Extract video info without downloading |
| `--verbose` | `-v` | Enable verbose logging |
| `--quiet` | | Suppress all output except errors |
| `--list-platforms` | | List supported platforms and exit |

### Filename Templates

Available variables: `{title}`, `{author}`, `{id}`, `{date}`, `{platform}`

```bash
vdl URL -f "{author}_{title}"
vdl URL -f "{platform}/{date}_{title}"
```

## Project Structure

```
video_downloader/
  __init__.py
  __main__.py           # python -m video_downloader entry
  cli.py                # CLI entry point (vdl command)
  core.py               # VideoDownloader main class
  platform_manager.py   # Platform detection and extractor registry
  download_manager.py   # File download with progress
  config.py             # Configuration management
  models.py             # Data models
  exceptions.py         # Exception hierarchy
  cookie_store.py       # Cookie file handling
  logger.py             # Logging setup
  extractors/
    base.py             # Abstract PlatformExtractor base
    yt_dlp.py           # yt-dlp extractor (YouTube, Bilibili, Twitter, Instagram, TikTok, Douyin)
    bilibili.py         # Bilibili-specific fallback extractor
    douyin.py           # Douyin 3-tier fallback (yt-dlp -> API -> Playwright)
```

## Architecture

The downloader uses a plugin-based extractor system:

1. **YtDlpExtractor** -- primary extractor backed by yt-dlp, handles most platforms
2. **BilibiliExtractor** -- fallback for Bilibili when yt-dlp support lags
3. **DouyinExtractor** -- 3-tier fallback chain for Douyin (yt-dlp -> API -> Playwright)

When a URL is submitted, the PlatformManager tries each registered extractor in order until one claims it.

## Troubleshooting

### yt-dlp errors

Make sure yt-dlp is up to date:
```bash
pip install --upgrade yt-dlp
```

### Douyin downloads fail

Douyin requires a fallback chain. If yt-dlp fails, the tool tries a direct API call, then falls back to Playwright browser automation:

```bash
# Install Playwright browser for Douyin fallback
playwright install chromium
```

### Cookie issues

- Cookies must be in Netscape format
- Use a browser extension like "Get cookies.txt" to export
- Some platforms rotate sessions frequently -- re-export cookies if downloads start failing

### Proxy support

Set the `HTTP_PROXY` or `HTTPS_PROXY` environment variable:

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
vdl https://www.youtube.com/watch?v=xxx
```

## License

MIT License -- see [LICENSE](LICENSE) for details.
