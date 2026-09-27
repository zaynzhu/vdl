# YouTube 下载 403 / 反爬坑

> 结论速览：
>
> - **现成方案**：`HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 yt-dlp --cookies-from-browser chrome -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -o "downloads/%(title).70s.%(ext)s" <URL>`，前提 yt-dlp 是 brew 最新版（≥2026.x）。
> - **适用条件**：macOS Apple Silicon 本机、Clash 类代理 7897 在跑、Chrome 有 YouTube 登录态；**系统 Python 3.9 环境的 `yt_dlp` 模块（pip 最高只到 2025.10.14）不行**，会 403。
> - **4K/2160p**：yt-dlp 2026.08+ 三要素齐备时已直接可下（`-f "bv*[height<=2160]+ba/b"`），无需 PO Token 插件；只看 `-F` 列表不算数，要实拉一段验证。

---

## ✅ 走代理 + brew 最新版 yt-dlp + Chrome cookies 一次成功（2026-09-27）

- **为何值得记**：排查了 6 轮（直连 → 换 player_client → 浏览器 cookies → 走代理 → 换客户端 → 发现 Python 版本上限），多轮命令验证；vdl 项目内部走 `yt_dlp` Python 模块，下次下 YouTube 必再撞。
- **最终方案**（yt-dlp 2026.08.19，brew；ffmpeg 9.0.2 负责合并）：

  ```bash
  brew install yt-dlp ffmpeg   # 一次性环境准备
  HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 yt-dlp \
    --cookies-from-browser chrome \
    -f "bv*[height<=1080]+ba/b" \
    --merge-output-format mp4 \
    --newline \
    -o "downloads/%(title).70s.%(ext)s" \
    "https://www.youtube.com/watch?v=<VIDEO_ID>"
  ```

- **为什么这样做**（三个条件缺一不可）：
  1. **yt-dlp 版本**：YouTube 的流下发依赖 PO Token（Proof of Origin）反爬机制，2025.10 之后变化频繁；旧版 extractor 拿不到有效流清单。brew 版自带新 Python（≥3.10），与系统 Python 3.9 解耦。
  2. **代理**：本机直连 YouTube 被风控/劫持（表现为 bot 检测、SSL 证书主机名不匹配），走本地 Clash 类代理后消失。
  3. **cookies**：不带 cookies 报 "Sign in to confirm you're not a bot"；Chrome 有登录态即可，无需导出 Netscape 文件。
- **适用条件**：macOS + brew 的 yt-dlp ≥2026.08；代理端口以 `USAGE.md` 当时的记录为准；Linux/无代理环境条件不同，勿照搬。
- **验证证据**：真实下载 `PPrzeY7H904`（49:29）成功——日志 `Downloading 1 format(s): 399`（视频 378.46MiB）+ `f251`（音频 43.95MiB），`[Merger] Merging formats into ...mp4`；`ffprobe` 复核输出 `codec_name=av1, width=1920, height=1080, avg_frame_rate=30/1, duration=2969.034`，文件 423M。
- **交叉验证**：单 agent 多轮执行收敛，无书面审查轨迹。
- **关键步骤**：① 确认代理端口通（`curl -x http://127.0.0.1:7897 -o /dev/null -w "%{http_code}" https://www.youtube.com/` 返回 200）→ ② 用 brew 的 `yt-dlp`（`which yt-dlp` 应为 `/opt/homebrew/bin/yt-dlp`）→ ③ 带上两条 PROXY 环境变量执行。
- **易错点**：
  - `python3 -m yt_dlp` 在系统 3.9 下永远是旧版——**别用**，直接调 `yt-dlp` 可执行文件。
  - 失败运行会留下 0 字节的 `.mp4`/`.mp4.part` 和 `.ytdl` 残留，重试时 yt-dlp 误判"has already been downloaded"（显示 `100% of 0.00B`）——先 `rm downloads/*.ytdl` 并删掉 <1M 的残留再重跑。
  - 默认 `-f "bv*+ba/b"` 会选 AV1 编码（同画质体积约为 H.264 的 1/5，本例 423M vs 估算 2.1G）；要 H.264 高码率版需显式 `-f "bv*[vcodec^=avc1][height<=1080]+ba/b"`。

## ⛔ 系统 Python 3.9 + pip yt-dlp 2025.10.14（2026-09-27）

- **报错稳定片段**（按客户端分）：
  - 不带 cookies：`Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies`
  - 带 cookies 默认客户端（web_safari）：HLS 分片 `HTTP Error 403: Forbidden. Retrying fragment N (1/10)...`
  - `android` / `ios` / `android_vr`：`Requested format is not available`（实际是 0 个可用格式，PO Token 机制丢弃）
  - `mweb` / `web_embedded`：`Video unavailable` / `This video is unavailable`
  - `tv`：直连时 `Unable to download API page: [SSL: CERTIFICATE_VERIFY_FAILED] certificate is not valid for 'www.youtube.com'`；走代理后 `The page needs to be reloaded.`
  - `tv_simply`：`Skipping client "tv_simply" since it does not support cookies`
