import yaml
from typing import Any, Dict, List


REQUIRED_TOP_LEVEL = ["metadata", "characters", "memory", "scenes", "quality_report"]
REQUIRED_SCENE_FIELDS = [
    "id", "title", "source_chapter", "source_events", "location",
    "time", "characters", "conflict", "purpose", "action", "dialogue"
]


def validate_yaml_text(yaml_text: str) -> tuple[bool, List[str]]:
    warnings: List[str] = []
    try:
        data = yaml.safe_load(yaml_text)
    except Exception as exc:
        return False, [f"YAML 无法解析：{exc}"]

    if not isinstance(data, dict):
        return False, ["YAML 顶层必须是对象。"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            warnings.append(f"缺少顶层字段：{key}")

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        warnings.append("scenes 必须是列表。")
    else:
        for index, scene in enumerate(scenes, start=1):
            for field in REQUIRED_SCENE_FIELDS:
                if field not in scene:
                    warnings.append(f"第 {index} 场缺少字段：{field}")
            if not scene.get("source_events"):
                warnings.append(f"第 {index} 场缺少来源事件 source_events。")

    return len(warnings) == 0, warnings
