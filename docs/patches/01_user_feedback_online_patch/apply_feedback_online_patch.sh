#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/www/wwwroot/n2s.cc.cd}"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
ROUTES_FILE="$BACKEND_DIR/app/api/routes.py"
MAIN_FILE="$FRONTEND_DIR/src/main.jsx"
CSS_FILE="$FRONTEND_DIR/src/styles.css"
ENV_FILE="$BACKEND_DIR/.env"

echo "===== 0. 取消交互 alias，避免 cp 卡住 ====="
unalias cp 2>/dev/null || true
unalias rm 2>/dev/null || true
unalias mv 2>/dev/null || true

echo "===== 1. 备份文件 ====="
BACKUP_TIME="$(date +%Y%m%d%H%M%S)"
/bin/cp -f "$ROUTES_FILE" "$ROUTES_FILE.bak.feedback_online.$BACKUP_TIME"
/bin/cp -f "$MAIN_FILE" "$MAIN_FILE.bak.feedback_online.$BACKUP_TIME"
/bin/cp -f "$CSS_FILE" "$CSS_FILE.bak.feedback_online.$BACKUP_TIME"

echo "===== 2. 清理 .env 中误加字段，避免 Pydantic Settings 报错 ====="
sed -i '/^FEEDBACK_ADMIN_TOKEN=/d' "$ENV_FILE" 2>/dev/null || true
sed -i '/^FEEDBACK_DIR=/d' "$ENV_FILE" 2>/dev/null || true

echo "===== 3. 后端追加 /api/feedback ====="
python3 - <<'PY'
from pathlib import Path
routes = Path("/www/wwwroot/n2s.cc.cd/backend/app/api/routes.py")
snippet = Path("./backend_feedback_routes_snippet.py").read_text(encoding="utf-8")
text = routes.read_text(encoding="utf-8")
marker = "# ===== N2S real feedback endpoint ====="
if marker not in text:
    routes.write_text(text.rstrip() + "\n\n" + snippet + "\n", encoding="utf-8")
    print("OK: feedback endpoint appended")
else:
    print("OK: feedback endpoint already exists")
PY

echo "===== 4. 前端替换 FeaturesPage ====="
python3 - <<'PY'
from pathlib import Path
import re
main = Path("/www/wwwroot/n2s.cc.cd/frontend/src/main.jsx")
replacement = Path("./frontend_FeaturesPage_feedback.jsx").read_text(encoding="utf-8")
text = main.read_text(encoding="utf-8")
new_text, count = re.subn(
    r"function FeaturesPage\(\)\s*\{.*?\n\}\n\nfunction App\(",
    replacement + "\n\nfunction App(",
    text,
    flags=re.S
)
if count != 1:
    raise SystemExit(f"FeaturesPage replace failed, count={count}")
main.write_text(new_text, encoding="utf-8")
print("OK: FeaturesPage replaced")
PY

echo "===== 5. 追加反馈样式 ====="
python3 - <<'PY'
from pathlib import Path
css_path = Path("/www/wwwroot/n2s.cc.cd/frontend/src/styles.css")
patch = Path("./frontend_feedback_chat.css").read_text(encoding="utf-8")
css = css_path.read_text(encoding="utf-8")
marker = ".feedbackChatBox"
if marker not in css:
    css_path.write_text(css.rstrip() + "\n\n" + patch + "\n", encoding="utf-8")
    print("OK: feedback css appended")
else:
    print("OK: feedback css already exists")
PY

echo "===== 6. 检查后端语法并重启，失败自动回滚 ====="
cd "$BACKEND_DIR"
source .venv/bin/activate
python -m py_compile app/api/routes.py

set +e
systemctl restart n2s-api
sleep 3
curl -fsS https://n2s.cc.cd/health >/tmp/n2s_health_check.txt 2>/tmp/n2s_health_error.txt
HEALTH_OK=$?
set -e

if [ "$HEALTH_OK" != "0" ]; then
  echo "后端启动失败，回滚 routes.py"
  /bin/cp -f "$ROUTES_FILE.bak.feedback_online.$BACKUP_TIME" "$ROUTES_FILE"
  systemctl restart n2s-api
  sleep 3
  journalctl -u n2s-api -n 80 --no-pager
  exit 1
fi

echo "OK: backend health"
cat /tmp/n2s_health_check.txt
echo ""

echo "===== 7. 构建前端 ====="
cd "$FRONTEND_DIR"
npm run build

echo "===== 8. 测试反馈接口 ====="
curl -sS -X POST "https://n2s.cc.cd/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"name":"server-test","contact":"","category":"功能建议","message":"反馈补丁测试","page":"server"}'
echo ""

echo "===== 完成 ====="
echo "反馈保存：$BACKEND_DIR/data/feedback/feedback.jsonl"
echo "反馈文档：$BACKEND_DIR/data/feedback/feedback_report.md"
