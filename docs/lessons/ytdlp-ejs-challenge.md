# yt-dlp EJS 挑战求解器缺失（2026 版 YouTube）

> 结论速览：
>
> - **现成方案**：yt-dlp 2026.8 调 YouTube 需 EJS solver 组件——CLI 加 `--remote-components ejs:github`，Python 模块 `ydl_opts['remote_components'] = ['ejs:github']`；运行时依赖 **deno**（brew 的 yt-dlp formula 已自带 deno 依赖，pip 环境要自行 `brew install deno`）。
> - **适用条件**：yt-dlp ≥2026.x 的 YouTube 提取（预览 `-F`/元数据与实际下载都受影响）；B 站等其他平台不受影响。

## ⛔ pip/venv 环境 yt-dlp 2026.8 缺 EJS solver（2026-09-27）

- **报错稳定片段**（按出现顺序）：
  - `WARNING: [youtube] [jsc] Remote components challenge solver script (deno) and NPM package (deno) were skipped. These may be required to solve JS challenges.`
  - `WARNING: [youtube] <id>: n challenge solving failed: Some formats may be missing.`
  - 最终 `ERROR: [youtube] <id>: The page needs to be reloaded.`
- **错误原因**：yt-dlp 2026 版起 YouTube 的 n challenge / 签名挑战需要 EJS（External JS）求解器组件。`--remote-components` 默认关闭（不自动下载 solver 脚本），且需要 deno 或 node 作为求解 runtime。brew 安装的 yt-dlp 把 deno 列为 formula 依赖（`brew deps yt-dlp` 可见），所以 brew CLI 直接可用；pip/venv 环境只有 yt-dlp 本体，n challenge 失败 → YouTube 返回"页面需要刷新"，预览与下载全挂。
- **为何值得记**：同一版本 yt-dlp（2026.8.19），brew CLI 成功、venv CLI/Python 模块失败，极易误判为「版本差异」或「代理/cookies 问题」而反复重试。vdl 的 `yt_dlp` Python 模块路径与 `python -m yt_dlp` 都会撞上。
- **替代方案（已验证）**：
  ```bash
  # CLI
  yt-dlp --remote-components ejs:github --cookies-from-browser chrome -F <URL>
  # Python 模块
  ydl_opts = {..., 'remote_components': ['ejs:github']}
  ```
  首次运行会从 GitHub 下载 solver 脚本（`yt.solver.lib.min.js`，需代理），缓存在 `~/.cache/yt-dlp/`，之后离线可用。solver 脚本下载后，deno runtime 必须在 PATH。
- **验证证据**（2026-09-27）：venv（Python 3.12 + yt-dlp 2026.8.19）CLI 不带该参数复现三段报错；加 `--remote-components ejs:github` 后 `-F` 拿到完整格式列表（含 1440p/2160p 共 4 档）。代理 7897 + Chrome cookies 三要素齐备。
- **对桌面打包的含义**：.app 若要离线/开箱可用，需 bundle deno 二进制进 Resources 并注入 PATH；solver 脚本可接受首次联网下载（remote_components 白名单），或预缓存 `~/.cache/yt-dlp` 一并打包。
- **判定时效**：基于 yt-dlp 2026.8.19 / EJS 0.8.0 / 2026-09-27；yt-dlp 后续版本若将 EJS 默认开启或改机制，此坑自动消失，届时可重验。
