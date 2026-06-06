import re
from typing import List

from app.models.schemas import NovelAnalysis, RequirementPlan


def parse_requirement(instruction: str, analysis: NovelAnalysis) -> RequirementPlan:
    text = (instruction or "").strip()
    focus_chapters: List[int] = []

    mapping = {
        "第一章": 1, "第1章": 1, "一章": 1, "第一": 1,
        "第二章": 2, "第2章": 2, "二章": 2, "第二": 2,
        "第三章": 3, "第3章": 3, "三章": 3, "第三": 3,
        "第四章": 4, "第4章": 4, "四章": 4, "第四": 4,
        "第五章": 5, "第5章": 5, "五章": 5, "第五": 5,
    }
    for key, number in mapping.items():
        if key in text and number not in focus_chapters:
            focus_chapters.append(number)

    focus_keywords = []
    for word in ["仓库", "旧楼", "会议室", "重逢", "钥匙", "录音", "匿名信", "照片", "反转", "对白"]:
        if word in text:
            focus_keywords.append(word)

    expand_level = "normal"
    max_new_scenes = 0
    max_expansion_ratio = 1.0
    if any(word in text for word in ["细致", "多写", "扩写", "重点", "详细"]):
        expand_level = "medium"
        max_new_scenes = 1
        max_expansion_ratio = 1.4
    if any(word in text for word in ["大量", "大幅", "非常详细"]):
        expand_level = "high"
        max_new_scenes = 2
        max_expansion_ratio = 1.8
    if any(word in text for word in ["压缩", "简短", "精简", "少一点"]):
        expand_level = "compact"
        max_new_scenes = 0
        max_expansion_ratio = 0.8

    style_constraints = {}
    if any(word in text for word in ["对白", "自然", "口语"]):
        style_constraints["dialogue"] = "对白更自然，避免解释腔。"
    if any(word in text for word in ["节奏", "短剧", "钩子"]):
        style_constraints["pace"] = "节奏更快，场尾保留钩子。"
    if any(word in text for word in ["悬疑", "克制"]):
        style_constraints["tone"] = "悬疑克制，不要过度煽情。"

    preserve = list(analysis.key_props[:])
    for word in ["父亲录音", "录音", "旧钥匙", "钥匙", "匿名信", "仓库", "项目经理", "反转"]:
        if word in text and word not in preserve:
            preserve.append(word)

    avoid = list(analysis.avoid[:])
    if "不要改变" in text or "别改" in text or "不能改" in text:
        avoid.extend(["改变用户指定伏笔", "改变核心真相"])

    return RequirementPlan(
        raw_instruction=text,
        focus_chapters=focus_chapters,
        focus_keywords=focus_keywords,
        expand_level=expand_level,
        max_new_scenes=max_new_scenes,
        max_expansion_ratio=max_expansion_ratio,
        style_constraints=style_constraints,
        preserve=preserve,
        avoid=list(dict.fromkeys(avoid)),
    )
