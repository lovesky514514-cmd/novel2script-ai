from typing import List

from app.models.schemas import Chapter, KnowledgeRule, NovelMemory
from app.services.rule_retriever import search_rules


def build_scene_context(chapter: Chapter, memory: NovelMemory, intent: str = "script_writer") -> dict:
    chapter_events = [event for event in memory.events if event.chapter_id == chapter.id]
    characters = []
    for event in chapter_events:
        characters.extend(event.characters)
    characters = list(dict.fromkeys(characters))

    related_foreshadows = [
        item for item in memory.foreshadows
        if item.chapter_id == chapter.id or item.status == "unresolved"
    ]

    query = " ".join([chapter.title, " ".join(characters), "冲突 对白 场景 钩子"])
    rules: List[KnowledgeRule] = search_rules(query=query, module=intent, limit=10)

    return {
        "chapter": chapter.model_dump(),
        "characters": characters,
        "events": [event.model_dump() for event in chapter_events],
        "foreshadows": [item.model_dump() for item in related_foreshadows],
        "rules": [rule.model_dump() for rule in rules],
    }
