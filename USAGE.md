# 📖 Video Downloader - 使用指南

本文档提供详细的使用说明和示例，帮助你快速上手 Video Downloader。

---

## 📋 目录

- [快速开始](#-快速开始)
- [命令行使用](#-命令行使用)
- [Python API 使用](#-python-api-使用)
- [常见场景](#-常见场景)
- [高级用法](#-高级用法)

---

## 🚀 快速开始

### 1. 验证安装

```bash
# 查看支持的平台
python -m video_downloader --list-platforms
```

**预期输出：**
```
📺 Supported Platforms:
  • bilibili
  • douyin
  • tiktok
```

### 2. 下载第一个视频

```bash
# 下载 B站视频（最简单的方式）
python -m video_downloader https://www.bilibili.com/video/BV1xx411c7mD
```

视频会自动下载到 `./downloads` 目录。

---

## 💻 命令行使用

### 基础命令

```bash
# 查看帮助
python -m video_downloader --help

# 查看支持的平台
python -m video_downloader --list-platforms

# 下载单个视频
python -m video_downloader [URL]

# 下载多个视频
python -m video_downloader [URL1] [URL2] [URL3]
```

### 常用参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--output` | `-o` | 指定输出目录 | `-o ./my_videos` |
| `--filename` | `-f` | 文件名模板 | `-f "{author}_{title}"` |
| `--quality` | `-q` | 视频画质 | `-q 1080P` |
| `--cookies` | `-c` | Cookie 文件路径 | `-c cookies.txt` |
| `--metadata-only` | - | 只提取信息不下载 | `--metadata-only` |
| `--verbose` | `-v` | 显示详细日志 | `-v` |
| `--quiet` | - | 静默模式 | `--quiet` |

---

## 📝 使用示例

### 示例 1: 下载到指定目录

```bash
python -m video_downloader -o ./my_videos https://www.bilibili.com/video/BV1xx411c7mD
```

### 示例 2: 自定义文件名

```bash
# 使用 作者名_标题 作为文件名
python -m video_downloader -f "{author}_{title}" https://www.douyin.com/video/123456

# 使用 平台_ID_日期 作为文件名
python -m video_downloader -f "{platform}_{id}_{date}" https://www.bilibili.com/video/BV1xx411c7mD
```

**可用变量：**
- `{title}` - 视频标题
- `{author}` - 作者名称
- `{id}` - 视频 ID
- `{date}` - 上传日期（YYYY-MM-DD）
- `{platform}` - 平台名称

### 示例 3: 批量下载

```bash
# 方式一：直接传入多个 URL
python -m video_downloader \
  https://www.bilibili.com/video/BV1xx411c7mD \
  https://www.bilibili.com/video/BV1yy411c7mE \
  https://www.douyin.com/video/123456

# 方式二：从文件读取（推荐）
python -m video_downloader --url-file urls.txt
```

**urls.txt 格式：**
```
https://www.bilibili.com/video/BV1xx411c7mD
https://www.douyin.com/video/123456
https://www.tiktok.com/@user/video/789
```

### 示例 4: 使用 Cookie

```bash
# 使用 Cookie 文件（获取高清画质或会员内容）
python -m video_downloader -c cookies.txt https://www.bilibili.com/video/BV1xx411c7mD
```

**如何获取 Cookie：**

1. 安装浏览器插件：
   - Chrome: "Get cookies.txt"
   - Firefox: "cookies.txt"

2. 登录目标网站（如 B站）

3. 使用插件导出 Cookie 为 Netscape 格式

4. 保存为 `cookies.txt`

### 示例 5: 指定画质（B站）

```bash
# 下载 1080P 画质
python -m video_downloader -q 1080P https://www.bilibili.com/video/BV1xx411c7mD

# 下载 4K 画质（需要大会员 + Cookie）
python -m video_downloader -c cookies.txt -q 4K https://www.bilibili.com/video/BV1xx411c7mD
```

**可用画质：**
- `4K` - 4K 超清（需要大会员）
- `1080P60` - 1080P 60帧（需要大会员）
- `1080P` - 1080P 高清
- `720P60` - 720P 60帧
- `720P` - 720P 高清
- `480P` - 480P 清晰
- `360P` - 360P 流畅

### 示例 6: 只查看视频信息

```bash
# 不下载，只显示视频信息
python -m video_downloader --metadata-only https://www.bilibili.com/video/BV1xx411c7mD
```

**输出示例：**
```
📺 标题: 【技术分享】Python 爬虫教程
👤 作者: TechChannel
⏱️  时长: 1234 秒
📅 日期: 2024-01-15
🎬 平台: bilibili
🎯 画质: 4K, 1080P, 720P, 480P
```

### 示例 7: 启用详细日志

```bash
# 查看详细的下载过程
python -m video_downloader -v https://www.bilibili.com/video/BV1xx411c7mD
```

---

## 🐍 Python API 使用

### 示例 1: 最简单的下载

```python
import asyncio
from video_downloader import VideoDownloader

async def main():
    downloader = VideoDownloader()
    
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    result = await downloader.download(url)
    
    if result.success:
        print(f"✅ 下载成功: {result.file_path}")
    else:
        print(f"❌ 下载失败: {result.error_message}")

asyncio.run(main())
```

### 示例 2: 自定义下载选项

```python
import asyncio
from video_downloader import VideoDownloader
from video_downloader.models import DownloadOptions

async def main():
    downloader = VideoDownloader()
    
    # 自定义选项
    options = DownloadOptions(
        output_dir="./my_videos",
        quality="1080P",
        filename_template="{author}_{title}"
    )
    
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    result = await downloader.download(url, options)
    
    if result.success:
        print(f"✅ 下载成功: {result.file_path}")
        print(f"📊 文件大小: {result.file_size / 1024 / 1024:.2f} MB")

asyncio.run(main())
```

### 示例 3: 批量下载

```python
import asyncio
from video_downloader import VideoDownloader
from video_downloader.models import DownloadOptions

async def main():
    downloader = VideoDownloader()
    
    urls = [
        "https://www.bilibili.com/video/BV1xx411c7mD",
        "https://www.douyin.com/video/123456",
        "https://www.tiktok.com/@user/video/789",
    ]
    
    options = DownloadOptions(output_dir="./batch_downloads")
    batch_result = await downloader.batch_download(urls, options)
    
    print(f"✅ 成功: {batch_result.successful}")
    print(f"❌ 失败: {batch_result.failed}")
    print(f"📊 总计: {batch_result.total}")
    
    # 查看详细结果
    for result in batch_result.results:
        if result.success:
            print(f"  ✓ {result.url}")
        else:
            print(f"  ✗ {result.url}: {result.error_message}")

asyncio.run(main())
```

### 示例 4: 提取视频信息

```python
import asyncio
from video_downloader import VideoDownloader

async def main():
    downloader = VideoDownloader()
    
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    metadata = await downloader.extract_metadata(url)
    
    print(f"📺 标题: {metadata.title}")
    print(f"👤 作者: {metadata.author}")
    print(f"⏱️  时长: {metadata.duration} 秒")
    print(f"📅 日期: {metadata.upload_date}")
    print(f"📝 描述: {metadata.description}")
    print(f"🖼️  封面: {metadata.thumbnail_url}")
    print(f"🎯 画质: {', '.join(metadata.available_qualities)}")

asyncio.run(main())
```

### 示例 5: 带进度显示的下载

```python
import asyncio
from video_downloader import VideoDownloader
from video_downloader.models import DownloadOptions, DownloadProgress

def progress_callback(progress: DownloadProgress):
    """下载进度回调"""
    percent = progress.downloaded / progress.total * 100
    speed_mb = progress.speed / 1024 / 1024
    
    print(f"\r下载进度: {percent:.1f}% | "
          f"速度: {speed_mb:.2f} MB/s | "
          f"已下载: {progress.downloaded / 1024 / 1024:.1f} MB",
          end="")

async def main():
    downloader = VideoDownloader()
    
    options = DownloadOptions(
        output_dir="./downloads",
        progress_callback=progress_callback
    )
    
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    result = await downloader.download(url, options)
    
    print()  # 换行
    if result.success:
        print(f"✅ 下载完成: {result.file_path}")

asyncio.run(main())
```

### 示例 6: 完整的错误处理

```python
import asyncio
from video_downloader import VideoDownloader
from video_downloader.exceptions import (
    UnsupportedPlatformError,
    VideoNotFoundError,
    NetworkError,
    AntiBotDetectedError
)

async def main():
    downloader = VideoDownloader()
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    
    try:
        result = await downloader.download(url)
        print(f"✅ 下载成功: {result.file_path}")
        
    except UnsupportedPlatformError as e:
        print(f"❌ 不支持的平台: {e}")
        print("提示: 使用 --list-platforms 查看支持的平台")
        
    except VideoNotFoundError as e:
        print(f"❌ 视频不存在: {e}")
        print("提示: 检查 URL 是否正确，视频是否已被删除")
        
    except AntiBotDetectedError as e:
        print(f"❌ 触发反爬虫检测: {e}")
        print("建议: 使用 Cookie 文件或减少请求频率")
        
    except NetworkError as e:
        print(f"❌ 网络错误: {e}")
        print("建议: 检查网络连接或使用代理")
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")

asyncio.run(main())
```

### 示例 7: 自定义配置

```python
from video_downloader import VideoDownloader
from video_downloader.config import DownloaderConfig

# 创建自定义配置
config = DownloaderConfig(
    output_dir="./my_downloads",
    cookie_file="./cookies.txt",
    filename_template="{author}_{title}",
    timeout=60,
    max_retries=5,
    headless=True,
    enable_stealth=True,
    proxy="http://127.0.0.1:7890",
)

# 使用自定义配置
downloader = VideoDownloader(config)
```

---

## 🎯 常见场景

### 场景 1: 下载 B站视频

```bash
# 普通视频
python -m video_downloader https://www.bilibili.com/video/BV1xx411c7mD

# 高清视频（需要登录）
python -m video_downloader -c cookies.txt -q 1080P https://www.bilibili.com/video/BV1xx411c7mD

# 4K 视频（需要大会员）
python -m video_downloader -c cookies.txt -q 4K https://www.bilibili.com/video/BV1xx411c7mD
```

### 场景 2: 下载抖音视频

```bash
# 普通视频
python -m video_downloader https://www.douyin.com/video/123456

# 图集（多张图片）
python -m video_downloader https://www.douyin.com/video/789012
# 会自动识别并下载所有图片
```

### 场景 3: 下载 TikTok 视频

```bash
python -m video_downloader https://www.tiktok.com/@user/video/123456
```

### 场景 4: 批量下载播放列表

```bash
# 1. 创建 urls.txt 文件，每行一个 URL
# 2. 运行批量下载
python -m video_downloader --url-file urls.txt -o ./playlist
```

### 场景 5: 下载并自动分类

```bash
# 按平台分类
python -m video_downloader -f "{platform}/{title}" [URL]

# 按作者分类
python -m video_downloader -f "{author}/{title}" [URL]

# 按日期分类
python -m video_downloader -f "{date}/{title}" [URL]
```

---

## 🔧 高级用法

### 1. 使用代理

```python
from video_downloader import VideoDownloader
from video_downloader.config import DownloaderConfig

config = DownloaderConfig(
    proxy="http://127.0.0.1:7890"  # HTTP 代理
    # proxy="socks5://127.0.0.1:1080"  # SOCKS5 代理
)

downloader = VideoDownloader(config)
```

### 2. 自定义 User-Agent

```python
config = DownloaderConfig(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

downloader = VideoDownloader(config)
```

### 3. 调整重试策略

```python
config = DownloaderConfig(
    max_retries=5,      # 最大重试次数
    timeout=120,        # 超时时间（秒）
)

downloader = VideoDownloader(config)
```

### 4. 禁用无头浏览器（调试用）

```python
config = DownloaderConfig(
    headless=False  # 显示浏览器窗口
)

downloader = VideoDownloader(config)
```

### 5. 自定义下载块大小

```python
config = DownloaderConfig(
    chunk_size=2 * 1024 * 1024  # 2MB 块大小
)

downloader = VideoDownloader(config)
```

---

## 💡 实用技巧

### 技巧 1: 快速测试 URL

```bash
# 先查看视频信息，确认 URL 正确
python -m video_downloader --metadata-only [URL]

# 确认无误后再下载
python -m video_downloader [URL]
```

### 技巧 2: 批量下载前验证

```python
import asyncio
from video_downloader import VideoDownloader

async def validate_urls(urls):
    """验证 URL 列表"""
    downloader = VideoDownloader()
    valid_urls = []
    
    for url in urls:
        try:
            metadata = await downloader.extract_metadata(url)
            print(f"✓ {url} - {metadata.title}")
            valid_urls.append(url)
        except Exception as e:
            print(f"✗ {url} - {e}")
    
    return valid_urls

# 使用
urls = ["url1", "url2", "url3"]
valid_urls = asyncio.run(validate_urls(urls))
```

### 技巧 3: 自动重命名冲突文件

下载器会自动处理文件名冲突，在文件名后添加数字：
- `video.mp4`
- `video_1.mp4`
- `video_2.mp4`

### 技巧 4: 使用环境变量

```bash
# 设置默认输出目录
export VIDEO_DOWNLOADER_OUTPUT_DIR="./my_videos"

# 设置默认 Cookie 文件
export VIDEO_DOWNLOADER_COOKIE_FILE="./cookies.txt"
```

---

## ❓ 常见问题

### Q: 下载速度慢怎么办？
A: 
- 使用代理服务器
- 选择较低的画质
- 检查网络连接

### Q: 如何下载会员视频？
A: 
1. 登录账号并开通会员
2. 导出 Cookie
3. 使用 `-c cookies.txt` 参数

### Q: 支持断点续传吗？
A: 是的，下载中断后重新运行相同命令即可继续。

### Q: 如何批量下载整个频道？
A: 需要先获取频道所有视频的 URL，然后使用批量下载功能。

---

## 📞 获取帮助

- 查看完整文档: [README.md](README.md)
- 提交问题: [GitHub Issues](https://github.com/yourusername/video-downloader-skill/issues)
- 参与讨论: [GitHub Discussions](https://github.com/yourusername/video-downloader-skill/discussions)

---

**祝你使用愉快！** 🎉
