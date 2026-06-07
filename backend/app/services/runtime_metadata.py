from datetime import datetime, timezone
import hashlib
import uuid

from app.version import APP_VERSION


def make_run_id() -> str:
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def input_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def attach_runtime_metadata(result, source_text: str = "", model_status: str = ""):
    if not getattr(result, "run_id", None):
        result.run_id = make_run_id()
    if not getattr(result, "generated_at", None):
        result.generated_at = now_iso()
    if not getattr(result, "input_hash", None):
        result.input_hash = input_hash(source_text)
    if not getattr(result, "model_status", None):
        result.model_status = model_status or "deepseek_or_fallback"
    result.guard_mode = "day2_fullstack_polish"
    return result


def metadata_dict(result) -> dict:
    return {
        "app_version": APP_VERSION,
        "run_id": getattr(result, "run_id", None) or "-",
        "generated_at": getattr(result, "generated_at", None) or "-",
        "input_hash": getattr(result, "input_hash", None) or "-",
        "model_status": getattr(result, "model_status", None) or "-",
        "guard_mode": getattr(result, "guard_mode", None) or "accuracy_pipeline",
        "output_gate": "enabled",
    }
