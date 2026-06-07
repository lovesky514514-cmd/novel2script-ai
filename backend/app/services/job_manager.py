import asyncio
import threading
import traceback
from pathlib import Path
import time
import uuid
from typing import Dict, Optional

from app.models.schemas import NovelInput
from app.services.knowledge_engine import warmup_knowledge_base
from app.services.output_gate import OutputQualityError, assert_final_payload_is_clean, finalize_result_payload
from app.services.workflow_ai import convert_ai


JOBS: Dict[str, Dict] = {}

STAGE_MIN_SECONDS = {
    "knowledge_warmup": 0.35,
    "chapter_memory": 0.35,
    "generation": 0.35,
    "validation": 0.35,
}


def create_job(payload: NovelInput) -> str:
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "stage": "queued",
        "stage_text": "等待生成",
        "progress": 0.0,
        "created_at": time.time(),
        "updated_at": time.time(),
        "elapsed_seconds": 0,
        "result": None,
        "error": None,
    }

    thread = threading.Thread(target=lambda: asyncio.run(_run_job(job_id, payload)), daemon=True)
    thread.start()
    return job_id


def _update(job_id: str, status: str, stage: str, stage_text: str, progress: float):
    job = JOBS[job_id]
    job.update({
        "status": status,
        "stage": stage,
        "stage_text": stage_text,
        "progress": progress,
        "updated_at": time.time(),
        "elapsed_seconds": int(time.time() - job["created_at"]),
    })


async def _hold_stage(seconds: float):
    await asyncio.sleep(seconds)


async def _run_job(job_id: str, payload: NovelInput):
    try:
        _update(job_id, "running", "knowledge_warmup", "正在启动知识库", 0.12)
        warmup_knowledge_base()
        await _hold_stage(STAGE_MIN_SECONDS["knowledge_warmup"])

        _update(job_id, "running", "chapter_memory", "正在构建人物与伏笔记忆", 0.32)
        await _hold_stage(STAGE_MIN_SECONDS["chapter_memory"])

        _update(job_id, "running", "generation", "正在生成分场剧本", 0.62)
        result = await convert_ai(payload)
        await _hold_stage(STAGE_MIN_SECONDS["generation"])

        _update(job_id, "running", "validation", "正在进行二次校验", 0.86)
        await _hold_stage(STAGE_MIN_SECONDS["validation"])

        JOBS[job_id]["result"] = assert_final_payload_is_clean(finalize_result_payload(result))
        _update(job_id, "done", "done", "生成完成", 1.0)
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, OutputQualityError):
            error_text = f"生成未通过校验：{exc}"
        JOBS[job_id]["error"] = error_text
        try:
            log_dir = Path(__file__).resolve().parents[2] / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / "backend_error.log").write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            pass
        _update(job_id, "error", "error", error_text, 1.0)


def get_job(job_id: str) -> Optional[Dict]:
    job = JOBS.get(job_id)
    if not job:
        return None
    job["elapsed_seconds"] = int(time.time() - job["created_at"])
    return job


def get_result(job_id: str) -> Optional[Dict]:
    job = JOBS.get(job_id)
    if not job:
        return None
    result = job.get("result")
    if result:
        return assert_final_payload_is_clean(finalize_result_payload(result))
    return None
