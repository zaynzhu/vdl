# VDL yt-dlp 重构设计

> 日期：2026-05-28
> 状态：已批准

## 背景

VDL 是一个多平台视频下载工具，当前支持 Bilibili、Douyin、TikTok。现有实现（`E:\code\codex\project-y`）架构设计良好，但各平台 extractor 实现不完整：

- Bilibili：基本能用，但 DASH 视频+音频未合并（无声），高画质受限
- Douyin：API 调用缺少 X-Bogus 签名，实际跑不通
- TikTok：同理，缺少 A-Bogus 签名

目标平台扩展为：YouTube、Bilibili、Douyin、Twitter/X、Instagram、TikTok。

## 核心决策

**yt-dlp 做主力，自研代码做补充。** 不重复造轮子。

- yt-dlp 已内置支持 YouTube、Bilibili、Twitter/X、Instagram、TikTok、Douyin
- yt-dlp 自动处理 DASH 合并（通过 ffmpeg）、画质选择、Cookie 认证
- 自研代码专注 Douyin 的三级 fallback（yt-dlp 失效时的备选方案）
- Bilibili 自研 extractor 保留为 yt-dlp 的备选

## 架构

```
VideoDownloader (core.py)
│
├── PlatformManager (platform_manager.py)
│   ├── YtDlpExtractor        ← 新增，覆盖 6 个平台
│   ├── DouyinExtractor        ← 改造，三级 fallback
│   └── BilibiliExtractor      ← 保留，yt-dlp 的备选
│
├── CookieStore                ← 保留，cookies.txt 管理
├── DownloadManager            ← 保留，文件下载 + 进度
├── BrowserAutomation          ← 保留，仅 Douyin Playwright fallback 用
│
├── cli.py                     ← 改造，CLI 入口
└── mcp_server.py              ← 改造，MCP Server
```

## YtDlpExtractor

核心新增模块，基于 `yt_dlp.YoutubeDL` 封装。

### 支持平台

| 平台 | yt-dlp extract_key | 备注 |
|------|-------------------|------|
| YouTube | `youtube` | 完美支持 |
| Bilibili | `bilibili` | 完美支持（含 DASH 合并） |
| Twitter/X | `twitter` | 能用 |
| Instagram | `instagram` | 能用 |
| TikTok | `tiktok` | 能用 |
| Douyin | `douyin` | 经常失效 → fallback |

### 设计要点

1. **只提取不下载** — `extract_metadata()` 和 `get_download_urls()` 只拿信息，不触发下载。实际下载由 `DownloadManager` 处理，保持与现有架构一致。

2. **yt-dlp 选项动态构建** — 根据平台和 Cookie 配置动态生成 `ydl_opts`：
   - 有 Cookie → `cookiefile` 参数
   - 有代理 → `proxy` 参数
   - 画质选择 → `format` 参数（默认 `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best`）

3. **同步转异步** — yt-dlp 是同步库，用 `asyncio.to_thread()` 包装，不阻塞事件循环。

4. **元数据映射** — yt-dlp 的 `extract_info()` 返回字段映射到 `VideoMetadata`：
   - `title` → `title`
   - `uploader` → `author`
   - `duration` → `duration`
   - `thumbnail` → `thumbnail_url`
   - `formats` → `quality_options`（解析可用画质列表）

5. **错误处理** — yt-dlp 异常映射到自定义异常体系（`PlatformError`、`VideoUnavailableError` 等）。

### URL 匹配

```python
SUPPORTED_PATTERNS = {
    'youtube':   r'https?://(?:www\.)?(?:youtube\.com|youtu\.be)/',
    'bilibili':  r'https?://(?:www\.)?bilibili\.com/video/',
    'twitter':   r'https?://(?:www\.)?(?:twitter\.com|x\.com)/',
    'instagram': r'https?://(?:www\.)?instagram\.com/',
    'tiktok':    r'https?://(?:www\.)?tiktok\.com/',
    'douyin':    r'https?://(?:www\.)?douyin\.com/',
}
```

## DouyinExtractor（三级 fallback）

抖音是最复杂的平台，设计三级 fallback 链：

```
DouyinExtractor.extract_metadata(url)
│
├── Level 1: yt-dlp（快，但经常失效）
│   └── 失败 →
├── Level 2: Douyin_TikTok_Download_API（中等，社区维护）
│   └── 失败 →
└── Level 3: Playwright 浏览器（慢，但最稳定）
```

### Level 1 — yt-dlp

复用 YtDlpExtractor 的逻辑，传入抖音 URL。大部分时候能用，签名更新期间会失效。

### Level 2 — Douyin_TikTok_Download_API

