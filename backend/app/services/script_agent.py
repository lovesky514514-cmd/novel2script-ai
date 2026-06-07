from typing import List

from app.models.schemas import Chapter, NovelMemory, ScriptScene
from app.services.context_builder import build_scene_context


def generate_demo_scenes(chapters: List[Chapter], memory: NovelMemory) -> List[ScriptScene]:
    scenes: List[ScriptScene] = []

    for index, chapter in enumerate(chapters, start=1):
        context = build_scene_context(chapter, memory, intent="script_writer")
        events = context["events"]
        characters = context["characters"] or ["未知角色"]
        source_event_ids = [event["id"] for event in events]

        conflict = events[0]["conflict"] if events else "本场冲突待识别。"
        location = events[0]["location"] if events else "待识别地点"

        scenes.append(
            ScriptScene(
                id=f"scene_{index:03d}",
                title=f"{chapter.title} 改编场景",
                source_chapter=index,
                source_events=source_event_ids,
                location=location,
                time="待细化时间",
                characters=characters,
                conflict=conflict,
                purpose="保留原章节关键事件，并转化为可表演场景。",
                action=[
                    "角色进入场景，动作暴露当前状态。",
                    "场景中的道具或空间承担情绪表达。",
                    "场景以未完全解决的问题结束。",
                ],
                dialogue=[
                    {
                        "speaker": characters[0],
                        "line": "这件事你早就知道，对不对？",
                        "emotion": "克制",
                        "subtext": "表面追问事实，实际确认关系裂缝。",
                    }
                ],
                notes="Demo 模式场景。AI 模式下将由 Script Writer 生成初稿。",
            )
        )

    return scenes
