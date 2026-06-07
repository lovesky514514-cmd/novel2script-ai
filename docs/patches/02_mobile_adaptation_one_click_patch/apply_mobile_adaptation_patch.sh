#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/www/wwwroot/n2s.cc.cd}"
FRONTEND_DIR="$APP_DIR/frontend"
CSS_FILE="$FRONTEND_DIR/src/styles.css"

echo "===== 1. 备份 styles.css ====="
BACKUP_TIME="$(date +%Y%m%d%H%M%S)"
/bin/cp -f "$CSS_FILE" "$CSS_FILE.bak.mobile_adaptation.$BACKUP_TIME"

echo "===== 2. 清理旧手机补丁并追加最终手机适配 ====="
python3 - <<'PY'
from pathlib import Path
css_path = Path("/www/wwwroot/n2s.cc.cd/frontend/src/styles.css")
css = css_path.read_text(encoding="utf-8")

markers = [
    ("/* ===== N2S MOBILE HOME OVERFLOW FIX START ===== */", "/* ===== N2S MOBILE HOME OVERFLOW FIX END ===== */"),
    ("/* ===== N2S MOBILE VISUAL V2 START ===== */", "/* ===== N2S MOBILE VISUAL V2 END ===== */"),
    ("/* ===== N2S MOBILE VISUAL V3 START ===== */", "/* ===== N2S MOBILE VISUAL V3 END ===== */"),
    ("/* ===== N2S MOBILE VISUAL V4 START ===== */", "/* ===== N2S MOBILE VISUAL V4 END ===== */"),
    ("/* ===== N2S MOBILE VISUAL V5 START ===== */", "/* ===== N2S MOBILE VISUAL V5 END ===== */"),
    ("/* ===== N2S MOBILE VISUAL V6 START ===== */", "/* ===== N2S MOBILE VISUAL V6 END ===== */"),
    ("/* ===== N2S MOBILE HOME LIFT V7 START ===== */", "/* ===== N2S MOBILE HOME LIFT V7 END ===== */"),
    ("/* ===== N2S MOBILE HOME LIFT FIXED START ===== */", "/* ===== N2S MOBILE HOME LIFT FIXED END ===== */"),
    ("/* ===== N2S MOBILE FINAL ADAPTATION START ===== */", "/* ===== N2S MOBILE FINAL ADAPTATION END ===== */"),
]
for start, end in markers:
    if start in css and end in css:
        css = css.split(start)[0] + css.split(end)[1]

patch = Path("./mobile_final_adaptation.css").read_text(encoding="utf-8")
css_path.write_text(css.rstrip() + "\n\n" + patch + "\n", encoding="utf-8")
print("OK: mobile css applied")
PY

echo "===== 3. 构建前端 ====="
cd "$FRONTEND_DIR"
npm run build

echo "===== 4. 测试 ====="
curl -I https://n2s.cc.cd
curl https://n2s.cc.cd/health
