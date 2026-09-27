#!/usr/bin/env bash
# VDL macOS 桌面应用构建：.app + dmg
# 用法：scripts/build_desktop.sh
# 前置：.venv（Python 3.12，含 pyinstaller）、代理环境变量（首次下载 ffmpeg 静态构建时需要）
set -euo pipefail
cd "$(dirname "$0")/.."

VENV=${VENV:-.venv}
APP_NAME=VDL
VERSION=$(python3 -c "import re; print(re.search(r'version=\"([^\"]+)\"', open('setup.py').read()).group(1))")
BUILD_DIR=build
DIST_DIR=dist

# 1. ffmpeg/ffprobe 静态构建（arm64，来自 evermeet.cx，缓存到 build/ffmpeg）
export HTTPS_PROXY=${HTTPS_PROXY:-http://127.0.0.1:7897}
export HTTP_PROXY=${HTTP_PROXY:-http://127.0.0.1:7897}
mkdir -p "$BUILD_DIR/ffmpeg"
for tool in ffmpeg ffprobe; do
  if [ ! -f "$BUILD_DIR/ffmpeg/$tool" ]; then
    echo ">> downloading static $tool..."
    curl -sL --max-time 300 "https://evermeet.cx/ffmpeg/getrelease/$tool/zip" -o "$BUILD_DIR/ffmpeg/$tool.zip"
    (cd "$BUILD_DIR/ffmpeg" && unzip -oq "$tool.zip" && rm "$tool.zip")
  fi
done

# 2. PyInstaller 打包 .app
"$VENV/bin/pyinstaller" vdl.spec --noconfirm

# 3. 注入 ffmpeg/ffprobe 到 .app/Contents/Resources/bin（运行时 desktop.py 注入 PATH）
BIN_DIR="$DIST_DIR/$APP_NAME.app/Contents/Resources/bin"
mkdir -p "$BIN_DIR"
cp "$BUILD_DIR/ffmpeg/ffmpeg" "$BUILD_DIR/ffmpeg/ffprobe" "$BIN_DIR/"

# 4. ad-hoc 签名（无 Apple Developer 账号；用户首次打开需右键 → 打开）
codesign --force --deep -s - "$DIST_DIR/$APP_NAME.app"

# 5. 打 dmg（staging 内放 Applications 符号链接，支持拖拽安装）
rm -rf "$BUILD_DIR/dmg-staging"
mkdir -p "$BUILD_DIR/dmg-staging"
cp -R "$DIST_DIR/$APP_NAME.app" "$BUILD_DIR/dmg-staging/"
ln -s /Applications "$BUILD_DIR/dmg-staging/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$BUILD_DIR/dmg-staging" -ov -format UDZO \
  "dist/$APP_NAME-$VERSION.dmg"

echo ">> done: dist/$APP_NAME.app + dist/$APP_NAME-$VERSION.dmg"
