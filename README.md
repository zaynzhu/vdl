# Video Downloader Skill

****

支持抖音、B站、TikTok 等平台，具备反爬虫检测绕过能力

## 特性

 � 多平台Bilibili、（4K/1080P/720P等）Douyin（抖音）TikTok支持抖音下载
 � 
- 🎭 浏览器指纹伪装
- 🤖 浏览器自动化Playwright
- 📥 断点续传和
- 🎯 质量选择B站支持多画质
- � 批量下载
 🛠️ 命令行界面

## 安装

命令行使用](#-命令行)
- [Python API#python-api-## )
- [常见问题](#-常见问题前置要求

- Python3.8 
-pip 

### 安装步骤

 1. 克隆仓库
git clone https://github.com/yourusername/video-downloader-skill.git
cdvideo-downloader-skill

 2. 安装依赖
pip install-r requirements.txt

3. 安装 Playwright 浏览器（用于抖音和 TikTok）**预期输出：**```支持的平台:
 - bibii(Blibili)
   uyi (Duyin)
   tktok(TikT)
```

---

##🎯 快速开始### 最简单的使用方式

#下载 B站视频
th - _ http://www.bibii.com/vie/BV1xx4117mD

#下载抖音视频
pythom ieo_er http/www.uyi.cm/vieo/123456

# 下载 TikTok 视频
python -m_ http://www.tikto.com/@user/vdeo/123456####� 命令行```bash
python -m video_downloader -o ./my_videos hw.iomvideo4
```

### 自定义文件名模板
```bash

python -m video_downloader -f "{author}_{title}" hdonomide
```

可用模板变量：
- `{title}` - 视频标题
- `{author}` - 作者名称
- `{id}` - 视频 ID
- `{date}` - 上传日期
- `{platform}` - 平台名称

### 批量下载

```bash
python -m video_downloader url1 url2 url3
```
**示例**```
```

### 使用 Cookie（获取高清画质）
```bash

python -m video_downloader -c cookies.txt pwbilibilicoieox```


Cookie 件e 为 Netscap格式
```**可用**- `4K`超清（）- `1080P60` 帧（）- `1080P` 高清- `720P60` 帧- `720P` 高清- `480P` 清晰- `360P` 流畅

### 6. 仅提取元数据
bash
python -m video_downloader --metadata-only
```****
``` h:ce1411
```

### 

```bash
python -m video_downloader --st-platorms
```

---# 🐍 Python API 使用

 使用

```python
import asyncio
from video_downloader import VideoDownloader
from video_downloader.models import DownloadOptions

async def main():
    # 创建下载器
    downloader = VideoDownloader()
    
    # 下载视频
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    options = DownloadOptions(
        output_dir="./downloads",
        quality="1080P"
    )
    
    result = await downloader.download(url, options)
    
    if result.success:
        print(f" 下载成功: {result.file_path}")
   else:
        print(f" 下载失败:{result.error_message}")
   
     批量下载
    
    urls = [    https://www.bilibili.com/video/BV1xx411c7mD"douyin.com/video/123456",
        "htps://www.t",]
    
    batch_result = await downloader.batch_download(urls, options)
    
    print(f"成功: {batch_result.successful} 失败: {batch_result.failed}")
   
    #  提取元数据
    metadata  =awaawit donloader.extract_metadata(url)
    
    print(f"标题: {metadata.title}")
    print(f"作者: {metadata.uthor}") print(f"时长:{metadata.duration}秒")

if _name == "mai"
    asyncio.run(ma())
```

### . 自定义配置

```python
from video_downloader import VideoDownloader
from video_downloaderconfig import DownloaderConfig
config=DownloaderConfig(
  outut_di="./my_dwnloads",
    cookie_file="./cookies.tt",
    filename_template="{author}_{title}",
    timeout=60,
    max_retries=5,
    headless=True,  # 无头浏览器模式
    enable_stealth=True,  # 启用反检测
    prox
)

downloader = VideoDownloader(config)
```

##  

ooi
 et ooie.t ooie
 escape ooe
    下载      ooe    
             in |             |            on    B 
        en

  ooie
     
    
    otio = 
        oila
       prgsallcro
    
    
    sul  itle
        sio1
     i
    
     行
     

iodownloadt_roge
``

### 

```h
pt as
 video_downloader ideoownloader
om video_downlader


 



dedownloader
 ore                latonaer.    rtrs
            ep          
        
    doun        
            iodoae    ite       Cookie
    
 etoo  
                接
 
 cense
 

sule




## ⚙️ 配置选项

### DownloaderConfig 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_dir` | str | `"./downloads"` | 下载文件保存目录 |
| `cookie_file` | str | `None` | Cookie 文件路径（Netscape 格式） |
| `filename_template` | str | `"{title}"` | 文件名模板 |
| `timeout` | int | `60` | 请求超时时间（秒） |
| `max_retries` | int | `3` | 最大重试次数 |
| `headless` | bool | `True` | 是否使用无头浏览器模式 |
| `enable_stealth` | bool | `True` | 是否启用反检测技术 |
| `proxy` | str | `None` | 代理服务器地址 |
| `user_agent` | str | `None` | 自定义 User-Agent |

### Cookie 管理

对于需要登录才能访问的内容（如 B站高清画质），需要提供 Cookie：

1. 使用浏览器插件（如 "Get cookies.txt"）导出 Cookie
2. 保存为 Netscape 格式的文本文件
3. 使用 `-c` 参数指定 Cookie 文件

---

## 🌍 支持的平台

| 平台 | 视频下载 | 图集下载 | 画质选择 | Cookie 支持 | 反爬虫签名 | 状态 |
|------|---------|---------|---------|------------|-----------|------|
| Bilibili | ✅ | ❌ | ✅ | ✅ | ✅ | 稳定 |
| Douyin | ✅ | ✅ | ❌ | ✅ | ⚠️ | 测试中 |
| TikTok | ✅ | ❌ | ❌ | ✅ | ⚠️ | 测试中 |

**说明：**
- ✅ 完全支持
- ⚠️ 功能受限，需要额外配置
- ❌ 暂不支持
- Douyin 和 TikTok 需要 X-Bogus/A-Bogus 签名才能正常工作
- 当前实现使用浏览器自动化绕过签名要求（推荐方式）
- 如需直接 API 调用，需要自行实现签名算法或使用第三方服务

---

## 🏗️ 架构设计

项目采用插件化架构，易于扩展新平台：

```
video_downloader/
├── __init__.py          # 包初始化
├── __main__.py          # CLI 入口
├── core.py              # 主入口类 VideoDownloader
├── platform_manager.py  # 平台管理器
├── download_manager.py  # 下载管理器
├── cookie_store.py      # Cookie 管理
├── browser_fingerprint.py  # 浏览器指纹
├── browser_automation.py   # 浏览器自动化
├── anti_bot_signature.py   # 反爬虫签名接口
├── anti_bot_strategy.py    # 反爬虫策略
├── config.py            # 配置管理
├── logger.py            # 日志系统
├── models.py            # 数据模型
├── exceptions.py        # 异常定义
├── cli.py               # 命令行接口
└── extractors/          # 平台提取器
    ├── __init__.py
    ├── base.py          # 抽象基类 PlatformExtractor
    ├── bilibili.py      # B站提取器
    ├── douyin.py        # 抖音提取器
    └── tiktok.py        # TikTok 提取器
```

### 核心组件说明

#### 1. VideoDownloader（核心类）
- 主入口类，协调所有组件
- 提供统一的下载接口
- 处理平台识别和路由

#### 2. PlatformManager（平台管理器）
- 管理所有平台提取器
- URL 模式匹配和平台识别
- 支持插件式扩展

#### 3. PlatformExtractor（平台提取器基类）
- 定义统一的提取器接口
- 各平台实现自己的提取逻辑
- 支持视频和图集下载

#### 4. DownloadManager（下载管理器）
- HTTP 文件下载
- 断点续传支持
- 进度跟踪和报告
- 智能重试机制

#### 5. BrowserAutomation（浏览器自动化）
- 基于 Playwright
- 反检测脚本注入
- 人类行为模拟

#### 6. CookieStore（Cookie 管理）
- 多平台 Cookie 隔离
- Netscape 格式支持
- 自动过期检查

---

## 🔧 故障排除

### 常见问题

#### 1. 403 Forbidden 错误

**原因：** 触发了反爬虫检测

**解决方案：**
- 使用 Cookie 文件：`python -m video_downloader -c cookies.txt [URL]`
- 减少并发下载数量
- 增加请求间隔时间
- 使用代理：`python -m video_downloader --proxy http://127.0.0.1:7890 [URL]`

#### 2. 超时错误

**原因：** 网络连接不稳定或服务器响应慢

**解决方案：**
- 检查网络连接
- 增加超时时间：`python -m video_downloader --timeout 120 [URL]`
- 使用代理服务器
- 重试下载

#### 3. 找不到下载链接

**原因：** 视频已被删除、设为私密或需要登录

**解决方案：**
- 确认视频是否存在
- 使用 Cookie 文件登录
- 检查视频是否需要会员权限

#### 4. Playwright 浏览器未安装

**错误信息：** `Executable doesn't exist at ...`

**解决方案：**
```bash
playwright install chromium
```

#### 5. 浏览器启动失败

**Windows 系统：**
- 确保已安装 Visual C++ Redistributable
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe

**Linux 系统：**
```bash
# Ubuntu/Debian
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2

# CentOS/RHEL
sudo yum install -y \
    nss \
    nspr \
    atk \
    at-spi2-atk \
    cups-libs \
    libdrm \
    libxkbcommon \
    libXcomposite \
    libXdamage \
    libXfixes \
    libXrandr \
    mesa-libgbm \
    alsa-lib
```

### 反爬虫签名问题

**X-Bogus (抖音) 和 A-Bogus (TikTok)：**

这些是复杂的反爬虫签名算法，需要逆向工程。当前实现提供了两种方案：

#### 方案一：浏览器自动化（推荐）
- 使用 Playwright 让浏览器自动生成签名
- **优点**：无需实现签名算法，更稳定
- **缺点**：速度较慢，资源消耗大

#### 方案二：自行实现签名算法
- 需要逆向工程最新的 JS 代码
- 需要定期更新以应对算法变化
- 参考 `video_downloader/anti_bot_signature.py` 中的接口

**如果遇到签名相关错误：**
- 确保已安装 Playwright 浏览器
- 使用 `--verbose` 参数查看详细日志
- 考虑使用第三方签名生成服务

---

## 👨‍💻 开发指南

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/video-downloader-skill.git
cd video-downloader-skill

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果有开发依赖

# 安装 Playwright
playwright install chromium
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_core.py -v

# 运行特定测试函数
pytest tests/test_core.py::test_download -v

# 查看测试覆盖率
pytest tests/ --cov=video_downloader --cov-report=html
```

### 代码格式化

```bash
# 使用 black 格式化代码
black video_downloader/

# 使用 flake8 检查代码风格
flake8 video_downloader/

# 使用 isort 排序导入
isort video_downloader/
```

### 类型检查

```bash
# 使用 mypy 进行类型检查
mypy video_downloader/
```

### 添加新平台支持

1. 在 `video_downloader/extractors/` 创建新的提取器文件
2. 继承 `PlatformExtractor` 基类
3. 实现必需的抽象方法
4. 在 `__init__.py` 中注册新平台

**示例：**

```python
# video_downloader/extractors/youtube.py
from .base import PlatformExtractor
from ..models import VideoMetadata, DownloadOptions

class YouTubeExtractor(PlatformExtractor):
    """YouTube 平台提取器"""
    
    @property
    def platform_name(self) -> str:
        return "youtube"
    
    @property
    def url_patterns(self) -> list[str]:
        return [
            r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
            r"https?://youtu\.be/[\w-]+"
        ]
    
    async def extract_metadata(self, url: str) -> VideoMetadata:
        # 实现元数据提取逻辑
        pass
    
    async def get_download_url(self, url: str, options: DownloadOptions) -> str:
        # 实现下载链接获取逻辑
        pass
```

---

## ❓ 常见问题

### Q: 支持哪些视频平台？
A: 目前支持 Bilibili（B站）、Douyin（抖音）、TikTok。更多平台正在开发中。

### Q: 可以下载会员专属内容吗？
A: 可以，但需要提供有效的 Cookie 文件。使用 `-c` 参数指定 Cookie 文件。

### Q: 下载速度慢怎么办？
A: 
- 检查网络连接
- 使用代理服务器
- 选择较低的画质
- 避免高峰时段下载

### Q: 如何批量下载整个播放列表？
A: 目前需要手动提取播放列表中的所有视频 URL，然后使用批量下载功能。

### Q: 支持下载直播回放吗？
A: 部分平台支持，具体取决于平台的 API 限制。

### Q: 如何贡献代码？
A: 请查看 [贡献指南](#-贡献指南) 部分。

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork 本仓库**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **开启 Pull Request**

### 贡献类型

- 🐛 报告 Bug
- ✨ 提出新功能
- 📝 改进文档
- 🔧 修复问题
- 🌐 添加新平台支持
- 🧪 添加测试用例

### 代码规范

- 遵循 PEP 8 代码风格
- 使用 Black 格式化代码
- 添加类型注解
- 编写单元测试
- 更新相关文档

### 提交 Issue

提交 Issue 时，请包含：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python 版本等）
- 相关日志或截图

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## ⚠️ 免责声明

本工具仅供学习和研究使用。请遵守各平台的服务条款，尊重内容创作者的版权。

- 下载的内容仅供个人使用
- 请勿用于商业目的或二次分发
- 请勿用于侵犯他人版权
- 使用本工具产生的任何法律责任由使用者自行承担

---

## 🙏 致谢

感谢以下开源项目：

- [Playwright](https://playwright.dev/) - 浏览器自动化
- [aiohttp](https://docs.aiohttp.org/) - 异步 HTTP 客户端
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载工具参考
- [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) - 抖音/TikTok API 参考

---

## 📞 联系方式

- 提交 Issue: [GitHub Issues](https://github.com/yourusername/video-downloader-skill/issues)
- 讨论区: [GitHub Discussions](https://github.com/yourusername/video-downloader-skill/discussions)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

Made with ❤️ by [Your Name]

</div>
