# 交接：VDL macOS dmg 桌面应用（设计转执行）

- 交接日期：2026-09-27
- 下一位角色：**执行**（按本方案实现；方案中标「建议」的部分可基于证据调整并记录理由）
- 项目根：`/Users/zaynzhu/code/claude code/project/vdl`（接手时核对实际路径）

## 1. 任务目标（用户已确认）

开发一个 macOS 桌面应用，**用现有 vdl（本项目 `video_downloader` 包）完成视频下载**，打包为可双击安装的 **.dmg**；把 **4K/2160p 下载做成画质可选项**。不做 Web 部署、不做 Windows/Linux 版本。

## 2. 必读材料（按顺序）

| 路径 | 用途 |
|------|------|
| `CLAUDE.md` 与 `AGENTS.md`（两份内容一致） | 项目规则与红线：models 字段禁回退清单、ffmpeg DASH 合并约定、命令 |
| `docs/lessons/youtube-download-403.md` | **核心环境事实**：YouTube 下载三要素、旧版 yt-dlp 全灭的失败路径、4K/PO Token 待验证条目（🔶）及其下一步验证动作 |
| `video_downloader/web.py` + `video_downloader/web_static/index.html` | **现成 Web UI**（FastAPI）：`/api/preview`（画质列表）、`/api/download`（队列）、`/api/queue`（SSE 进度）、`/api/cookies`（Netscape 文件上传/列表）。本方案的地基 |
| `docs/superpowers/specs/2026-06-01-vdl-web-ui-design.md` | Web UI 设计规格（背景参考） |
| `USAGE.md` | vdl CLI/API 用法、代理与 cookies 约定 |
| `video_downloader/core.py`、`download_manager.py`、`extractors/yt_dlp.py` | 下载内核（DownloadManager 已用 ffmpeg 合并 DASH） |

## 3. 已验证环境事实（2026-09-27 实测，来自 lessons，勿重新探索）

- 本机下 YouTube 三要素缺一不可：`HTTPS_PROXY` 代理（本机 127.0.0.1:7897）+ **yt-dlp ≥2026.08** + Chrome cookies。
- **系统 Python 3.9 不可用**：pip 只能装到 yt-dlp 2025.10.14，全部 player_client 被 PO Token 反爬挡死。构建/运行一律用 Python 3.12+（brew/uv）。
- ffmpeg 9.0.2 已通过 brew 装好（合并音视频必需）。
- `downloads/` 已被 .gitignore 忽略。
- 4K（2160p）yt-dlp 能否直接拿到**尚未验证**（lessons 🔶 条目，验证动作已写明：`yt-dlp -F <URL>` 看是否出现 2160p）。

## 4. 方案

### 4.1 技术选型（模型建议，可调整）

**主方案：pywebview 壳 + FastAPI 复用现有 Web UI + PyInstaller/py2app 打包**

- 启动链：.app 启动 → uvicorn 在 `127.0.0.1:<随机空闲端口>` 起现有 FastAPI app → pywebview 开原生窗口加载该地址 → 关窗即退出进程。
- 理由：vdl 是 Python 项目，`web.py` + `web_static/index.html` 已实现预览/下载/队列/进度/cookies 管理全套 API 与前端，复用成本最低；PyInstaller 打 Python 运行时最成熟。
- 备选（不作为首期）：Tauri + vdl CLI sidecar 单二进制——UI 更精致且利于后续自动更新，但双技术栈复杂度高，列为演进方向。
- 否决：SwiftUI 原生重写（不复用现有 UI 与内核封装，成本最高）。

### 4.2 打包要点