- **错误原因**：yt-dlp 2025.10.x 是支持 Python 3.9 的最后版本线，pip 在 3.9 下自动装旧版；2025.10 之后 YouTube 的 PO Token 机制要求新版 extractor 才能拿到完整流清单，旧版各 player_client 全部失效（`tv_simply` 则原生不支持 cookies 路径）。
- **为何不可再采用**：只要 `python3` 仍是 3.9（`/Library/Developer/CommandLineTools` 自带），`pip install -U yt-dlp` 永远装不到 ≥2026 版，此路必然再错。
- **替代方案**：本文件 ✅ 条目（brew 版 yt-dlp 可执行文件）。
- **判定时效**：基于 yt-dlp 2025.10.14 / Python 3.9 / YouTube 反爬策略，2026-09-27 判定；系统 Python 升级到 3.10+ 后 pip 可装新版，此坑自动消失，届时可重验 `python3 -m yt_dlp` 路径。**对 vdl 项目的直接含义**：`video_downloader/extractors/yt_dlp.py` 走 `yt_dlp` 模块，在当前环境下下 YouTube 会复现 ⛔ 报错；修复方向是让 vdl 优先调用 brew 的 `yt-dlp` 子进程或升级项目运行时 Python。

## ⛔ 直连不走代理（含浏览器 cookies 齐全时）（2026-09-27）

- **报错原文**：`ERROR: [youtube] PPrzeY7H904: Sign in to confirm you're not a bot.`；tv 客户端直连时 `SSL: CERTIFICATE_VERIFY_FAILED ... Hostname mismatch, certificate is not valid for 'www.youtube.com'`
- **报错稳定片段**：`Sign in to confirm you're not a bot`（变量上下文：视频 id、客户端名各行出现）；`certificate is not valid for 'www.youtube.com'`
- **错误原因**：直连 YouTube 被 GFW 侧干扰，SSL 主机名不匹配是连接被劫持的典型表现；YouTube 侧则对数据中心/异常 IP 触发 bot 校验。与 cookies 是否有效无关。
- **为何不可再采用**：本机网络环境下直连 YouTube 必然复现；即使某次探测侥幸通过，下载分片阶段也会 403。
- **替代方案**：所有 yt-dlp 调用前设 `HTTPS_PROXY=http://127.0.0.1:7897`（端口以 USAGE.md 为准）。
- **判定时效**：2026-09-27，强网络环境依赖；换网络环境（如海外直连）后此条不再适用。

## ✅ 4K/2160p：新版 yt-dlp 2026.08+ 已直接拿到，无需 PO Token 插件（2026-09-27）

- **为何值得记**：2025.10.14 旧版各客户端只返回到 1080p（4K 流 VP9/AV1 被 PO Token 门槛拦下，见下方 ⛔ 条目背景），曾推断需要 `bgutil-ytdlp-pot-provider` 插件 + Node 服务才能解锁 4K；实测新版已放行，避免了不必要的插件集成。
- **验证证据**（测试视频 `PPrzeY7H904`，49:29，浏览器端确认有 2160p 档；yt-dlp 2026.08.19 + 代理 7897 + Chrome cookies 三要素）：
  - `yt-dlp --cookies-from-browser chrome -F <URL>`：格式列表含 **2160p 两档**——`313` webm VP9 14301k（4.94GiB）、`401` mp4 AV1 5987k（2.07GiB），另有 1440p 两档（`271` VP9 / `400` AV1）。
  - 实拉验证：`-f "401+251" --download-sections "*0-15"` 分段下载 15 秒成功（7.8MB，含音视频合并），`ffprobe` 复核输出 `av1, 3840, 2160`——排除「格式列表可见但分片 403」的假阳性（2025.10 旧版 web_safari 客户端正是这种失败形态）。
- **结论**：`-f "bv*[height<=2160]+ba/b"` 即可下 4K；下载链路同 ✅ 首条目（代理 + brew 新版 + cookies，缺一不可）。体积参考：49 分钟视频 VP9 4.94GiB / AV1 2.07GiB（AV1 约为 VP9 的 42%），UI 磁盘预估可直接用 yt-dlp 返回的 filesize。
- **适用条件与时效**：基于 yt-dlp 2026.08.19 / 该测试视频 / 2026-09-27 判定；PO Token 机制变化频繁，若未来新版又拿不到 2160p，回退方案才是 `bgutil-ytdlp-pot-provider` 插件 + 本地 token 服务（评估过的方向，未实施）。B 站 4K 档登录 cookie 即可、无 PO Token 门槛，仍是替代路线。
- **易错点**：只看 `-F` 列表不算数，必须实际拉一段流验证（历史教训：旧版 android/ios 客户端报 `Requested format is not available` 是 0 格式，web_safari 是列表有但分片 403，两种失败形态不同）。
