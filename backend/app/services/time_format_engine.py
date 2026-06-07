from pathlib import Path
from typing import Dict

import yaml

_RULE_CACHE: Dict | None = None


def load_time_rules() -> Dict:
    global _RULE_CACHE
    if _RULE_CACHE is not None:
        return _RULE_CACHE

    path = Path(__file__).resolve().parents[1] / "knowledge" / "time_format_rules.yaml"
    if path.exists():
        _RULE_CACHE = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        _RULE_CACHE = {}
    return _RULE_CACHE


def classify_scene_time(text: str, location: str = "") -> str:
    """Return professional Chinese screenplay time label.

    日 = 白天 / 日间，不是日期。
    场景地点优先于台词/短信里的未来时间。
    """
    load_time_rules()
    text = text or ""
    location = location or ""
    combined = f"{text}\n{location}"

    if any(k in location for k in ["会议室", "公司", "办公室", "工作场景"]):
        return "日"

    if any(k in combined for k in ["上午", "下午", "白天", "工作时间", "第二天"]):
        return "日"

    if any(k in combined for k in ["深夜", "凌晨", "夜深", "十二点", "午夜"]):
        return "深夜"
    if any(k in combined for k in ["雨夜", "夜", "晚上", "黑暗", "夜色", "灯光"]):
        return "夜"

    if any(k in combined for k in ["清晨", "黎明", "天刚亮", "早晨"]):
        return "晨"
    if any(k in combined for k in ["中午", "午后"]):
        return "午"
    if any(k in combined for k in ["傍晚", "黄昏", "日落"]):
        return "傍晚"

    return "-"


def classify_scene_space(text: str, location: str = "") -> str:
    load_time_rules()
    combined = f"{text}\n{location}"

    indoor = any(k in combined for k in ["会议室", "走廊", "房间", "仓库里", "仓库内", "教室", "办公室", "楼道"])
    outdoor = any(k in combined for k in ["楼下", "街道", "江边", "门口", "仓库外", "外面"])

    if indoor and outdoor:
        return "内外"
    if indoor:
        return "内"
    if outdoor:
        return "外"
    return "-"