- 构建环境：Python 3.12（uv 或 brew），依赖中 **yt-dlp>=2026.8**（lessons 红线；`setup.py`/`requirements.txt` 现有 `>=2024.1.0` 下限过低，需一并提升——用户已知晓此事并要求全局记录，改动属本任务范围）。
- ffmpeg/ffprobe：优先 **bundle 静态构建**（macOS x86_64+arm64 universal2）到 `.app/Contents/Resources/`，运行时注入 PATH；注意 ffmpeg 许可（LGPL 配置）与关于页声明。备选：首次启动检测系统 ffmpeg，缺失时引导安装。
- `web_static/` 随 PyInstaller datas 打进包。
- dmg 生成：`hdiutil` 或 create-dmg。
- **签名（待定，需问用户）**：是否有 Apple Developer 账号？有则 codesign + notarytool 公证；没有则 ad-hoc 签名 + README 说明「右键 → 打开」绕 Gatekeeper。

### 4.3 应用功能设计

以现有 API 为底座，新增：

- **设置页**：代理 URL（默认读环境变量，可覆盖——对应本机 7897 经验）、下载目录（默认 `~/Downloads/vdl`）、cookies 来源。
- **cookies 双通道**：Netscape 文件导入为主（现有 `/api/cookies` 已支持上传）；浏览器自动读取为辅（yt-dlp `cookies-from-browser`，桌面打包环境可能遇钥匙串权限，作降级路径）。
- **画质选择**：直接消费 `/api/preview` 返回的画质列表；显示每档预计体积（yt-dlp filesize/tbr 估算）。

### 4.4 4K 可选项（分阶段，先验证再投入）

1. **阶段 1（接手者第一件事）**：brew 版 yt-dlp 2026.08+ 对 4K 视频跑 `yt-dlp -F`，确认 2160p 是否已出现在格式列表（lessons 🔶 条目的既定验证动作，命令见 lessons）。若出现 → 画质下拉天然支持 4K，只需 UI 呈现 + 磁盘空间预估（4K 约 6~10 GB / 50 分钟，lessons 估算值）。
2. **阶段 2（仅当阶段 1 拿不到 2160p）**：集成 `bgutil-ytdlp-pot-provider` 插件（pip 依赖打入包）+ token 生成端（评估 bundle Deno/Node 的体积与复杂度）；短期内 UI 可先做「4K 暂不可用，已降级 1080p」的明确提示，不阻塞首版发布。
3. **替代源提示**：B 站同源视频的 4K 档登录 cookie 即可、无 PO Token 门槛——4K 不可用时 UI 提示可尝试 B 站链接（本会话已确认 B 站支持 2160p）。

### 4.5 明确的实现边界

- 不改 `video_downloader/models.py` 字段红线（CLAUDE.md 清单）。
- 不新增未被本方案要求的功能（无账号体系、无订阅/批量任务计划、无跨平台）。
- vdl 内核（extractors/download_manager）原则上不动；确需改（如让 YtDlpExtractor 支持外部 yt-dlp 可执行文件以便热更新）先在交接文档记录再动手。
- 本机代理端口等环境值**不硬编码**进源码，一律走设置/环境变量。

## 5. 决策状态表

| 决策 | 状态 | 说明 |
|------|------|------|
| 做 dmg 应用、复用 vdl、4K 做成可选项 | 用户已确认 | 本任务起点 |
| pywebview + FastAPI + PyInstaller 技术栈 | 模型建议 | 依据：现有 Web UI 完整、Python 单栈成本最低；可基于证据换 Tauri |
| 构建 Python 3.12 + yt-dlp>=2026.8 | 模型建议（有实测证据） | lessons ⛔ 条目：3.9 + 旧版必挂 |
| bundle 静态 ffmpeg | 模型建议 | 许可配置是注意点 |
| 4K 分阶段（先验证 PO Token 是否已免） | 模型建议 | lessons 🔶 待验证条目决定走阶段 1 还是 2 |
| Apple 签名方式 | **用户已确认**（2026-09-27） | 无 Developer 账号，dmg 仅自用；维持 ad-hoc 签名。实测本机构建产物无 quarantine 标记，双击直接打开 |
| 最低 macOS 版本 | **用户已确认**（2026-09-27） | 用户 M2 Mac mini / macOS 26，对下限无偏好；维持 13.0（交接建议值，提高无功能收益） |

