from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from app.models.schemas import ConvertResult, ScriptScene
from app.services.character_guard import sanitize_scenes
from app.services.error_pattern_engine import (
    clean_repair_log,
    infer_location_from_text,
    infer_props_from_text,
    infer_time_from_text,
    normalize_props,
    split_location_text,
    strip_chapter_prefix,
)
from app.services.report_generator import generate_quality_report
from app.services.schema_guard import normalize_scene_characters
from app.services.schema_validator import validate_yaml_text
from app.services.validation_engine import build_validation_report, validate_script, validate_single_scene_against_chapter
from app.services.yaml_generator import dump_script_yaml
from app.services.runtime_metadata import metadata_dict


def _safe_str(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _as_list(value: Any) -> List[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def _fact_map(result: ConvertResult) -> Dict[int, Dict[str, Any]]:
    facts: Dict[int, Dict[str, Any]] = {}
    for index, fact in enumerate(result.chapter_facts or [], start=1):
        if not isinstance(fact, dict):
            continue
        try:
            order = int(fact.get("source_chapter") or fact.get("chapter_order") or index)
        except Exception:
            order = index
        facts[order] = fact
    return facts


def _enrich_fact_from_chapter(fact: Dict[str, Any], chapter) -> Dict[str, Any]:
    """Fill missing facts from the current chapter using generic heuristics.

    This is not story-specific. It only avoids empty '-' fields when the Pro layer
    is unavailable or returns incomplete data.
    """
    enriched = dict(fact or {})
    text = chapter.text or ""

    if not _safe_str(enriched.get("scene_title"), ""):
        enriched["scene_title"] = strip_chapter_prefix(chapter.title)
    if not _safe_str(enriched.get("location"), "") or _safe_str(enriched.get("location")) == "-":
        enriched["location"] = infer_location_from_text(text)
    if not _safe_str(enriched.get("time"), "") or _safe_str(enriched.get("time")) == "-":
        enriched["time"] = infer_time_from_text(text)
    if not enriched.get("key_props"):
        enriched["key_props"] = infer_props_from_text(text)
    if not enriched.get("key_events"):
        enriched["key_events"] = [text[:220]] if text else []
    if not enriched.get("source_chapter"):
        enriched["source_chapter"] = chapter.order
    return enriched


def _title_from_fact(fact: Dict[str, Any], fallback: str = "-") -> str:
    for key in ["scene_title", "title", "chapter_title"]:
        value = _safe_str(fact.get(key), "")
        if value:
            return value
    return fallback or "-"


def _characters_from_fact(fact: Dict[str, Any], current: List[str]) -> List[str]:
    for key in ["on_stage_characters", "characters", "present_characters"]:
        value = fact.get(key)
        if isinstance(value, list) and value:
            return [str(item).strip() for item in value if str(item).strip()]
    return current or []


def _events_from_fact(fact: Dict[str, Any]) -> List[str]:
    for key in ["key_events", "events", "must_include"]:
        value = fact.get(key)
        if isinstance(value, list) and value:
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    return []


def _props_from_fact(fact: Dict[str, Any]) -> List[str]:
    return normalize_props(fact.get("key_props") or fact.get("props") or [])


def _is_generic(text: str) -> bool:
    text = text or ""
    generic_markers = ["本章关键事件", "推动主线", "信息差", "人物对抗", "转化为可表演场景", "核心冲突"]
    return any(marker in text for marker in generic_markers)


def _conflict_from_fact(fact: Dict[str, Any], scene: ScriptScene) -> str:
    conflict = _safe_str(fact.get("conflict"), "")
    if conflict and conflict != "-" and not _is_generic(conflict):
        return conflict
    events = _events_from_fact(fact)
    if events:
        return f"围绕“{events[0][:40]}”形成本场冲突。"
    return scene.conflict or "-"


def _purpose_from_fact(fact: Dict[str, Any], scene: ScriptScene) -> str:
    purpose = _safe_str(fact.get("purpose"), "")
    if purpose and purpose != "-" and not _is_generic(purpose):
        return purpose
    events = _events_from_fact(fact)
    if events:
        return f"将“{_title_from_fact(fact, scene.title)}”中的关键事件转化为可表演场景，并推动后续剧情。"
    return scene.purpose or "-"


def _action_from_fact(scene: ScriptScene, fact: Dict[str, Any]) -> List[str]:
    events = _events_from_fact(fact)
    props = _props_from_fact(fact)
    action: List[str] = []
    if events:
        for item in events[:3]:
            action.append(item)
    else:
        action = [
            f"镜头进入{scene.location}，交代人物状态和空间关系。",
            "人物围绕当前章节的核心线索展开行动。",
            "场尾留下推动下一场的悬念。",
        ]
    if props:
        action.append("本场重点保留道具：" + "、".join(dict.fromkeys(props)) + "。")
    return action[:5]


def _dialogue_from_fact(scene: ScriptScene, fact: Dict[str, Any]) -> List[Dict[str, str]]:
    characters = _characters_from_fact(fact, scene.characters)
    conflict = _conflict_from_fact(fact, scene)
    if len(characters) >= 2:
        return [
            {
                "speaker": characters[0],
                "line": "这件事必须说清楚。",
                "emotion": "克制",
                "subtext": conflict,
            },
            {
                "speaker": characters[1],
                "line": "有些事不是你看到的那样。",
                "emotion": "压抑",
                "subtext": "对方仍有隐瞒。",
            },
        ]
    if len(characters) == 1:
        return [
            {
                "speaker": characters[0],
                "line": "这里一定还有没被发现的线索。",
                "emotion": "紧张",
                "subtext": "推动本场继续向前。",
            }
        ]
    return []


def _action_has_prop_line(action: List[str]) -> bool:
    return any("本场重点保留道具" in str(item) for item in action or [])


def _sanitize_action_props(action: List[str], fact: Dict[str, Any]) -> List[str]:
    props = _props_from_fact(fact)
    cleaned = [str(item) for item in (action or []) if "本场重点保留道具" not in str(item)]
    if props:
        cleaned.append("本场重点保留道具：" + "、".join(dict.fromkeys(props)) + "。")
    return cleaned


def _bind_scene_to_fact(scene: ScriptScene, fact: Dict[str, Any]) -> ScriptScene:
    bound = deepcopy(scene)
    bound.title = _title_from_fact(fact, bound.title)
    bound.location = _safe_str(fact.get("location"), bound.location or "-")
    bound.time = _safe_str(fact.get("time"), bound.time or "-")
    bound.characters = _characters_from_fact(fact, bound.characters)
    bound.conflict = _conflict_from_fact(fact, bound)
    bound.purpose = _purpose_from_fact(fact, bound)

    if not bound.action or not _action_has_prop_line(bound.action):
        bound.action = _action_from_fact(bound, fact)
    bound.action = _sanitize_action_props(bound.action, fact)

    if not bound.dialogue:
        bound.dialogue = _dialogue_from_fact(bound, fact)

    note = "fact_bound_general"
    if note not in (bound.notes or ""):
        bound.notes = ((bound.notes or "") + " " + note).strip()
    return bound


def _scene_units_from_fact(fact: Dict[str, Any]) -> List[Dict[str, Any]]:
    units = fact.get("scene_units")
    if isinstance(units, list):
        clean = [item for item in units if isinstance(item, dict) and _safe_str(item.get("location"), "")]
        if len(clean) >= 2:
            return clean

    locations = fact.get("locations") or fact.get("location")
    parts = split_location_text(locations)
    if len(parts) >= 2:
        events = _events_from_fact(fact)
        props = _props_from_fact(fact)
        result = []
        for index, loc in enumerate(parts, start=1):
            result.append({
                "title": f"{_title_from_fact(fact, '场景')} {index}",
                "location": loc,
                "time": fact.get("time", "-"),
                "characters": fact.get("on_stage_characters", []),
                "events": events[index - 1:index] or events[:1],
                "props": props,
                "conflict": fact.get("conflict", "-"),
                "purpose": fact.get("purpose", "-"),
            })
        return result
    return []


def _split_scene_by_units(scene: ScriptScene, fact: Dict[str, Any]) -> List[ScriptScene]:
    units = _scene_units_from_fact(fact)
    if len(units) < 2:
        return [scene]

    scenes: List[ScriptScene] = []
    for unit in units:
        unit_fact = dict(fact)
        unit_fact["scene_title"] = unit.get("title") or _title_from_fact(fact, scene.title)
        unit_fact["location"] = unit.get("location") or fact.get("location")
        unit_fact["time"] = unit.get("time") or fact.get("time")
        unit_fact["on_stage_characters"] = unit.get("characters") or fact.get("on_stage_characters") or scene.characters
        unit_fact["key_events"] = unit.get("events") or fact.get("key_events") or []
        unit_fact["key_props"] = unit.get("props") or fact.get("key_props") or []
        unit_fact["conflict"] = unit.get("conflict") or fact.get("conflict") or "-"
        unit_fact["purpose"] = unit.get("purpose") or fact.get("purpose") or "-"

        clone = deepcopy(scene)
        clone = _bind_scene_to_fact(clone, unit_fact)
        clone.notes = ((clone.notes or "") + " split_from_scene_units").strip()
        scenes.append(clone)

    return scenes


def _dedupe(scenes: List[ScriptScene], facts: Dict[int, Dict[str, Any]], repair_log: List[str]) -> List[ScriptScene]:
    seen_dialogue = {}
    seen_action = {}
    seen_purpose = {}
    out: List[ScriptScene] = []
    for scene in scenes:
        fact = facts.get(scene.source_chapter, {})
        dialogue_sig = tuple(item.get("line", "") for item in (scene.dialogue or []))
        action_sig = tuple(scene.action or [])
        purpose_sig = (scene.purpose or "").strip()

        if purpose_sig and purpose_sig in seen_purpose:
            scene.purpose = f"将“{scene.title}”中的关键事件转化为独立场景，并推动后续剧情。"
            repair_log.append(f"{scene.id}: purpose disambiguated from chapter_facts.")
        if dialogue_sig and dialogue_sig in seen_dialogue:
            scene.dialogue = _dialogue_from_fact(scene, fact)
            repair_log.append(f"{scene.id}: dialogue regenerated from chapter_facts.")
        if (scene.purpose or "").strip() in [p for p in seen_action.keys() if isinstance(p, str)]:
            scene.purpose = f"将“{scene.title}”中的关键事件转化为独立场景，并推动后续剧情。"
        if action_sig and action_sig in seen_action:
            scene.action = _action_from_fact(scene, fact)
            repair_log.append(f"{scene.id}: action regenerated from chapter_facts.")

        out.append(scene)
        seen_purpose[(scene.purpose or "").strip()] = scene.id
        seen_dialogue[tuple(item.get("line", "") for item in (scene.dialogue or []))] = scene.id
        seen_action[tuple(scene.action or [])] = scene.id
    return out


def _renumber(scenes: List[ScriptScene]) -> List[ScriptScene]:
    for index, scene in enumerate(scenes, start=1):
        scene.id = f"scene_{index:03d}"
    return scenes


def enforce_final_result(result: ConvertResult) -> ConvertResult:
    repair_log: List[str] = []
    if result.validation_report:
        repair_log.extend(clean_repair_log(result.validation_report.repair_log or []))

    facts = _fact_map(result)
    scenes_by_chapter: Dict[int, ScriptScene] = {}
    for scene in result.scenes or []:
        try:
            scenes_by_chapter.setdefault(int(scene.source_chapter), scene)
        except Exception:
            continue

    final_scenes: List[ScriptScene] = []

    for chapter in result.chapters:
        fact = _enrich_fact_from_chapter(facts.get(chapter.order, {}), chapter)
        current = scenes_by_chapter.get(chapter.order)
        if current is None:
            current = ScriptScene(
                id=f"scene_{chapter.order:03d}",
                title=_title_from_fact(fact, chapter.title),
                source_chapter=chapter.order,
                source_events=[],
                location=_safe_str(fact.get("location"), "-"),
                time=_safe_str(fact.get("time"), "-"),
                characters=_characters_from_fact(fact, []),
                conflict=_conflict_from_fact(fact, ScriptScene(id="-", title="-", source_chapter=chapter.order, source_events=[], location="-", time="-", characters=[], conflict="-", action=[], dialogue=[], purpose="-")),
                action=[],
                dialogue=[],
                purpose="-",
                notes="created_from_chapter_facts",
            )

        bound = _bind_scene_to_fact(current, fact)
        issues = validate_single_scene_against_chapter(chapter, bound, fact)
        if issues:
            bound.action = _action_from_fact(bound, fact)
            bound.dialogue = _dialogue_from_fact(bound, fact)
            bound.conflict = _conflict_from_fact(fact, bound)
            bound.purpose = _purpose_from_fact(fact, bound)
            bound.notes = ((bound.notes or "") + " repaired_from_facts").strip()
            repair_log.append(f"{bound.id}: fact-bound repaired {len(issues)} issues.")

        final_scenes.extend(_split_scene_by_units(bound, fact))

    final_scenes = _dedupe(final_scenes, facts, repair_log)
    final_scenes = _renumber(final_scenes)
    final_scenes = normalize_scene_characters(result.memory, final_scenes)
    final_scenes, character_warnings = sanitize_scenes(result.memory, final_scenes)
    repair_log.extend(clean_repair_log(character_warnings))

    result.scenes = final_scenes

    final_issues = validate_script(
        result.chapters,
        result.memory,
        result.scenes,
        result.requirement_plan,
        result.knowledge_trace,
        result.chapter_facts,
    )

    result.validation_report = build_validation_report(
        first_pass=result.validation_report.first_pass_issues if result.validation_report else [],
        repair_log=list(dict.fromkeys(clean_repair_log(repair_log))),
        final_issues=final_issues,
    )

    runtime = metadata_dict(result)
    preview_yaml = dump_script_yaml(
        result.title,
        len(result.chapters),
        result.memory,
        result.scenes,
        result.quality_report,
        result.analysis,
        result.requirement_plan,
        result.knowledge_trace,
        result.validation_report,
        runtime,
        result.story_bible,
        result.chapter_facts,
        result.repair_questions,
        result.model_trace,
    )
    yaml_valid, yaml_warnings = validate_yaml_text(preview_yaml)
    warnings = list(dict.fromkeys(clean_repair_log(repair_log + [issue.message for issue in final_issues] + yaml_warnings)))

    result.quality_report = generate_quality_report(
        result.memory,
        result.scenes,
        yaml_valid and len(final_issues) == 0,
        warnings,
    )

    result.yaml_text = dump_script_yaml(
        result.title,
        len(result.chapters),
        result.memory,
        result.scenes,
        result.quality_report,
        result.analysis,
        result.requirement_plan,
        result.knowledge_trace,
        result.validation_report,
        runtime,
        result.story_bible,
        result.chapter_facts,
        result.repair_questions,
        result.model_trace,
    )
    return result
