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
        output_path="./downloads",
        quality="1080p",
    )
    result = await downloader.download("https://www.youtube.com/watch?v=xxx", options)

    if result.success:
        print(f"Saved to: {result.file_path}")
    else:
        print(f"Failed: {result.error}")

    # Extract metadata only
    metadata = await downloader.extract_metadata("https://www.douyin.com/video/123")
    print(f"Title: {metadata.title}")
    print(f"Author: {metadata.author}")

asyncio.run(main())
```

## Desktop App (macOS)

从 `dist/VDL-<版本>.dmg` 安装：挂载后把 **VDL.app** 拖入 Applications。

**首次打开**：无 Apple Developer 签名（ad-hoc），绕过 Gatekeeper 的方式为
**右键点击 VDL.app → 打开 → 再点「打开」**（直接双击会提示无法验证开发者）。

**运行环境要求**：

| 依赖 | 说明 |
|------|------|
| 代理（下 YouTube 时） | 默认跟随系统环境变量 `HTTPS_PROXY`，也可在应用「设置」页覆盖 |
| cookies | 应用「Cookie 管理」上传 Netscape cookies.txt，或选择浏览器（Chrome 首次会触发钥匙串授权弹窗） |
| deno | yt-dlp 解 YouTube JS 挑战必需：`brew install deno`（缺它时 YouTube 预览报 "The page needs to be reloaded"） |
| ffmpeg / ffprobe | 已随 app 打包（静态构建），无需安装 |

**功能入口**：粘贴 URL 自动预览（画质下拉含 4K/2160p 与预计体积）→ 下载队列实时进度；「设置」页可改代理与下载目录（默认 `~/Downloads/vdl`）。

**自行构建**：`scripts/build_desktop.sh`（Python 3.12 venv + PyInstaller；详见 `vdl.spec`）。

