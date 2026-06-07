from typing import List

from app.models.schemas import NovelMemory, QualityReport, ScriptScene


def generate_quality_report(memory: NovelMemory, scenes: List[ScriptScene], format_valid: bool, format_warnings: List[str]) -> QualityReport:
    covered_events = {event_id for scene in scenes for event_id in scene.source_events}
    total_events = max(len(memory.events), 1)
    event_coverage = round(len(covered_events) / total_events, 2)

    known_characters = {character.name for character in memory.characters}
    used_characters = {name for scene in scenes for name in scene.characters}
    unknown_characters = [
        name for name in used_characters
        if name not in known_characters and name != "未知角色"
    ]
    character_consistency = 1.0 if not unknown_characters else max(0.0, 1.0 - len(unknown_characters) * 0.1)

    used_text = " ".join([" ".join(scene.action) + " " + scene.conflict for scene in scenes])
    retained = [
        item for item in memory.foreshadows
        if any(token in used_text for token in item.description.replace("“", " ").replace("”", " ").split())
    ]
    total_foreshadows = max(len(memory.foreshadows), 1)
    foreshadow_retention = round(len(retained) / total_foreshadows, 2) if memory.foreshadows else 1.0

    warnings = list(format_warnings)
    suggestions: List[str] = []

    if event_coverage < 1:
        warnings.append("部分原文事件尚未进入剧本场景。")
        suggestions.append("为未覆盖事件补充分场，或合并到相邻场景。")
    if unknown_characters:
        warnings.append(f"发现未登记角色：{', '.join(unknown_characters)}。")
        suggestions.append("检查角色是否来自原文，必要时合并重名角色。")
    if foreshadow_retention < 1:
        warnings.append("部分伏笔尚未在剧本中保留或回应。")
        suggestions.append("将关键伏笔绑定到 source_events 或 scene.notes。")

    return QualityReport(
        event_coverage=event_coverage,
        character_consistency=round(character_consistency, 2),
        foreshadow_retention=foreshadow_retention,
        format_valid=format_valid,
        warnings=warnings,
        suggestions=suggestions,
    )
