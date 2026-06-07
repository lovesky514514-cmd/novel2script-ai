from typing import Any, Dict, List, Optional

import yaml

from app.models.schemas import (
    KnowledgeTrace,
    NovelAnalysis,
    NovelMemory,
    QualityReport,
    RequirementPlan,
    ScriptScene,
    ValidationReport,
)
from app.version import APP_VERSION


MISSING_TEXT_VALUES = {
    "",
    "待识别",
    "待更新",
    "unknown",
    "Unknown",
    "N/A",
    "暂无",
    "暂无动作",
    "暂无对白",
    "主要场景",
    "日/夜",
    "角色",
    "核心人物",
}


def _dash(value: Any) -> Any:
    if value is None:
        return "-"
    if isinstance(value, str):
        stripped = value.strip()
        return "-" if stripped in MISSING_TEXT_VALUES else stripped
    if isinstance(value, list):
        if not value:
            return ["-"]
        return [_dash(item) for item in value]
    if isinstance(value, dict):
        return {key: _dash(item) for key, item in value.items()}
    return value


def _scene_to_yaml(scene: ScriptScene) -> Dict[str, Any]:
    return _dash(scene.model_dump())


def dump_script_yaml(
    title: str,
    source_chapters: int,
    memory: NovelMemory,
    scenes: List[ScriptScene],
    report: QualityReport,
    analysis: Optional[NovelAnalysis] = None,
    requirement_plan: Optional[RequirementPlan] = None,
    knowledge_trace: Optional[KnowledgeTrace] = None,
    validation_report: Optional[ValidationReport] = None,
    runtime_metadata: Optional[Dict[str, Any]] = None,
    story_bible: Optional[Dict[str, Any]] = None,
    chapter_facts: Optional[List[Dict[str, Any]]] = None,
    repair_questions: Optional[List[Dict[str, Any]]] = None,
    model_trace: Optional[Dict[str, Any]] = None,
) -> str:
    runtime_metadata = runtime_metadata or {}
    payload = {
        "metadata": {
            "title": title or "-",
            "source_chapters": source_chapters,
            "adaptation_style": analysis.adaptation_direction if analysis else "-",
            "genre": analysis.genre if analysis else "-",
            "language": "zh-CN",
            "created_by": "Novel2Script AI",
            "app_version": runtime_metadata.get("app_version") or APP_VERSION,
            "run_id": runtime_metadata.get("run_id") or "-",
            "generated_at": runtime_metadata.get("generated_at") or "-",
            "input_hash": runtime_metadata.get("input_hash") or "-",
            "model_status": runtime_metadata.get("model_status") or "-",
            "guard_mode": runtime_metadata.get("guard_mode") or "accuracy_pipeline",
            "output_gate": runtime_metadata.get("output_gate") or "enabled",
        },
        "accuracy_pipeline": {
            "story_bible": _dash(story_bible or {}),
            "chapter_facts": _dash(chapter_facts or []),
            "repair_questions": _dash(repair_questions or []),
            "model_trace": _dash(model_trace or {}),
        },
        "analysis": _dash(analysis.model_dump()) if analysis else {},
        "requirement_plan": _dash(requirement_plan.model_dump()) if requirement_plan else {},
        "knowledge_trace": _dash(knowledge_trace.model_dump()) if knowledge_trace else {},
        "characters": [_dash(item.model_dump()) for item in memory.characters],
        "memory": {
            "timeline": memory.timeline or ["-"],
            "foreshadows": [_dash(item.model_dump()) for item in memory.foreshadows] or ["-"],
            "unresolved_conflicts": [
                _dash(event.model_dump()) for event in memory.events
                if event.conflict
            ] or ["-"],
        },
        "scenes": [_scene_to_yaml(scene) for scene in scenes],
        "quality_report": _dash(report.model_dump()),
        "validation_report": _dash(validation_report.model_dump()) if validation_report else {},
    }
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
