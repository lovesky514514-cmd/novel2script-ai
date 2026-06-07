from copy import deepcopy
from typing import List

from app.models.schemas import ConvertResult, ScriptScene
from app.services.report_generator import generate_quality_report
from app.services.yaml_generator import dump_script_yaml


def _contains_any(text: str, keys: List[str]) -> bool:
    return any(key in text for key in keys)


def _pick_target_scene(scenes: List[ScriptScene], instruction: str) -> int:
    chapter_digits = {
        "第一": 1, "第1": 1, "一": 1,
        "第二": 2, "第2": 2, "二": 2,
        "第三": 3, "第3": 3, "三": 3,
        "第四": 4, "第4": 4, "四": 4,
        "第五": 5, "第5": 5, "五": 5,
    }

    for key, number in chapter_digits.items():
        if key in instruction:
            for index, scene in enumerate(scenes):
                if scene.source_chapter == number or str(number) in scene.title:
                    return index

    location_keys = ["仓库", "雨夜", "旧楼", "会议室", "录音", "钥匙", "重逢"]
    for key in location_keys:
        if key in instruction:
            for index, scene in enumerate(scenes):
                joined = " ".join([
                    scene.title or "",
                    scene.location or "",
                    scene.conflict or "",
                    " ".join(scene.action or []),
                ])
                if key in joined:
                    return index

    return 0


def revise_script_result(result: ConvertResult, instruction: str) -> ConvertResult:
    revised = result.model_copy(deep=True)
    instruction = (instruction or "").strip()
    if not instruction:
        return revised

    target_index = _pick_target_scene(revised.scenes, instruction)
    scene = revised.scenes[target_index]

    changes: List[str] = []

    if _contains_any(instruction, ["对白", "自然", "口语"]):
        scene.dialogue.append({
            "speaker": scene.characters[0] if scene.characters else "角色",
            "line": "我不是想逼你回答，我只是想知道，当年你到底瞒了我什么。",
            "emotion": "克制",
            "subtext": "把质问压在平静语气里，让关系张力更明显。",
        })
        changes.append("已补强对白，让人物表达更自然。")

    if _contains_any(instruction, ["重点", "扩写", "细致", "多写", "详细"]):
        scene.action.extend([
            "镜头停在关键道具上，角色的迟疑让观众意识到这里还有隐情。",
            "对方没有立刻回答，场面短暂停顿，压出本场的情绪张力。",
        ])
        scene.purpose = f"{scene.purpose} 本场按用户要求增加细节，但不改变核心事实。"
        changes.append("已增加动作细节，但控制在原场景范围内。")

    if _contains_any(instruction, ["钩子", "反转", "悬念"]):
        scene.action.append("场尾出现新的线索，打断人物原本的判断。")
        scene.notes = f"{scene.notes} 场尾已增加悬念钩子。".strip()
        changes.append("已增强场尾钩子。")

    if _contains_any(instruction, ["压缩", "删掉", "精简"]):
        scene.action = scene.action[: max(2, min(len(scene.action), 3))]
        scene.dialogue = scene.dialogue[: max(1, min(len(scene.dialogue), 2))]
        scene.notes = f"{scene.notes} 已按要求精简场面。".strip()
        changes.append("已压缩动作和对白。")

    if _contains_any(instruction, ["不要改变", "保留", "别改", "不能改"]):
        scene.notes = f"{scene.notes} 保留用户指定的核心伏笔或事实，不改动主线真相。".strip()
        changes.append("已加入保留约束。")

    if not changes:
        scene.notes = f"{scene.notes} 用户修改要求：{instruction}".strip()
        changes.append("已记录修改要求。")

    report = generate_quality_report(revised.memory, revised.scenes, True, [])
    revised.quality_report = report
    revised.yaml_text = dump_script_yaml(
        revised.title,
        len(revised.chapters),
        revised.memory,
        revised.scenes,
        report,
        revised.analysis,
        revised.requirement_plan,
        revised.knowledge_trace,
        revised.validation_report,
    )
    return revised