集成 [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) 的核心签名逻辑。该库使用 JS RPC 方式生成签名，比纯 Python 逆向更稳定。

### Level 3 — Playwright

用 `BrowserAutomation` 模块打开抖音页面，注入 JS 拿到签名后的 API 参数，然后请求 API 获取视频信息。最慢但最稳定。

### 配置

- 每一级 fallback 都有独立的超时和错误处理
- Level 1 失败时自动降级，用户无感
- 可通过配置跳过某一级（如 `douyin_skip_ytdlp=True`）
- Playwright fallback 需要 `playwright install chromium`

## BilibiliExtractor（备选）

保留 project-y 的自研 Bilibili extractor 作为 yt-dlp 的备选。当 yt-dlp 的 Bilibili 支持更新不及时时 fallback。

已知问题（需后续修复）：
- DASH 视频+音频流未合并
- 高画质需要 Cookie 但未动态检测可用画质

## CLI

```bash
# 基本用法
vdl download "https://www.bilibili.com/video/BV1xx411c7mD"

# 指定画质和输出目录
vdl download "https://www.youtube.com/watch?v=xxx" -q 1080p -o ./videos

# 批量下载
vdl download url1 url2 url3

# 只获取信息不下载
vdl info "https://www.douyin.com/video/123456"

# 列出支持的平台
vdl platforms

# 指定 Cookie 文件
vdl download "https://www.bilibili.com/video/BV1xx" --cookies ./cookies/bilibili.txt
```

入口点：`setup.py` 的 `console_scripts` → `vdl = video_downloader.cli:main`

## MCP Server

保留 project-y 的 MCP server 架构，修复已知 bug（`result.url` 不存在），暴露 4 个工具：

| 工具 | 说明 |
|------|------|
| `download_video` | 下载单个视频（url, quality, output_dir, cookies） |
| `batch_download` | 批量下载（urls[], output_dir） |
| `get_video_info` | 获取视频信息不下载（url） |
| `list_platforms` | 列出支持的平台 |

MCP server 通过 stdio 模式运行，可接入 Claude Desktop、Cline 等 AI 工具。

## Cookie 管理

使用 cookies.txt 文件（Netscape 格式），每个平台一个文件：

```
cookies/
├── bilibili.txt
├── douyin.txt
├── youtube.txt
└── *.txt.example    ← 示例文件，提交到 Git
```

yt-dlp 原生支持 `--cookies` 参数，直接传入文件路径即可。CookieStore 保留用于自研 extractor 的 Cookie 管理。

## 文件结构

```
vdl/
├── video_downloader/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py
│   ├── config.py
│   ├── models.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── cookie_store.py
│   ├── download_manager.py
│   ├── browser_automation.py
│   ├── browser_fingerprint.py
│   ├── anti_bot_strategy.py
│   ├── anti_bot_signature.py
│   ├── platform_manager.py
│   ├── cli.py
│   └── extractors/
│       ├── __init__.py
│       ├── base.py
│       ├── yt_dlp.py         ← 新增
│       ├── douyin.py          ← 改造
│       └── bilibili.py        ← 保留
├── mcp_server.py
├── tests/
├── cookies/
│   ├── bilibili.txt.example
│   └── douyin.txt.example
├── README.md
├── USAGE.md
├── CONTRIBUTING.md
├── requirements.txt
├── setup.py
└── .gitignore
```

## 依赖变化

```txt
# 新增
yt-dlp>=2024.1.0

# 保留
aiohttp>=3.9.0
playwright>=1.40.0
httpx>=0.25.0
python-dateutil>=2.8.2
```

## 从 project-y 迁移

| 文件 | 动作 |
|------|------|
| `video_downloader/` 整个包 | 复制到 vdl |
| `mcp_server.py` | 复制到 vdl |
| `tests/` | 复制到 vdl |
| `quick_start.py` | 复制到 vdl |
| `test_integration.py` | 复制到 vdl |

## 实现顺序

| 阶段 | 内容 | 预计工作量 |
|------|------|-----------|
| 1 | 搬代码到 vdl + 加 yt-dlp 依赖 | 半小时 |
| 2 | 实现 YtDlpExtractor | 2-3 小时 |
| 3 | 改造 DouyinExtractor（三级 fallback） | 3-4 小时 |
| 4 | 改造 PlatformManager 注册逻辑 | 半小时 |
| 5 | 修复 MCP Server bug | 半小时 |
| 6 | 改造 CLI | 1 小时 |
| 7 | 测试 + 文档更新 | 1-2 小时 |

## 不做的事情

- 不做 GUI
- 不做抖音签名算法逆向（用 Playwright 替代）
- 不做 Bilibili DASH 合并（yt-dlp 已处理）
- 不做多用户/账号体系
