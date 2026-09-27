# -*- mode: python ; coding: utf-8 -*-
# VDL macOS 桌面应用打包配置（PyInstaller）
# 构建：见 scripts/build_desktop.sh

import os
from PyInstaller.utils.hooks import collect_submodules

# 项目根（venv 为 editable 安装时，包源码需通过 pathex 直接定位）
ROOT = os.path.abspath(SPECPATH)

hiddenimports = (
    collect_submodules("video_downloader")
    # yt-dlp 运行时动态加载 extractor 子模块，需整体收集
    + collect_submodules("yt_dlp.extractor")
)

a = Analysis(
    ["scripts/launcher.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[
        # Web UI 静态资源随包分发
        ("video_downloader/web_static", "video_downloader/web_static"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VDL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # macOS .app 无终端黑窗
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="VDL",
)

app = BUNDLE(
    coll,
    name="VDL.app",
    info_plist={
        "CFBundleDisplayName": "VDL",
        "CFBundleName": "VDL",
        "CFBundleIdentifier": "com.zaynzhu.vdl",
        "CFBundleShortVersionString": "0.2.0",
        "CFBundleVersion": "0.2.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "13.0",
    },
)
