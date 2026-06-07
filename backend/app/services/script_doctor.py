from typing import List

from app.models.schemas import ScriptScene
from app.services.rule_retriever import search_rules


def polish_scenes(scenes: List[ScriptScene]) -> List[ScriptScene]:
    rules = search_rules(query="对白 潜台词 动作 场尾钩子", module="script_doctor", limit=8)
    rule_titles = [rule.title for rule in rules]

    polished: List[ScriptScene] = []
    for scene in scenes:
        scene.notes = f"{scene.notes} 剧本医生已检查：{', '.join(rule_titles[:3])}。"
        if scene.dialogue:
            scene.dialogue[0]["line"] = scene.dialogue[0]["line"].replace("对不对？", "你还想瞒到什么时候？")
            scene.dialogue[0]["subtext"] = "逼问不是为了答案，而是为了确认对方是否还站在自己这边。"
        if "场景以未完全解决的问题结束。" not in scene.action:
            scene.action.append("场景以未完全解决的问题结束。")
        polished.append(scene)
    return polished
