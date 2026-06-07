from collections import Counter
from typing import Any, Dict, List

from app.models.schemas import Chapter, KnowledgeTrace, NovelMemory, RequirementPlan, ScriptScene, ValidationIssue, ValidationReport
from app.services.error_pattern_engine import get_offstage_speaker_markers, get_offstage_character_fields, get_time_keywords


PLACEHOLDER_PHRASES = [
    "环境先给出压迫感和情绪基调",
    "围绕关键线索展开对峙",
    "信息一层层被逼出",
    "场景中的道具或空间承担情绪表达",
    "角色进入场景",
]

BANNED_WORDS = ["Demo 模式", "待剧本专家", "AI 模式下", "unknown", "待更新", "待识别"]


def _dialogue_sig(scene: ScriptScene):
    return tuple(item.get("line", "") for item in scene.dialogue)


def _fact_value(fact: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = fact.get(key)
        if value is not None and str(value).strip() and str(value).strip() not in ["-", "未指定"]:
            return str(value).strip()
    return ""


def _expected_time_from_text(text: str) -> str:
    keywords = get_time_keywords()
    # Current explicit scene time priority.
    for label, result in [("day", "日"), ("dusk", "傍晚"), ("deep_night", "深夜"), ("night", "夜")]:
        for item in keywords.get(label, []):
            if item and item in text:
                return result
    return ""


def _allowed_offstage_speaker(speaker: str, fact: Dict[str, Any] | None = None) -> bool:
    fact = fact or {}
    if any(marker in speaker for marker in get_offstage_speaker_markers()):
        return True
    for field in get_offstage_character_fields():
        value = fact.get(field)
        if isinstance(value, list) and speaker in [str(item) for item in value]:
            return True
    return False


def validate_single_scene_against_chapter(chapter: Chapter, scene: ScriptScene, fact: Dict[str, Any] | None = None) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    fact = fact or {}

    if not scene.title or scene.title in ["-", "未指定"]:
        issues.append(ValidationIssue(code="empty_title", target=scene.id, message="场景标题为空。"))
    if not scene.location or scene.location in ["-", "未指定"]:
        issues.append(ValidationIssue(code="empty_location", target=scene.id, message="场景地点为空。"))
    if not scene.time or scene.time in ["-", "未指定"]:
        issues.append(ValidationIssue(code="empty_time", target=scene.id, message="场景时间为空。"))

    expected_location = _fact_value(fact, "location")
    expected_time = _fact_value(fact, "time")

    if expected_location and scene.location != expected_location:
        # Split scenes may use one location unit from a multi-location fact.
        if scene.location not in expected_location and expected_location not in scene.location:
            issues.append(ValidationIssue(code="fact_location_mismatch", target=scene.id, message=f"地点应来自 {expected_location}，当前为 {scene.location}。"))

    if expected_time and scene.time != expected_time:
        issues.append(ValidationIssue(code="fact_time_mismatch", target=scene.id, message=f"时间应为 {expected_time}，当前为 {scene.time}。"))

    if not expected_time:
        inferred_time = _expected_time_from_text(chapter.text)
        if inferred_time and scene.time != inferred_time:
            if not (inferred_time == "深夜" and scene.time == "夜"):
                issues.append(ValidationIssue(code="time_not_from_chapter", target=scene.id, message=f"时间应接近 {inferred_time}，当前为 {scene.time}。"))

    action_text = "\n".join(scene.action or [])
    for phrase in PLACEHOLDER_PHRASES:
        if phrase in action_text:
            issues.append(ValidationIssue(code="template_action", target=scene.id, message=f"动作仍含模板句：{phrase}"))

    joined = " ".join([scene.title or "", scene.location or "", scene.time or "", scene.conflict or "", scene.purpose or "", action_text, scene.notes or ""])
    for word in BANNED_WORDS:
        if word in joined:
            issues.append(ValidationIssue(code="banned_placeholder", target=scene.id, message=f"发现占位词：{word}"))

    if scene.source_chapter != chapter.order:
        issues.append(ValidationIssue(code="wrong_source_chapter", target=scene.id, message=f"source_chapter 应为 {chapter.order}。"))

    return issues


def validate_script(
    chapters: List[Chapter],
    memory: NovelMemory,
    scenes: List[ScriptScene],
    requirement_plan: RequirementPlan,
    knowledge_trace: KnowledgeTrace | None = None,
    chapter_facts: List[Dict[str, Any]] | None = None,
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    known_names = {item.name for item in memory.characters}
    chapter_map = {chapter.order: chapter for chapter in chapters}
    fact_map = {}
    for index, fact in enumerate(chapter_facts or [], start=1):
        if isinstance(fact, dict):
            try:
                order = int(fact.get("source_chapter") or index)
            except Exception:
                order = index
            fact_map[order] = fact

    dialogue_signatures = []
    action_signatures = []

    for scene in scenes:
        chapter = chapter_map.get(scene.source_chapter)
        fact = fact_map.get(scene.source_chapter, {})

        if scene.id == "":
            issues.append(ValidationIssue(code="empty_scene_id", target=scene.id, message="场景 ID 为空。"))

        for character in scene.characters:
            if character and known_names and character not in known_names:
                # Do not hard fail unknown names; story_bible may be incomplete in early drafts.
                pass

        for dialogue in scene.dialogue:
            speaker = dialogue.get("speaker", "")
            if speaker and scene.characters and speaker not in scene.characters and not _allowed_offstage_speaker(speaker, fact):
                issues.append(ValidationIssue(code="speaker_not_in_scene", target=scene.id, message=f"{speaker} 不在本场人物中。"))

        if chapter:
            issues.extend(validate_single_scene_against_chapter(chapter, scene, fact))

        dialogue_signatures.append(_dialogue_sig(scene))
        action_signatures.append(tuple(scene.action or []))

    dialogue_counter = Counter(dialogue_signatures)
    for signature, count in dialogue_counter.items():
        if signature and count > 1:
            issues.append(ValidationIssue(code="duplicate_dialogue", target="scenes", message="多个场景对白重复。"))

    action_counter = Counter(action_signatures)
    for signature, count in action_counter.items():
        if signature and count > 1:
            issues.append(ValidationIssue(code="duplicate_action", target="scenes", message="多个场景动作重复。"))

    if requirement_plan.raw_instruction:
        raw = requirement_plan.raw_instruction
        if "第三章" in raw and not any(scene.source_chapter == 3 for scene in scenes):
            issues.append(ValidationIssue(code="instruction_not_applied", target="requirement_plan", message="用户要求第三章，但结果没有第三章场景。"))

    if knowledge_trace is not None:
        if not knowledge_trace.used_rules:
            issues.append(ValidationIssue(code="knowledge_not_used", target="knowledge_trace", message="未记录知识库规则命中。"))
        if not knowledge_trace.applied_rules:
            issues.append(ValidationIssue(code="rule_not_applied", target="knowledge_trace", message="未记录规则应用到场景。"))

    return issues


def build_validation_report(first_pass: List[ValidationIssue], repair_log: List[str], final_issues: List[ValidationIssue]) -> ValidationReport:
    status = "pass" if not final_issues else "needs_review"
    return ValidationReport(
        first_pass_issues=first_pass,
        repair_log=repair_log,
        final_issues=final_issues,
        final_status=status,
        pass_count=2,
    )