## 6. 项目当前状态（2026-09-27 核对）

- 分支 `main`，工作区干净（仅 `.zcodeignore` 未跟踪，系 ZCode 平台生成文件，**不入库、不删**）。
- **本地领先 `origin/main` 2 个 commit 未推送**（`ac2249c` lessons 经验库、`9c6dbef` AGENTS.md 配对 + 指针）——是否 push 由用户决定，接手者不擅自推送。
- `setup.py` version 0.2.0，entry_points 有 console_scripts（vdl CLI）。
- 测试：`python -m pytest tests/ -v`（跳过 playwright：`--ignore=tests/test_browser_automation.py`）；本机系统 Python 未装项目依赖，需自建 3.12 虚拟环境后运行——**交接时未运行过测试**。

## 7. 验收例子（建议，执行前与用户确认）

1. dmg 挂载 → 拖入 /Applications → 启动出现应用窗口（无终端黑窗）。
2. 粘贴 YouTube 链接 → 预览列出画质与预计体积 → 1080p 下载成功且音视频已合并（本机代理环境）。
3. 4K 档：阶段 1 验证通过则 2160p 可选且下载成功；未通过则 UI 有明确降级提示。
4. B 站链接 + cookies 文件导入可正常下载。
5. 无代理/断网时错误信息可读，不静默失败。
6. 全量测试在 3.12 环境通过。

## 8. 接手约定（内联，不依赖任何 skill）

- 先读第 2 节材料与项目规则文件，核对分支与工作区状态；用几句话向用户复述目标、边界和第一步，无阻塞即开工。
- 文档与代码冲突时按代码裁定并修正进度判断；**影响第 5 节「用户已确认」项的冲突**：暂停受影响部分，向用户列出差异请裁决，不按模型偏好推翻。
- 两处待定项（签名、最低 macOS 版本）不阻塞开发，但阻塞发布；开工后第一次回复时向用户问清。
- 环境缺工具（如无 brew/Node）时用等价能力，否则如实标「未验证」，不假装通过。
- 完成或受阻时：更新本文档「执行结果」一节（实际改动、偏离及理由、验证证据、剩余问题）；只有只读权限时在回复中给交回摘要。

## 执行结果

（2026-09-27 执行角色填写。接手核对与 4.4 阶段 1 验证当日完成，以下为最终状态。）

### 实际改动（均已 commit）

| Commit | 内容 |
|--------|------|
| `72189b0` build | yt-dlp 下限 >=2026.8；python_requires 提至 >=3.10（yt-dlp 2026.x 不支持 3.9，lessons 实测）；补 python-multipart（cookie 上传依赖缺失，测试复现）；新增 app extras（pywebview） |
| `01423c7` feat | `_parse_qualities` 填充 bitrate/file_size_estimate（含 tbr×duration 估算回退）；storyboard 缩略图流过滤；测试 4 条 |
| `de192f7` fix | yt_dlp extractor 支持 browser_cookies；DEFAULT_YDL_OPTS 加 remote_components（EJS solver，见内核备案 3/4）；lessons 新增 `ytdlp-ejs-challenge.md` |
| `ce2a378` feat | web.py：`/api/settings`（持久化 `~/.vdl/settings.json`，代理/下载目录/浏览器 cookies）、预览与下载共用 cookies/代理逻辑、YouTube 等 6 平台直连下载（yt_dlp API + 进度 hook + ffmpeg 合并）、真实进度 SSE；index.html：设置页、画质下拉含体积、浏览器 cookies 选项；测试 15 条 |
| `784e91b` feat | desktop.py 桌面壳（uvicorn 随机端口 + pywebview 窗口 + 关窗退出）；entry_point `vdl-app` |
| `8eda045` build | vdl.spec（PyInstaller，web_static datas + yt_dlp extractor 全收集）、scripts/build_desktop.sh（ffmpeg 静态构建下载/bundle/ad-hoc 签名/dmg）、USAGE.md 桌面应用章节 |
| lessons | `youtube-download-403.md` 🔶 4K 条目升级为 ✅；新增 `ytdlp-ejs-challenge.md`；INDEX.md 同步 |

