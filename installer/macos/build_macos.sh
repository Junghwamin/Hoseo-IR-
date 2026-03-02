#!/bin/bash
# ===========================================================================
# 호서대학교 IR센터 연구실적 분석 포털 - macOS 빌드 스크립트
#
# Standalone Python을 포함한 .app 번들을 생성하고 DMG로 패키징한다.
#
# 사용법:
#   bash installer/macos/build_macos.sh
#
# 요구사항:
#   - macOS 11.0+ (GitHub Actions macos-latest에서 실행 권장)
#   - Python 3.11 (actions/setup-python으로 설치)
# ===========================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build/macos"
APP_NAME="IR센터 연구실적 분석 포털"
APP_BUNDLE="$BUILD_DIR/${APP_NAME}.app"
DIST_DIR="$PROJECT_ROOT/dist/macos"
APP_VERSION="3.0"

echo "=========================================="
echo "  IR센터 분석 포털 - macOS 빌드"
echo "=========================================="

# --- 1. 빌드 디렉토리 초기화 ---
echo ""
echo "[1/5] 빌드 디렉토리 초기화..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# --- 2. Python venv 생성 + 의존성 설치 ---
echo ""
echo "[2/5] Python 가상환경 생성 및 의존성 설치..."
VENV_DIR="$BUILD_DIR/python-venv"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"
deactivate

# --- 3. .app 번들 구조 생성 ---
echo ""
echo "[3/5] .app 번들 구조 생성..."
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources/app"
mkdir -p "$APP_BUNDLE/Contents/Resources/app/output/reports"
mkdir -p "$APP_BUNDLE/Contents/Resources/app/Raw data"

# Info.plist 복사
cp "$SCRIPT_DIR/Info.plist" "$APP_BUNDLE/Contents/Info.plist"
# Info.plist 버전 업데이트
sed -i '' "s/3.0/$APP_VERSION/g" "$APP_BUNDLE/Contents/Info.plist"

# 아이콘 복사 (있으면)
if [ -f "$SCRIPT_DIR/icon.icns" ]; then
    cp "$SCRIPT_DIR/icon.icns" "$APP_BUNDLE/Contents/Resources/icon.icns"
fi

# --- 4. 앱 파일 및 Python 환경 복사 ---
echo ""
echo "[4/5] 파일 복사..."

# Python venv 복사
cp -R "$VENV_DIR" "$APP_BUNDLE/Contents/Resources/python-venv"

# 앱 소스 코드 복사
cp -R "$PROJECT_ROOT/report_app" "$APP_BUNDLE/Contents/Resources/app/report_app"
cp -R "$PROJECT_ROOT/config" "$APP_BUNDLE/Contents/Resources/app/config"
cp -R "$PROJECT_ROOT/.streamlit" "$APP_BUNDLE/Contents/Resources/app/.streamlit"
cp "$PROJECT_ROOT/전임교원_연구실적_전처리.py" "$APP_BUNDLE/Contents/Resources/app/"
cp "$PROJECT_ROOT/requirements.txt" "$APP_BUNDLE/Contents/Resources/app/"

# __pycache__ 삭제
find "$APP_BUNDLE" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 런처 스크립트 복사 (실행 가능하게)
cp "$SCRIPT_DIR/launcher.sh" "$APP_BUNDLE/Contents/MacOS/launcher"
chmod +x "$APP_BUNDLE/Contents/MacOS/launcher"

# --- 5. DMG 생성 ---
echo ""
echo "[5/5] DMG 생성..."
mkdir -p "$DIST_DIR"
DMG_PATH="$DIST_DIR/HoseoIR_Setup_v${APP_VERSION}.dmg"

# 기존 DMG 삭제
rm -f "$DMG_PATH"

hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$APP_BUNDLE" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

echo ""
echo "=========================================="
echo "  빌드 완료!"
echo "  .app: $APP_BUNDLE"
echo "  .dmg: $DMG_PATH"
echo "=========================================="
