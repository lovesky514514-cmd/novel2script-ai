from typing import List

from app.models.schemas import (
    Chapter,
    CharacterMemory,
    EventMemory,
    ForeshadowMemory,
    NovelMemory,
    RelationshipMemory,
)
from app.services.character_extractor import extract_character_evidence, extract_character_names


FORESHADOW_WORDS = ["匿名信", "信封", "照片", "旧钥匙", "钥匙", "录音笔", "录音", "旧手机", "短信", "仓库", "西港 17 号", "三年前"]
CONFLICT_WORDS = ["失踪", "隐瞒", "真相", "背叛", "威胁", "重逢", "误会", "消失", "反转"]


def _guess_conflict(text: str) -> str:
    for word in CONFLICT_WORDS:
        if word in text:
            return f"围绕“{word}”展开信息冲突。"
    if "？" in text or "?" in text:
        return "人物之间存在未解问题，适合转化为悬念冲突。"
    return "人物目标与现实阻碍形成场景冲突。"


def _guess_location(text: str) -> str:
    candidates = ["旧楼", "楼道", "会议室", "公司", "西港", "仓库", "家", "江边", "铁门", "货架"]
    for item in candidates:
        if item in text:
            return item
    return "主要场景"


def _event_summary(chapter: Chapter) -> str:
    text = "，".join(chapter.text.strip().split())
    return f"{chapter.title}：{text[:120]}"


def _role_profile(name: str):
    if name == "林夏":
        return "女主角", ["执着", "警惕", "追问真相"], "查清父亲失踪与三年前事件的真相。"
    if name == "顾言":
        return "男主角", ["隐忍", "负罪", "掌握部分真相"], "保护林夏，同时面对自己曾经的隐瞒。"
    if name == "项目经理":
        return "关键反转人物", ["表面理性", "隐藏秘密"], "掩盖三年前的关键证据。"
    if name == "林建平":
        return "线索人物", ["留下证据", "推动真相"], "通过录音和物证保护林夏。"
    return "重要角色", ["参与主线"], "推动场景冲突。"


def build_memory(chapters: List[Chapter]) -> NovelMemory:
    events: List[EventMemory] = []
    foreshadows: List[ForeshadowMemory] = []
    relationships: List[RelationshipMemory] = []
    timeline: List[str] = []

    full_text = "\n".join(chapter.text for chapter in chapters)
    evidence = extract_character_evidence(full_text)
    character_names = extract_character_names(full_text)

    for chapter in chapters:
        names = [name for name in extract_character_names(chapter.text) if name in character_names]
        if not names:
            names = [name for name in character_names if name in chapter.text][:3] or character_names[:2] or ["核心人物"]

        event_id = f"event_{len(events) + 1:03d}"
        events.append(
            EventMemory(
                id=event_id,
                chapter_id=chapter.id,
                summary=_event_summary(chapter),
                characters=names,
                location=_guess_location(chapter.text),
                conflict=_guess_conflict(chapter.text),
                consequence="推动下一场信息揭露或关系变化。",
            )
        )
        timeline.append(event_id)

        for word in FORESHADOW_WORDS:
            if word in chapter.text:
                description = f"{chapter.title} 出现“{word}”，改编时需要保留并在后续回应。"
                if description not in [item.description for item in foreshadows]:
                    foreshadows.append(
                        ForeshadowMemory(
                            id=f"foreshadow_{len(foreshadows) + 1:03d}",
                            chapter_id=chapter.id,
                            description=description,
                            status="unresolved",
                            importance=5 if word in ["匿名信", "旧钥匙", "录音笔", "仓库"] else 4,
                        )
                    )

    if "林夏" in character_names and "顾言" in character_names:
        relationships.append(
            RelationshipMemory(
                id="relationship_001",
                source="林夏",
                target="顾言",
                relation="旧识重逢，存在误会和隐瞒。",
                evidence="林夏与顾言在旧楼、会议室或仓库对峙。",
            )
        )
    if "林夏" in character_names and "林建平" in character_names:
        relationships.append(
            RelationshipMemory(
                id=f"relationship_{len(relationships)+1:03d}",
                source="林夏",
                target="林建平",
                relation="父女关系，林建平通过录音推动真相揭露。",
                evidence="文本中出现林建平是林夏父亲。",
            )
        )

    characters = []
    for index, name in enumerate(character_names):
        role, traits, motivation = _role_profile(name)
        ev = evidence.get(name, [])
        characters.append(
            CharacterMemory(
                id=f"char_{index + 1:03d}",
                name=name,
                role=role,
                traits=traits,
                motivation=motivation,
                first_seen=ev[0] if ev else "根据小说证据识别",
                current_state="参与当前改编主线",
            )
        )

    return NovelMemory(
        characters=characters,
        relationships=relationships,
        events=events,
        foreshadows=foreshadows,
        timeline=timeline,
    )