### 阶段 1 结论（4.4）：通过，无需阶段 2

yt-dlp 2026.08.19 对测试视频 `-F` 直接返回 2160p（313 VP9 4.94GiB / 401 AV1 2.07GiB）；实拉 15 秒分段 + ffprobe 复核 3840x2160 排除假阳性。**bgutil PO Token 插件（阶段 2）不需要**。4K 下拉与体积预估已实装。

### 验证证据

- 全量测试：`pytest tests/ --ignore=tests/test_browser_automation.py -m "not integration"` → **267 passed**（3 deselected 为真实网络集成测试；其 fixture `ExtractionContext()` 缺必填字段是**现存 bug**，与本任务无关，未修）
- 真实预览（venv 与打包 .app 双环境）：YouTube 测试视频返回 8 档画质，2160p 4.94GB 在列，体积与 CLI `-F` 一致
- 真实下载：venv 环境下 480p（f244+opus）完整走通 → ffprobe 复核 vp9+opus 双流 mp4；**打包 .app 内** 144p 走通 → 双流 mp4（验证 Resources/bin 的 ffmpeg 注入生效）
- 打包产物：`dist/VDL.app`（ad-hoc 签名 com.zaynzhu.vdl，arm64）+ `dist/VDL-0.2.0.dmg`（132M，含 Applications 链接，hdiutil 校验通过）
- 桌面壳：dev 与打包形态均启动正常（"VDL Desktop ready" 日志 + 进程存活）

### 偏离与待定项处理

- **两处待定项已由用户确认关闭（2026-09-27）**：① 签名 = ad-hoc 维持（无 Developer 账号，dmg 仅自用不分发；本机构建产物实测无 quarantine，双击直接打开）；② 最低 macOS = 13.0 维持（用户 M2 Mac mini / macOS 26，无偏好，提高无功能收益）。原按默认值处理的两项不再需要后续动作。
- ffmpeg bundle 选 evermeet.cx 静态 arm64 构建（77M×2）而非交接 4.2 建议的 universal2：首版目标本机 Apple Silicon，universal2 需另行编译，体积翻倍；如需 Intel 支持再扩。
- deno **未 bundle**（110M）：EJS solver 运行时依赖检测系统 PATH（本机 brew 已装）；USAGE.md 已写明 `brew install deno`。solver 脚本首次联网自动下载（remote_components 白名单）。
- `open` 启动 .app 不继承 shell 环境变量（launchd 隔离）：桌面形态的代理/端口环境变量不能依赖终端 export，靠设置页或 launchctl setenv；为此 desktop 壳加了 `VDL_DESKTOP_PORT` 测试钩子。
- web 层下载绕开 core.py 的理由与备案见「执行备案」节；**核心下载链路（yt-dlp 直连）与 lessons ✅ 条目同构，属已验证路径**。

### 剩余问题与建议下一位动作

1. ~~待用户确认：签名方式、最低 macOS 版本~~ **均已确认关闭**（见「偏离与待定项处理」）；是否 push 已执行（全部 commit 已推 origin/main）
2. ~~验收例子 1（双击启动出窗口）~~ **已完成**（见下方「Finder 启动修复」）；4K 完整下载（~5GB，代理速度约 274KB/s）建议用户自行择时验收
3. `test_ytdlp_integration.py` fixture 现存 bug（ExtractionContext 必填字段）可顺手修复
4. 未做：应用图标、自动更新（属 Tauri 演进方向）、Intel 架构

### Finder 启动修复（2026-09-28，commit 74aaf67）

