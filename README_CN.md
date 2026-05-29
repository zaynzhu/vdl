<div align="center">

# 🎬 VDL

**基于 yt-dlp 的多平台视频下载器**

中文 | [English](README.md)

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
> VDL 将 yt-dlp 封装为简洁的 CLI + MCP Server，覆盖 6 大平台，支持自动 fallback。没有 GUI，没有多余功能 —— 只需 `vdl <url>` 即可下载。

## ✨ 特性

- **6 个平台，一条命令** -- YouTube、Bilibili、抖音、Twitter/X、Instagram、TikTok
- **yt-dlp 核心引擎** -- 成熟的提取方案，自动合并 DASH 音视频流
- **抖音三级 fallback** -- yt-dlp → 直接 API → Playwright 浏览器，全自动降级
- **Cookie 认证** -- Netscape 格式 cookies，支持 Bilibili 高画质
- **批量下载** -- 传入多个 URL，并发下载带进度追踪
- **MCP Server** -- 通过 Model Context Protocol 集成 AI 工具
- **文件名模板** -- 自定义 `{title}`、`{author}`、`{id}`、`{date}`、`{platform}`
- **画质选择** -- `1080p`、`720p`、`480p` 或 yt-dlp 格式字符串

## 🚀 快速开始

```bash
# 安装
git clone https://github.com/zaynzhu/vdl.git
cd vdl
pip install -e .

# 下载视频
vdl https://www.bilibili.com/video/BV1xx411c7mD

# 指定画质下载
vdl https://www.youtube.com/watch?v=xxx -q 1080p -o ./videos

# 只获取视频信息不下载
vdl --metadata-only https://www.douyin.com/video/123456

# 列出支持的平台
vdl --list-platforms
```

## 📦 安装

### 从源码安装（推荐）

```bash
git clone https://github.com/zaynzhu/vdl.git
cd vdl
pip install -e .
```

### 依赖

```bash
# 核心引擎（自动安装）
pip install yt-dlp

# 抖音 fallback（可选）
playwright install chromium
```

## 🔄 功能对比

| 功能 | VDL | youtube-dl | you-get | cobalt |
|------|:---:|:----------:|:-------:|:------:|
| YouTube | ✅ | ✅ | ✅ | ✅ |
| Bilibili（高画质） | ✅ | ⚠️ | ✅ | ❌ |
| 抖音 | ✅ | ❌ | ⚠️ | ❌ |
| Twitter/X | ✅ | ✅ | ⚠️ | ✅ |
| Instagram | ✅ | ⚠️ | ❌ | ✅ |
| TikTok | ✅ | ⚠️ | ⚠️ | ✅ |
| CLI | ✅ | ✅ | ✅ | ❌ |
| MCP Server | ✅ | ❌ | ❌ | ❌ |
| 批量下载 | ✅ | ❌ | ❌ | ❌ |
| Cookie 认证 | ✅ | ✅ | ⚠️ | ❌ |

## 💡 使用方法

### 基本下载

```bash
vdl https://www.bilibili.com/video/BV1xx411c7mD
```

### 指定画质和目录

```bash
vdl https://www.youtube.com/watch?v=xxx -q 720p -o ./my_videos
```

### 自定义文件名

```bash
vdl URL -f "{author}_{title}"
vdl URL -f "{platform}/{date}_{title}"
```

### 批量下载

```bash
vdl url1 url2 url3
```

### 使用 Cookie（Bilibili 高画质）

```bash
vdl https://www.bilibili.com/video/BV1xx -c cookies/bilibili.txt
```

### Cookie 配置

1. 复制示例文件：`cp cookies/bilibili.txt.example cookies/bilibili.txt`
2. 从浏览器导出 cookies（使用 "Get cookies.txt" 扩展）
3. 替换示例内容为真实 cookies
4. 使用：`vdl URL -c cookies/bilibili.txt`

## 📚 文档

| 主题 | 说明 |
|------|------|
| [USAGE.md](USAGE.md) | 详细使用指南 |
| [架构](#架构) | Extractor 系统工作原理 |
| [Cookie 配置](#cookie-配置) | 各平台 Cookie 设置 |
| [常见问题](#faq) | 常见问题和解决方案 |

## 🏗️ 架构

```text
VideoDownloader (core.py)
│
├── PlatformManager
│   ├── YtDlpExtractor        ← 主力，覆盖 6 个平台
│   ├── BilibiliExtractor      ← Bilibili 备选
│   └── DouyinExtractor        ← 抖音三级 fallback
│
├── CookieStore                ← Netscape 格式 cookies
├── DownloadManager            ← HTTP 下载 + 进度
└── BrowserAutomation          ← Playwright（仅抖音 fallback）
```

## ❓ FAQ

<details>
<summary><strong>yt-dlp 报错或提取失败</strong></summary>

更新 yt-dlp 到最新版本：
```bash
pip install --upgrade yt-dlp
```
</details>

<details>
<summary><strong>抖音下载失败</strong></summary>

VDL 会自动尝试 3 种方式：yt-dlp → API → Playwright。如果都失败，安装 Playwright 浏览器：
```bash
playwright install chromium
```
</details>

<details>
<summary><strong>如何使用代理</strong></summary>

设置环境变量：
```bash
export HTTPS_PROXY=http://127.0.0.1:7897
vdl https://www.youtube.com/watch?v=xxx
```
</details>

<details>
<summary><strong>Cookie 问题</strong></summary>

- Cookies 必须是 Netscape 格式（使用 "Get cookies.txt" 浏览器扩展）
- 部分平台会频繁刷新 session —— 下载失败时重新导出
- 示例文件在 `cookies/*.txt.example`
</details>

<details>
<summary><strong>如何使用 MCP Server</strong></summary>

VDL 内置 MCP Server，可接入 AI 工具：
```bash
python mcp_server.py
```
暴露 4 个工具：`download_video`、`batch_download`、`get_video_info`、`list_platforms`。
支持 Claude Desktop、Cline 等 MCP 客户端。
</details>

## 🤝 贡献

欢迎贡献！流程如下：

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/amazing-feature`）
3. 先写测试（TDD）
4. 提交更改（`git commit -m 'feat: add amazing feature'`）
5. 推送分支（`git push origin feature/amazing-feature`）
6. 发起 Pull Request

```bash
# 开发环境搭建
git clone https://github.com/zaynzhu/vdl.git
cd vdl
pip install -e ".[dev]"

# 运行测试
python -m pytest tests/ -v

# 代码格式化
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

## 🙏 贡献者

<a href="https://github.com/zaynzhu/vdl/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=zaynzhu/vdl" />
</a>

## 📄 许可证

MIT License —— 详见 [LICENSE](LICENSE)。
