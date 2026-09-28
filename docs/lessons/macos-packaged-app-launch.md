# macOS 打包应用从 Finder 启动的坑（cwd 只读 / 环境变量 / dmg 挂载卷）

> 结论速览：
>
> - **现成方案**：PyInstaller 打包的 .app 被 Finder/LaunchServices 启动时 **cwd 是只读的 `/`**——import 链上所有相对路径的 mkdir/写文件必须 try/except 容忍或改用用户目录绝对路径；调试用 `open --stdout <log> --stderr <log> <app>` 抓真实报错（此失败形态无崩溃日志，`open` 也不继承 shell 环境变量）。
> - **适用条件**：macOS + 任意打包形态（PyInstaller 等）+ 应用启动期有相对路径写操作；终端直接跑二进制不暴露此坑，只有双击/`open` 路径会撞。

## ✅ Finder 启动 cwd 只读导致应用静默打不开（2026-09-28）

- **环境**：macOS 26 / arm64（M2 Mac mini）、Python 3.12.14、PyInstaller 6.22.3（vdl 项目 VDL.app）
- **为何值得记**：用户装了好几遍都"打不开"，排查 4 轮才定位——无崩溃日志（`~/Library/Logs/DiagnosticReports` 无 .ips）、无窗口、进程约 10 秒后静默退出；而此前从终端跑二进制验收全部通过，纯验收盲区。下次打包任何 macOS 应用都可能再撞。
- **报错原文**（`open --stderr` 抓到的真实栈，两处先后暴露；变量上下文：具体文件行号）：
  ```
  OSError: [Errno 30] Read-only file system: 'downloads'
    File "video_downloader/web.py", line 143, in <module>   ← 模块级 state = AppState()
    File "video_downloader/web.py", line 111, in __init__
    File "video_downloader/config.py", line 46, in __post_init__
    File "pathlib.py", line 1311, in mkdir

  OSError: [Errno 30] Read-only file system: 'cookies'
    File "video_downloader/web.py", line 143, in <module>
    File "video_downloader/web.py", line 118, in __init__
  ```
- **错误原因**：Finder/LaunchServices 启动的 GUI 应用 cwd 是 `/`（SIP 只读）；终端跑二进制时 cwd 是项目目录，同一个包两种结果。import 期（模块级 `state = AppState()`）就触发 mkdir，进程在创建窗口前退出；Python 异常退出不是信号崩溃，所以不产生 .ips 日志，表象就是"双击没反应"。
- **最终方案**（vdl commit `74aaf67`）：① 相对路径 mkdir 一律 `try/except OSError`（下载时以用户设置目录为准，不再依赖启动期建目录）；② cookie 目录创建失败回退 `Path.home()/".vdl"/cookies`；③ 下载目录统一跟随用户设置（默认 `~/Downloads/vdl`），彻底消除相对路径假设。
- **调试关键命令**（没有它根本看不到报错）：
  ```bash
  open --stdout /tmp/vdl_out.log --stderr /tmp/vdl_err.log /Applications/VDL.app
  sleep 12 && cat /tmp/vdl_err.log && ps aux | grep "[M]acOS/VDL"
  ```
- **验证证据**：修复后 `open` 启动 stderr 干净、进程存活，`lsappinfo list` 出现 VDL 及 `VDL Web Content` / `VDL Networking` / `VDL Graphics and Media` 渲染进程（窗口在渲染的铁证，且 "in front"）；对运行实例（`lsof` 找随机监听端口，本次 55563）curl `/api/preview` 正常返回 2160p 档；补回归测试（monkeypatch `Path.mkdir` 抛 `OSError(30)`），全量 268 passed。
- **交叉验证**：单 agent 多轮收敛（复现 → 修第一处 → 重打包暴露第二处 → 再修 → 重打包 `open` 验收）；过程记录在 `docs/handoffs/vdl-dmg-app.md`「Finder 启动修复」节。
- **关键步骤**：① `open --stderr` 复现抓栈 → ② `grep -rn "mkdir" <pkg>/` 列出全部调用点逐一排查 → ③ 补回归测试 → ④ 重打包后**必须再用 `open`**（不是终端二进制）走一遍验收。
- **易错点**：
  - `open` 不继承 shell 环境变量（launchd 环境）——靠 env 传测试端口/代理无效，自动化验收要么直接跑二进制，要么走应用内设置；
  - 终端直接跑二进制的验收 ≠ 双击验收，cwd 不同；
  - 同一 import 链常有多处 mkdir，修完第一处要重打包重验，别假设一次修完。

## ✅ dmg 安装后「应用程序里出现多个 VDL」是错觉（2026-09-28）

- **环境**：同上；vdl `VDL-0.2.0.dmg` 拖拽安装场景。
- **为何值得记**：用户被桌面/访达里的三个"VDL"迷惑以为装重复了，实际磁盘只有一个真身；只要装完不推出挂载卷，每次都会再现这种错觉。
- **真相**：三个"VDL"分别是——① `/Applications/VDL.app`（真身，唯一安装）；② **dmg 双击后的挂载卷** `/Volumes/VDL`（桌面显示一个卷图标，内含 VDL.app + Applications 符号链接，是拖拽安装的"源"）；③ Launchpad 图标（与 ① 同一 app 的入口）。`hdiutil detach /Volumes/VDL` 后只剩 ①。
- **验证证据**：`ls -d /Applications/VDL*` 仅 1 个；全盘 `mdfind -name "VDL"` 确认 Applications 范围内仅 1 个 app；`hdiutil info` 显示卷仍挂载，`hdiutil detach` 后 `ls /Volumes/ | grep -i vdl` 为空且 Applications 计数仍为 1。
- **交叉验证**：单 agent 单次核查（命令输出即证据）。
- **易错点**：dmg 装完不推出挂载卷，卷会一直在桌面/侧边栏显示，看起来像"又多了一个应用"。