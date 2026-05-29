<div align="center">

# 🎬 VDL

**Multi-Platform Video Downloader powered by yt-dlp**

[中文](README_CN.md) | English

![License](https://img.shields.io/github/license/zaynzhu/vdl?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/zaynzhu/vdl?style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/zaynzhu/vdl?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/zaynzhu/vdl?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/zaynzhu/vdl?style=for-the-badge)
![Python Version](https://img.shields.io/pypi/pyversions/yt-dlp?style=for-the-badge&label=Python)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge)
![Downloads](https://img.shields.io/github/downloads/zaynzhu/vdl/total?style=for-the-badge)
![Code Style](https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge)

</div>

---

> [!TIP]
> VDL wraps yt-dlp into a clean CLI + MCP server, covering 6 major platforms with automatic fallback chains. No GUI, no bloat — just `vdl <url>` and it works.

## ✨ Features

- **6 Platforms, One Command** -- YouTube, Bilibili, Douyin, Twitter/X, Instagram, TikTok
- **yt-dlp as Core Engine** -- Battle-tested extraction with automatic DASH merging via ffmpeg
- **Douyin 3-Tier Fallback** -- yt-dlp → direct API → Playwright browser, fully automatic
- **Cookie Authentication** -- Netscape format cookies for HD quality on Bilibili and more
- **Batch Download** -- Pass multiple URLs, concurrent downloads with progress tracking
- **MCP Server** -- AI tool integration via Model Context Protocol (stdio JSON-RPC)
- **Filename Templates** -- Customizable with `{title}`, `{author}`, `{id}`, `{date}`, `{platform}`
- **Quality Selection** -- `1080p`, `720p`, `480p` or yt-dlp format strings

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/zaynzhu/vdl.git
cd vdl
pip install -e .

# Download a video
vdl https://www.bilibili.com/video/BV1xx411c7mD

# Download at specific quality
vdl https://www.youtube.com/watch?v=xxx -q 1080p -o ./videos

# Get video info without downloading
vdl --metadata-only https://www.douyin.com/video/123456

# List supported platforms
vdl --list-platforms
```

## 📦 Installation

### From source (recommended)

```bash
git clone https://github.com/zaynzhu/vdl.git
cd vdl
pip install -e .
```

### Dependencies

```bash
# Core engine (auto-installed)
pip install yt-dlp

# Douyin fallback (optional)
playwright install chromium
```

## 🔄 Comparison

| Feature | VDL | youtube-dl | you-get | cobalt |
|---------|:---:|:----------:|:-------:|:------:|
| YouTube | ✅ | ✅ | ✅ | ✅ |
| Bilibili (HD) | ✅ | ⚠️ | ✅ | ❌ |
| Douyin | ✅ | ❌ | ⚠️ | ❌ |
| Twitter/X | ✅ | ✅ | ⚠️ | ✅ |
| Instagram | ✅ | ⚠️ | ❌ | ✅ |
| TikTok | ✅ | ⚠️ | ⚠️ | ✅ |
| CLI | ✅ | ✅ | ✅ | ❌ |
| MCP Server | ✅ | ❌ | ❌ | ❌ |
| Batch Download | ✅ | ❌ | ❌ | ❌ |
| Cookie Auth | ✅ | ✅ | ⚠️ | ❌ |

## 💡 Usage

### Basic download

```bash
vdl https://www.bilibili.com/video/BV1xx411c7mD
```

### Quality and output directory

```bash
vdl https://www.youtube.com/watch?v=xxx -q 720p -o ./my_videos
```

### Custom filename

```bash
vdl URL -f "{author}_{title}"
vdl URL -f "{platform}/{date}_{title}"
```

### Batch download

```bash
vdl url1 url2 url3
```

### With cookies (Bilibili HD)

```bash
vdl https://www.bilibili.com/video/BV1xx -c cookies/bilibili.txt
```

### Cookie Setup

1. Copy the example: `cp cookies/bilibili.txt.example cookies/bilibili.txt`
2. Export cookies from your browser (use "Get cookies.txt" extension)
3. Replace example content with your real cookies
4. Use: `vdl URL -c cookies/bilibili.txt`

## 📚 Documentation

| Topic | Description |
|-------|-------------|
| [USAGE.md](USAGE.md) | Detailed usage guide with examples |
| [Architecture](#architecture) | How the extractor system works |
| [Cookie Setup](#cookie-setup) | Per-platform cookie configuration |
| [Troubleshooting](#faq) | Common issues and solutions |

## 🏗️ Architecture

```text
VideoDownloader (core.py)
│
├── PlatformManager
│   ├── YtDlpExtractor        ← primary, covers 6 platforms
│   ├── BilibiliExtractor      ← fallback for Bilibili
│   └── DouyinExtractor        ← 3-tier fallback chain
│
├── CookieStore                ← Netscape format cookies
├── DownloadManager            ← HTTP download + progress
└── BrowserAutomation          ← Playwright (Douyin fallback only)
```

## ❓ FAQ

<details>
<summary><strong>yt-dlp errors or extraction fails</strong></summary>

Update yt-dlp to the latest version:
```bash
pip install --upgrade yt-dlp
```
</details>

<details>
<summary><strong>Douyin downloads fail</strong></summary>

VDL tries 3 methods automatically: yt-dlp → API → Playwright. If all fail, install the Playwright browser:
```bash
playwright install chromium
```
</details>

<details>
<summary><strong>How to use proxies</strong></summary>

Set environment variables:
```bash
export HTTPS_PROXY=http://127.0.0.1:7897
vdl https://www.youtube.com/watch?v=xxx
```
</details>

<details>
<summary><strong>Cookie issues</strong></summary>

- Cookies must be in Netscape format (use "Get cookies.txt" browser extension)
- Some platforms rotate sessions frequently — re-export if downloads start failing
- Example files are in `cookies/*.txt.example`
</details>

<details>
<summary><strong>How to use the MCP Server</strong></summary>

VDL includes an MCP server for AI tool integration:
```bash
python mcp_server.py
```
Exposes 4 tools: `download_video`, `batch_download`, `get_video_info`, `list_platforms`.
Works with Claude Desktop, Cline, and other MCP-compatible clients.
</details>

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests first (TDD)
4. Commit your changes (`git commit -m 'feat: add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

```bash
# Development setup
git clone https://github.com/zaynzhu/vdl.git
cd vdl
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run linter
black video_downloader/ && flake8 video_downloader/
```

## ⭐ Star History

<a href="https://star-history.com/#zaynzhu/vdl&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=zaynzhu/vdl&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=zaynzhu/vdl&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=zaynzhu/vdl&type=Date" />
 </picture>
</a>

## 🙏 Contributors

<a href="https://github.com/zaynzhu/vdl/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=zaynzhu/vdl" />
</a>

## 📄 License

MIT License -- see [LICENSE](LICENSE) for details.