用户实测双击打不开。根因：打包后从 Finder/LaunchServices 启动时 **cwd 是只读的 `/`**，import 链上三处 `mkdir`（`config.py __post_init__`、`web.py AppState` 的 `./cookies`、隐含的相对路径假设）抛 `OSError: Read-only file system`，进程静默退出（无崩溃日志、无窗口）。此前验收全部从终端跑二进制（cwd 为项目目录）故未暴露。

修复：① `DownloaderConfig.__post_init__` mkdir 失败改为容忍（下载时以用户设置目录为准）；② `AppState` cookie 目录失败回退 `~/.vdl/cookies`；③ `_make_config` 的 output_dir 跟随用户设置（默认 `~/Downloads/vdl`），消除相对路径。补回归测试（模拟只读 mkdir）。

验收：重打包后 `open`（等价 Finder 双击）启动——stderr 干净、进程存活、窗口注册（`VDL Web Content` 等渲染进程出现）；无终端代理变量时预览照常（系统代理被自动读取），2160p 档返回正常。修复已随 dmg 重建并替换 /Applications 安装。

## 执行备案：内核改动（按 4.5 约定先记录）

接手核对发现两处现有缺陷使 Web UI 对 YouTube 的下载/画质选择实际不可用，按 4.5 约定备案后实施最小改动：

1. **`extractors/yt_dlp.py::_parse_qualities`**（唯一的内核文件改动）：现有代码不填 `QualityOption.bitrate` / `file_size_estimate`（字段已存在但恒为 0），而 4.3 要求画质下拉显示预计体积。改动仅填充既有字段（从 format 的 `filesize`/`filesize_approx`/`tbr` 取值），不改模型字段、不改下载逻辑。
2. **Web 层下载链路绕开 core.py 对 YouTube 的坏路径**（不动 core.py/extractors 的下载逻辑）：现状 `YtDlpExtractor.get_download_urls` 对 DASH 内容（bv+ba）返回 1 个 URL（fallback `formats[-1]` 实为音频流），且 DownloadManager 直接拉 googlevideo URL 未经验证。改在 `web.py` 分流：YtDlpExtractor 覆盖的 6 平台改用 yt_dlp Python API 直连下载（lessons ✅ 验证过的链路：版本 ≥2026.8 + 代理 + cookies，含 ffmpeg 合并与进度 hook）；DouyinExtractor 等其余平台维持 `downloader.download()` 原路径。附带修复：quality 传 format_id（如 "313"）时 `_map_quality` 会当高度解析失败静默回落 best——web 层直连下载自行组装 format selector，不再经过该函数。
3. **`extractors/yt_dlp.py` 的 `extract_metadata`/`get_download_urls`/`_build_opts` 增加 keyword-only 参数 `browser_cookies`**：对应 yt-dlp 的 `cookiesfrombrowser` 选项。原因：YouTube 无 cookies 时预览必报 bot 检测（lessons 三要素），预览必须与下载共用同一 cookies/代理逻辑；现有 `_build_opts` 只支持 cookiefile，浏览器 cookies（桌面应用主通道之一，交接 4.3）无法到达 yt-dlp。属参数扩展，不改既有行为与签名兼容性。
4. **`extractors/yt_dlp.py` 的 `DEFAULT_YDL_OPTS` 增加 `'remote_components': ['ejs:github']`**：yt-dlp 2026.8 起解 YouTube JS 挑战（n challenge）需要 EJS solver 组件，pip 模块环境默认缺失，报错形态为 `n challenge solving failed` → `The page needs to be reloaded`，预览/下载全挂（venv CLI 复现，brew CLI 因 formula 自带 deno 依赖而幸免）。该 opt 只是「允许获取」白名单，需要时才下载 solver 脚本并缓存，对 B 站等其他平台无副作用。运行时依赖 deno（brew CLI 已带）；桌面打包需 bundle deno 二进制或 README 说明依赖（见打包节）。详见 `docs/lessons/ytdlp-ejs-challenge.md`。
