import json
import re
from typing import Any, Dict, List, Tuple

from app.models.schemas import (
    Chapter,
    KnowledgeRule,
    NovelAnalysis,
    NovelMemory,
    RequirementPlan,
    ScriptScene,
    ValidationIssue,
)
from app.services.ai_client import AIClient, response_content
from app.services.scene_planner import build_scene_from_chapter
from app.services.validation_engine import validate_single_scene_against_chapter
from app.services.error_pattern_engine import infer_location_from_text, infer_props_from_text, infer_time_from_text, strip_chapter_prefix


def _json_loads_loose(text: str) -> Any:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        try:
            return json.loads(text[first:last + 1])
        except Exception:
            pass
    return {}


def _scene_from_dict(item: Dict[str, Any], chapter: Chapter, fallback: ScriptScene) -> ScriptScene:
    return ScriptScene(
        id=f"scene_{chapter.order:03d}",
        title=str(item.get("title") or fallback.title),
        source_chapter=chapter.order,
        source_events=item.get("source_events") or fallback.source_events,
        location=str(item.get("location") or fallback.location),
        time=str(item.get("time") or fallback.time),
        characters=item.get("characters") or fallback.characters,
        conflict=str(item.get("conflict") or fallback.conflict),
        purpose=str(item.get("purpose") or fallback.purpose),
        action=item.get("action") or fallback.action,
        dialogue=item.get("dialogue") or fallback.dialogue,
        notes=str(item.get("notes") or ""),
    )


def _extract_scene_json(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get("scene"), dict):
        return data["scene"]
    if isinstance(data, dict) and isinstance(data.get("scenes"), list) and data["scenes"]:
        return data["scenes"][0]
    if isinstance(data, dict):
        return data
    return {}


def _fallback_scene(chapter: Chapter, memory: NovelMemory, analysis: NovelAnalysis, requirement_plan: RequirementPlan) -> ScriptScene:
    event_map = {event.chapter_id: event for event in memory.events}
    scene = build_scene_from_chapter(
        chapter=chapter,
        event=event_map.get(chapter.id),
        memory=memory,
        analysis=analysis,
        requirement_plan=requirement_plan,
    )
    scene.notes = (scene.notes or "") + " clean_fallback"
    return scene


def _deterministic_facts(chapter: Chapter, memory: NovelMemory) -> Dict[str, Any]:
    """Generic fallback only. It must not contain story-specific titles/places/names."""
    text = chapter.text
    names = [c.name for c in memory.characters if c.name and c.name in text]
    location = infer_location_from_text(text)
    time = infer_time_from_text(text)
    props = infer_props_from_text(text)
    title = strip_chapter_prefix(chapter.title)
    return {
        "chapter_id": chapter.id,
        "source_chapter": chapter.order,
        "chapter_title": chapter.title,
        "scene_title": title,
        "location": location,
        "time": time,
        "on_stage_characters": names,
        "off_stage_characters": [],
        "key_events": [text[:220]] if text else [],
        "key_props": props,
        "conflict": "-",
        "purpose": "-",
        "must_include": [],
        "must_not": [],
        "scene_units": [],
        "evidence": text[:500],
    }


def _issue_dicts(issues: List[ValidationIssue]) -> List[Dict[str, str]]:
    return [issue.model_dump() for issue in issues]


