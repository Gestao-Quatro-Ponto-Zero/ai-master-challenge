#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/dist/OSS.app"
CONTENTS="$APP/Contents"

mkdir -p "$CONTENTS/MacOS" "$CONTENTS/Resources"
/usr/bin/swiftc \
  -target arm64-apple-macosx13.0 \
  "$ROOT/launcher/OSSLauncher.swift" \
  -o "$CONTENTS/MacOS/OSS" \
  -framework AppKit

cat > "$CONTENTS/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDisplayName</key><string>OSS</string>
  <key>CFBundleExecutable</key><string>OSS</string>
  <key>CFBundleIdentifier</key><string>com.pedrotgon.oss</string>
  <key>CFBundleName</key><string>OSS</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0.0</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

/usr/bin/codesign --force --deep --sign - "$APP"
echo "$APP"
