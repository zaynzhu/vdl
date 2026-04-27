# 贡献指南

感谢你考虑为 Video Downloader Skill 做出贡献！

## 🎯 贡献方式

### 报告 Bug

如果你发现了 bug，请创建一个 Issue 并包含：

- **清晰的标题**：简要描述问题
- **详细描述**：问题的具体表现
- **复现步骤**：如何重现这个问题
- **预期行为**：你期望发生什么
- **实际行为**：实际发生了什么
- **环境信息**：
  - 操作系统（Windows/Linux/Mac）
  - Python 版本
  - 相关依赖版本
- **日志或截图**：如果有的话

### 提出新功能

如果你有新功能的想法：

1. 先创建一个 Issue 讨论这个功能
2. 说明为什么需要这个功能
3. 描述功能的具体实现方式
4. 等待维护者反馈

### 提交代码

1. **Fork 仓库**
   ```bash
   # 在 GitHub 上点击 Fork 按钮
   ```

2. **克隆你的 Fork**
   ```bash
   git clone https://github.com/your-username/vdl-skill.git
   cd vdl-skill
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **安装开发依赖**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

5. **进行修改**
   - 编写代码
   - 添加测试
   - 更新文档

6. **运行测试**
   ```bash
   pytest tests/ -v
   ```

7. **代码格式化**
   ```bash
   black video_downloader/
   flake8 video_downloader/
   ```

8. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

9. **推送到你的 Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

10. **创建 Pull Request**
    - 在 GitHub 上打开你的 Fork
    - 点击 "New Pull Request"
    - 填写 PR 描述

## 📝 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 使用 [Black](https://github.com/psf/black) 格式化代码
- 使用 [flake8](https://flake8.pycqa.org/) 检查代码
- 添加类型注解（Type Hints）

### Commit Message 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例：**
```
feat(bilibili): add support for 4K video download

- Implement 4K quality detection
- Add cookie authentication for premium content
- Update tests

Closes #123
```

### 测试要求

- 所有新功能必须包含测试
- 确保所有测试通过
- 测试覆盖率不低于 80%

```bash
# 运行测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=video_downloader --cov-report=html
```

### 文档要求

- 更新 README.md（如果需要）
- 添加 docstring 到新函数/类
- 更新 USAGE.md（如果添加了新功能）

## 🌟 添加新平台支持

如果你想添加新平台的支持：

1. **创建提取器文件**
   ```python
   # video_downloader/extractors/your_platform.py
   from .base import PlatformExtractor
   from ..models import VideoMetadata, DownloadOptions
   
   class YourPlatformExtractor(PlatformExtractor):
       @property
       def platform_name(self) -> str:
           return "your_platform"
       
       @property
       def url_patterns(self) -> list[str]:
           return [r"https?://your-platform\.com/.*"]
       
       async def extract_metadata(self, url: str) -> VideoMetadata:
           # 实现元数据提取
           pass
       
       async def get_download_url(self, url: str, options: DownloadOptions) -> str:
           # 实现下载链接获取
           pass
   ```

2. **注册提取器**
   ```python
   # video_downloader/extractors/__init__.py
   from .your_platform import YourPlatformExtractor
   ```

3. **添加测试**
   ```python
   # tests/test_your_platform.py
   import pytest
   from video_downloader.extractors.your_platform import YourPlatformExtractor
   
   def test_url_validation():
       extractor = YourPlatformExtractor()
       assert extractor.can_handle("https://your-platform.com/video/123")
   ```

4. **更新文档**
   - 在 README.md 的平台支持表格中添加新平台
   - 添加使用示例

## 🐛 调试技巧

### 启用详细日志

```bash
python -m video_downloader -v [URL]
```

### 使用调试器

```python
import pdb; pdb.set_trace()
```

### 查看浏览器窗口

```python
config = DownloaderConfig(headless=False)
downloader = VideoDownloader(config)
```

## 📋 Pull Request 检查清单

在提交 PR 之前，请确保：

- [ ] 代码遵循项目的代码风格
- [ ] 所有测试通过
- [ ] 添加了新功能的测试
- [ ] 更新了相关文档
- [ ] Commit message 符合规范
- [ ] 没有合并冲突
- [ ] PR 描述清晰

## 🤝 行为准则

- 尊重所有贡献者
- 接受建设性批评
- 专注于对项目最有利的事情
- 对社区成员表现出同理心

## 📞 需要帮助？

如果你有任何问题：

- 查看 [README.md](README.md)
- 查看 [USAGE.md](USAGE.md)
- 创建一个 Issue
- 在 Discussions 中提问

---

再次感谢你的贡献！🎉