async def extract_story_bible(
    client: AIClient,
    chapters: List[Chapter],
    memory: NovelMemory,
    used_rules: List[KnowledgeRule],
) -> Dict[str, Any]:
    fallback = {
        "mode": "fallback",
        "characters": [c.model_dump() for c in memory.characters],
        "timeline": memory.timeline,
        "rules": [r.title for r in used_rules[:8]],
    }
    if client.provider == "mock" or not client.api_key:
        return fallback

    payload = {
        "task": "阅读小说全文和剧本知识规则，只抽取事实，不写剧本。",
        "output_schema": {
            "story_bible": {
                "genre": "题材",
                "logline": "一句话主线",
                "characters": [{"name": "人物", "role": "身份", "motivation": "动机", "state": "当前状态"}],
                "relationships": [{"source": "人物A", "target": "人物B", "relation": "关系"}],
                "timeline": ["按章节顺序列事实"],
                "foreshadows": [{"prop": "伏笔/道具", "first_seen": "首次出现", "payoff": "后续作用"}],
                "global_rules": ["改编时必须遵守的规则"]
            }
        },
        "chapters": [c.model_dump() for c in chapters],
        "memory": memory.model_dump(),
        "knowledge_rules": [r.model_dump() for r in used_rules[:12]],
    }
    try:
        response = await client.pro_model_json([
            {"role": "system", "content": "你是剧本改编前期策划，只做事实抽取。只输出 JSON。"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ])
        data = _json_loads_loose(response_content(response))
        return data.get("story_bible", data) or fallback
    except Exception as exc:
        fallback["error"] = f"{type(exc).__name__}: {exc}"
        return fallback


async def extract_chapter_fact(
    client: AIClient,
    chapter: Chapter,
    story_bible: Dict[str, Any],
    memory: NovelMemory,
) -> Dict[str, Any]:
    fallback = _deterministic_facts(chapter, memory)
    if client.provider == "mock" or not client.api_key:
        return fallback

    payload = {
        "task": "只抽取当前章节事实，不写剧本。",
        "story_bible": story_bible,
        "chapter": chapter.model_dump(),
        "output_schema": {
            "chapter_fact": {
                "source_chapter": chapter.order,
                "scene_title": "建议场景标题；必须根据当前章节内容生成，不要套用示例标题",
                "location": "本章当前主要场景地点；如有多个独立地点，可写为列表或同时填写 scene_units",
                "time": "日/夜/深夜/晨/午/傍晚/-；不要把日期里的日当成白天",
                "on_stage_characters": ["本章现场人物"],
                "off_stage_characters": ["只被提到/录音/照片/电话/短信出现的人"],
                "key_events": ["本章关键事件，按发生顺序"],
                "key_props": ["本章实际出现且会被镜头强调的道具，不要把地点当道具"],
                "conflict": "本章主要冲突",
                "purpose": "本章在剧本中的功能",
                "must_include": ["必须保留的信息"],
                "must_not": ["不能提前泄露/不能误写的信息"],
                "scene_units": [
                    {
                        "title": "如果本章含多个独立地点，则为每个地点生成一个单元标题",
                        "location": "该单元地点",
                        "time": "该单元时间",
                        "characters": ["该单元现场人物"],
                        "events": ["该单元事件"],
                        "props": ["该单元道具"],
                        "conflict": "该单元冲突",
                        "purpose": "该单元目的"
                    }
                ],
                "evidence": "原文依据"
            }
        },
        "time_rule": "日=白天/日间，不是日期；夜=夜晚；深夜=夜深以后。",
    }
    try:
        response = await client.pro_model_json([
            {"role": "system", "content": "你是小说事实抽取器。只输出 JSON。不要改写，不要脑补。"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ])
        data = _json_loads_loose(response_content(response))
        fact = data.get("chapter_fact", data) if isinstance(data, dict) else {}
        return {**fallback, **(fact or {})}
    except Exception as exc:
        fallback["error"] = f"{type(exc).__name__}: {exc}"
        return fallback


async def generate_scene_from_fact(
    client: AIClient,
    chapter: Chapter,
    fact: Dict[str, Any],
    story_bible: Dict[str, Any],
    used_rules: List[KnowledgeRule],
    fallback: ScriptScene,
    user_instruction: str,
) -> ScriptScene:
    if client.provider == "mock" or not client.api_key:
        return fallback

    payload = {
        "task": "根据 chapter_fact 把当前章节改成一场影视分场剧本。只输出 JSON。",
        "hard_constraints": [
            "只写当前章节这一场。",
            "必须使用 chapter_fact 的地点、时间、现场人物。",
            "不能复制其他场的对白、动作、冲突、目的。",
            "不能把后文信息提前写进来。",
            "日表示白天/日间，不是日期。"
        ],
        "user_instruction": user_instruction,
        "story_bible": story_bible,
        "chapter_fact": fact,
        "chapter_text": chapter.text,
        "knowledge_rules": [r.model_dump() for r in used_rules[:6]],
        "output_schema": {
            "scene": {
                "id": f"scene_{chapter.order:03d}",
                "source_chapter": chapter.order,
                "title": fact.get("scene_title", fallback.title),
                "location": fact.get("location", fallback.location),
                "time": fact.get("time", fallback.time),
                "characters": fact.get("on_stage_characters", fallback.characters),
                "conflict": "本场冲突",
                "action": ["镜头/动作/空间调度，至少 3 条"],
                "dialogue": [{"speaker": "人物", "line": "对白", "emotion": "情绪", "subtext": "潜台词"}],
                "purpose": "本场目的",
                "notes": "生成说明"
            }
        },
    }

    try:
        response = await client.chat_model_json([
            {"role": "system", "content": "你是中文影视编剧。只输出 JSON。"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ], temperature=0.35)
        data = _json_loads_loose(response_content(response))
        scene = _scene_from_dict(_extract_scene_json(data), chapter, fallback)
        scene.notes = (scene.notes or "") + " chat_generated_from_facts"
        return scene
    except Exception as exc:
        fallback.notes = (fallback.notes or "") + f" chat_generation_failed: {type(exc).__name__}"
        return fallback


async def repair_scene_with_pro(
    client: AIClient,
    chapter: Chapter,
    scene: ScriptScene,
    fact: Dict[str, Any],
    issues: List[ValidationIssue],
    fallback: ScriptScene,
) -> Tuple[ScriptScene, List[Dict[str, Any]]]:
    questions: List[Dict[str, Any]] = []

    if not issues:
        return scene, questions

    if client.provider == "mock" or not client.api_key:
        fallback.notes = (fallback.notes or "") + " pro_repair_mock_fallback"
        return fallback, questions

    payload = {
        "task": "修复当前这一场，不要重写其他场。只输出 JSON。",
        "chapter": chapter.model_dump(),
        "chapter_fact": fact,
        "bad_scene": scene.model_dump(),
        "validator_errors": _issue_dicts(issues),
        "output_schema": {
            "scene": "修复后的 scene 对象",
            "questions": [
                {
                    "target": "字段名",
                    "question": "如果原文无法判断，需要问用户的问题",
                    "reason": "为什么需要确认",
                    "suggested_default": "可选默认值"
                }
            ]
        },
        "rules": [
            "地点、时间、人物必须来自当前 chapter_fact。",
            "不能复用其他场对白。",
            "如果原文能判断，直接修；只有原文无法判断时才生成 questions。"
        ]
    }

    try:
        response = await client.pro_model_json([
            {"role": "system", "content": "你是剧本医生和事实校验员。只输出 JSON。"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ], temperature=0.1)
        data = _json_loads_loose(response_content(response))
        repaired_data = data.get("scene", data) if isinstance(data, dict) else {}
        repaired = _scene_from_dict(repaired_data, chapter, fallback)
        repaired.notes = (repaired.notes or "") + " pro_repaired"
        questions = data.get("questions", []) if isinstance(data, dict) else []
        return repaired, questions
    except Exception as exc:
        fallback.notes = (fallback.notes or "") + f" pro_repair_failed: {type(exc).__name__}"
        questions = [{
            "target": f"scene_{chapter.order:03d}",
            "question": "这一场修复失败，是否允许使用系统根据章节事实生成的保底版本？",
            "reason": str(exc),
            "suggested_default": "允许"
        }]
        return fallback, questions


async def generate_scenes_accuracy_pipeline(
    chapters: List[Chapter],
    memory: NovelMemory,
    analysis: NovelAnalysis,
    requirement_plan: RequirementPlan,
    used_rules: List[KnowledgeRule],
) -> Tuple[List[ScriptScene], Dict[str, Any]]:
    client = AIClient()
    story_bible = await extract_story_bible(client, chapters, memory, used_rules)

    scenes: List[ScriptScene] = []
    chapter_facts: List[Dict[str, Any]] = []
    repair_questions: List[Dict[str, Any]] = []
    model_trace = {
        "pipeline": "pro_learn -> pro_extract_facts -> chat_generate_scene -> deterministic_validate -> pro_repair",
        "chat_model": client.chat_model,
        "pro_model": client.pro_model,
        "provider": client.provider,
        "scene_steps": [],
    }

    for chapter in chapters:
        fallback = _fallback_scene(chapter, memory, analysis, requirement_plan)
        fact = await extract_chapter_fact(client, chapter, story_bible, memory)
        chapter_facts.append(fact)

        scene = await generate_scene_from_fact(
            client=client,
            chapter=chapter,
            fact=fact,
            story_bible=story_bible,
            used_rules=used_rules,
            fallback=fallback,
            user_instruction=requirement_plan.raw_instruction,
        )

        issues = validate_single_scene_against_chapter(chapter, scene, fact)
        step = {
            "chapter": chapter.order,
            "initial_issue_count": len(issues),
            "initial_issues": _issue_dicts(issues),
            "used_repair": False,
            "used_fallback": False,
        }

        if issues:
            scene, questions = await repair_scene_with_pro(client, chapter, scene, fact, issues, fallback)
            repair_questions.extend([{"scene_id": scene.id, **q} for q in questions])
            step["used_repair"] = True

            issues_after = validate_single_scene_against_chapter(chapter, scene, fact)
            step["repair_issue_count"] = len(issues_after)
            step["repair_issues"] = _issue_dicts(issues_after)

            if issues_after:
                scene = fallback
                scene.notes = (scene.notes or "") + " fallback_after_repair_failed"
                step["used_fallback"] = True

        scenes.append(scene)
        model_trace["scene_steps"].append(step)

    return scenes, {
        "story_bible": story_bible,
        "chapter_facts": chapter_facts,
        "repair_questions": repair_questions,
        "model_trace": model_trace,
    }
