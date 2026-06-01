# VDL Web UI 设计

## 目标
本地网页界面，粘贴 URL 预览视频信息后下载。支持批量 URL、下载队列、Cookie 管理。

## 架构

```
浏览器 ←→ FastAPI (localhost:8000) ←→ VideoDownloader core
                                        ↓
                                    ./downloads/
                                    ./cookies/
```

## API

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/preview | 提取视频元数据（标题/封面/时长/画质） |
| POST | /api/download | 提交下载任务 |
| GET | /api/queue | 查询下载队列状态 |
| DELETE | /api/queue/{id} | 取消下载 |
| POST | /api/cookies | 上传 cookies.txt |
| GET | /api/cookies | 列出已上传的 cookies |
| DELETE | /api/cookies/{name} | 删除 cookie 文件 |
| GET | /api/events | SSE 推送下载进度 |

## 前端
单页 HTML，内嵌 CSS/JS。四个区域：
1. **URL 输入区** — textarea，支持多行粘贴，粘贴后自动预览
2. **预览卡片** — 标题/封面/时长/画质选择/下载按钮
3. **下载队列** — 进度条、状态、取消按钮
4. **Cookie 管理** — 上传/列表/删除

## 后端
- `video_downloader/web.py` — FastAPI 应用
- `video_downloader/web_static/index.html` — 前端文件
- 下载任务用 asyncio 后台运行，进度通过 SSE 推送
- Cookie 文件存 `./cookies/`

## 启动
```bash
vdl-web                    # 新 CLI 命令
python -m video_downloader.web  # 直接启动
```

## 依赖
新增：`fastapi`, `uvicorn[standard]`（可选依赖，不强制安装）
