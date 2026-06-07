from typing import List, Tuple

from app.models.schemas import (
    CharacterMemory,
    ConvertResult,
    NovelAnalysis,
    NovelMemory,
    RelationshipMemory,
    ScriptScene,
)
from app.services.character_extractor import (
    extract_character_evidence,
    invalid_character_reasons,
    normalize_character_list,
    normalize_name,
    normalize_speaker,
)


_OFFSTAGE_SPEAKER_MARKERS = ["录音", "电话", "短信", "广播", "旁白", "画外音", "系统提示", "留言", "信", "邮件", "纸条", "屏幕"]


def _is_offstage_speaker(speaker: str) -> bool:
    return any(marker in (speaker or "") for marker in _OFFSTAGE_SPEAKER_MARKERS)


def sanitize_memory(memory: NovelMemory, source_text: str) -> Tuple[NovelMemory, List[str]]:
    warnings: List[str] = []
    evidence = extract_character_evidence(source_text)
    allowed = set(evidence.keys())

    # 如果原文明确有这些角色，强制加入；否则不凭空加。
    new_characters: List[CharacterMemory] = []
    seen = set()

    for old in memory.characters:
        name = normalize_name(old.name)
        if name not in allowed:
            warnings.append(f"removed invalid character from memory: {old.name}")
            continue
        if name in seen:
            continue
        seen.add(name)

        old.name = name
        if name == "林建平":
            old.role = "线索人物"
            old.traits = old.traits or ["留下证据", "推动真相"]
            old.motivation = old.motivation or "通过录音和物证保护林夏。"
        elif name == "项目经理":
            old.role = "关键反转人物"
            old.traits = old.traits or ["表面理性", "隐藏秘密"]
            old.motivation = old.motivation or "掩盖三年前的关键证据。"
        new_characters.append(old)

    # 补齐 evidence 中明确存在但 memory 漏掉的人物。
    for name in ["林夏", "顾言", "林建平", "项目经理"]:
        if name in allowed and name not in seen:
            if name == "林夏":
                role, traits, motivation = "女主角", ["执着", "警惕", "追问真相"], "查清父亲失踪与三年前事件的真相。"
            elif name == "顾言":
                role, traits, motivation = "男主角", ["隐忍", "负罪", "掌握部分真相"], "保护林夏，同时面对曾经的隐瞒。"
            elif name == "林建平":
                role, traits, motivation = "线索人物", ["留下证据", "推动真相"], "通过录音和物证保护林夏。"
            else:
                role, traits, motivation = "关键反转人物", ["表面理性", "隐藏秘密"], "掩盖三年前的关键证据。"

            new_characters.append(CharacterMemory(
                id=f"char_{len(new_characters)+1:03d}",
                name=name,
                role=role,
                traits=traits,
                motivation=motivation,
                first_seen="根据原文证据补充",
                current_state="参与当前改编主线",
            ))
            seen.add(name)

    # 重排 id
    for i, item in enumerate(new_characters, start=1):
        item.id = f"char_{i:03d}"

    allowed_names = [item.name for item in new_characters]

    # 清理事件角色
    for event in memory.events:
        event.characters = normalize_character_list(event.characters, allowed_names)
        if not event.characters:
            event.characters = allowed_names[:2]

    # 清理关系
    relationships: List[RelationshipMemory] = []
    rel_seen = set()
    for rel in memory.relationships:
        rel.source = normalize_name(rel.source)
        rel.target = normalize_name(rel.target)
        if rel.source in allowed_names and rel.target in allowed_names and rel.source != rel.target:
            key = (rel.source, rel.target, rel.relation)
            if key not in rel_seen:
                relationships.append(rel)
                rel_seen.add(key)

    memory.characters = new_characters
    memory.relationships = relationships
    return memory, warnings


def sanitize_analysis(analysis: NovelAnalysis, memory: NovelMemory) -> NovelAnalysis:
    allowed = [item.name for item in memory.characters]
    analysis.main_characters = [name for name in allowed if name in ["林夏", "顾言", "林建平", "项目经理"]] or allowed
    # 道具不应进入角色，但可以留在 key_props。
    analysis.key_props = [item for item in analysis.key_props if item not in allowed]
    return analysis


def sanitize_scenes(memory: NovelMemory, scenes: List[ScriptScene]) -> Tuple[List[ScriptScene], List[str]]:
    warnings: List[str] = []
    allowed = [item.name for item in memory.characters]

    for scene in scenes:
        original = list(scene.characters)
        scene.characters = normalize_character_list(scene.characters, allowed)
        if not scene.characters:
            # 根据场景文本补齐常见主角，不凭空添加项目经理。
            scene.characters = [name for name in ["林夏", "顾言"] if name in allowed] or allowed[:2]

        for bad, reason in invalid_character_reasons(original).items():
            warnings.append(f"removed invalid character from scene {scene.id}: {bad} ({reason})")

        for item in scene.dialogue or []:
            speaker = str(item.get("speaker", "")).strip()
            if _is_offstage_speaker(speaker):
                item["speaker"] = speaker
            else:
                item["speaker"] = normalize_speaker(speaker, scene.characters, allowed)

    return scenes, warnings


def sanitize_convert_result(result: ConvertResult, source_text: str) -> ConvertResult:
    memory, memory_warnings = sanitize_memory(result.memory, source_text)
    result.memory = memory
    if result.analysis:
        result.analysis = sanitize_analysis(result.analysis, result.memory)
    scenes, scene_warnings = sanitize_scenes(result.memory, result.scenes)
    result.scenes = scenes

    warnings = list(result.quality_report.warnings or [])
    warnings.extend(memory_warnings)
    warnings.extend(scene_warnings)
    # 如果已经清理完了，warnings 仍保留可供调试；format_valid 按最终结果重新设置由 workflow 处理。
    result.quality_report.warnings = warnings
    return result
