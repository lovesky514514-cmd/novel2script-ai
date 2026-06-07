# ===== N2S real feedback endpoint =====
# Append this block to backend/app/api/routes.py.
# Do NOT add FEEDBACK_ADMIN_TOKEN or FEEDBACK_DIR to .env.

from datetime import datetime as N2SFeedbackDateTime
from pathlib import Path as N2SFeedbackPath
import json as n2s_feedback_json
import uuid as n2s_feedback_uuid
from pydantic import BaseModel as N2SFeedbackBaseModel, Field as N2SFeedbackField
from fastapi import HTTPException as N2SFeedbackHTTPException


class N2SFeedbackPayload(N2SFeedbackBaseModel):
    name: str = ""
    contact: str = ""
    category: str = "功能建议"
    message: str = N2SFeedbackField(..., min_length=1, max_length=3000)
    page: str = ""
    run_id: str = ""
    user_agent: str = ""


def _n2s_feedback_paths():
    backend_dir = N2SFeedbackPath(__file__).resolve().parents[2]
    feedback_dir = backend_dir / "data" / "feedback"
    feedback_file = feedback_dir / "feedback.jsonl"
    report_file = feedback_dir / "feedback_report.md"
    return feedback_dir, feedback_file, report_file


def _n2s_export_feedback_report(feedback_file: N2SFeedbackPath, report_file: N2SFeedbackPath):
    items = []

    if feedback_file.exists():
        for line in feedback_file.read_text(encoding="utf-8").splitlines():
            try:
                items.append(n2s_feedback_json.loads(line))
            except n2s_feedback_json.JSONDecodeError:
                continue

    lines = [
        "# Novel2Script 用户反馈汇总",
        "",
        f"导出时间：{N2SFeedbackDateTime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"反馈总数：{len(items)}",
        "",
    ]

    for index, item in enumerate(reversed(items[-200:]), 1):
        lines.extend([
            f"## {index}. {item.get('category', '未分类')}",
            "",
            f"- 时间：{item.get('created_at', '')}",
            f"- 称呼：{item.get('name', '') or '未填写'}",
            f"- 联系方式：{item.get('contact', '') or '未填写'}",
            f"- 页面：{item.get('page', '')}",
            f"- 状态：{item.get('status', 'new')}",
            "",
            item.get("message", ""),
            "",
            "---",
            "",
        ])

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("\n".join(lines), encoding="utf-8")


@router.post("/feedback")
def submit_feedback(payload: N2SFeedbackPayload):
    message = payload.message.strip()

    if not message:
        raise N2SFeedbackHTTPException(status_code=400, detail="反馈内容不能为空。")

    feedback_dir, feedback_file, report_file = _n2s_feedback_paths()
    feedback_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "id": str(n2s_feedback_uuid.uuid4()),
        "created_at": N2SFeedbackDateTime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": payload.name.strip()[:80],
        "contact": payload.contact.strip()[:120],
        "category": payload.category.strip()[:40] or "功能建议",
        "message": message[:3000],
        "page": payload.page.strip()[:80],
        "run_id": payload.run_id.strip()[:80],
        "user_agent": payload.user_agent.strip()[:240],
        "status": "new",
    }

    with feedback_file.open("a", encoding="utf-8") as file:
        file.write(n2s_feedback_json.dumps(record, ensure_ascii=False) + "\n")

    _n2s_export_feedback_report(feedback_file, report_file)

    return {
        "ok": True,
        "message": "反馈已收到。",
        "feedback_id": record["id"],
    }
