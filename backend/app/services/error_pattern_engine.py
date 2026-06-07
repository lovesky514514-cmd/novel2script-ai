from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml


ROOT = Path(__file__).resolve().parents[1]
PATTERN_PATH = ROOT / "knowledge" / "error_patterns.yaml"


@lru_cache(maxsize=1)
def load_error_patterns() -> Dict[str, Any]:
    if not PATTERN_PATH.exists():
        return {"patterns": []}
    return yaml.safe_load(PATTERN_PATH.read_text(encoding="utf-8")) or {"patterns": []}


def get_pattern(pattern_id: str) -> Dict[str, Any]:
    for pattern in load_error_patterns().get("patterns", []):
        if pattern.get("id") == pattern_id:
            return pattern
    return {}


def get_time_keywords() -> Dict[str, List[str]]:
    return get_pattern("current_scene_time_priority").get("current_scene_time_keywords", {})


def get_offstage_speaker_markers() -> List[str]:
    return get_pattern("offstage_voice_character").get("allow_speaker_markers", [])


def get_offstage_character_fields() -> List[str]:
    return get_pattern("offstage_voice_character").get("fact_fields", [])


def get_location_suffixes() -> List[str]:
    return get_pattern("location_words_not_props").get("location_suffixes", [])


def get_multi_location_separators() -> List[str]:
    return get_pattern("multi_location_should_split").get("separators", [])


def get_stale_log_phrases() -> List[str]:
    return get_pattern("stale_repair_log_noise").get("stale_phrases", [])


def text_contains_calendar_date(text: str) -> bool:
    for item in get_pattern("date_text_not_scene_time").get("ignore_regex", []):
        if re.search(item, text or ""):
            return True
    return False


def clean_repair_log(items: List[Any]) -> List[Any]:
    stale = get_stale_log_phrases()
    cleaned = []
    for item in items or []:
        text = str(item)
        if any(phrase in text for phrase in stale):
            continue
        cleaned.append(item)
    return cleaned


def normalize_prop_name(prop: Any) -> str:
    text = str(prop or "").strip()
    if not text:
        return ""
    text = re.sub(r"[（(].*?[）)]", "", text).strip()
    text = text.replace("：", "").replace(":", "").strip()
    return text


def looks_like_location_word(text: str) -> bool:
    text = str(text or "").strip()
    if not text:
        return False
    suffixes = get_location_suffixes()
    if any(text.endswith(suffix) for suffix in suffixes):
        return True
    # Very common location connective forms, but avoid over-removing short concrete props.
    if any(word in text for word in ["门口", "走廊", "楼道", "仓库", "会议室", "办公室"]):
        return True
    return False


def normalize_props(props: Any) -> List[str]:
    if props is None:
        return []
    if isinstance(props, str):
        raw = re.split(r"[、,，;；/]+", props)
    elif isinstance(props, list):
        raw = props
    else:
        raw = [props]
    result = []
    for item in raw:
        name = normalize_prop_name(item)
        if not name or looks_like_location_word(name):
            continue
        if name not in result:
            result.append(name)
    return result


def split_location_text(location: Any) -> List[str]:
    if isinstance(location, list):
        return [str(item).strip() for item in location if str(item).strip()]
    text = str(location or "").strip()
    if not text:
        return []
    # Treat " / " as a subarea connector, not necessarily a separate scene.
    if " / " in text:
        return [text]
    parts = [text]
    for sep in get_multi_location_separators():
        new_parts = []
        for part in parts:
            if sep in part:
                new_parts.extend([x.strip() for x in part.split(sep) if x.strip()])
            else:
                new_parts.append(part)
        parts = new_parts
    # Split only if the parts look like independent locations.
    if len(parts) >= 2 and sum(1 for p in parts if looks_like_location_word(p)) >= 2:
        return parts
    return [text]



COMMON_PROP_LEXICON = [
    "信封", "匿名信", "信", "照片", "钥匙", "手机", "短信", "纸条", "录音", "录音笔",
    "保险箱", "箱子", "文件", "档案", "合同", "电脑", "笔记本", "书", "旧书",
    "伞", "包", "刀", "枪", "药", "项链", "戒指", "票", "车票", "门卡", "证件",
]


def infer_time_from_text(text: str) -> str:
    keywords = get_time_keywords()
    # Daytime scene markers have priority over future-time message words.
    for item in keywords.get("day", []):
        if item in (text or ""):
            return "日"
    for item in keywords.get("dusk", []):
        if item in (text or ""):
            return "傍晚"
    for item in keywords.get("deep_night", []):
        if item in (text or ""):
            return "深夜"
    for item in keywords.get("night", []):
        if item in (text or ""):
            return "夜"
    return "-"


def infer_location_from_text(text: str) -> str:
    text = text or ""
    # Generic Chinese location suffix extraction. No story-specific names.
    suffixes = get_location_suffixes()
    # Prefer longer chunks around location suffixes.
    candidates = []
    for suffix in sorted(suffixes, key=len, reverse=True):
        for m in re.finditer(r"[\u4e00-\u9fa5A-Za-z0-9]{1,12}" + re.escape(suffix), text):
            item = m.group(0)
            if len(item) >= 2:
                candidates.append(item)
    # Merge near "旧楼/三楼/门口" style fragments into a readable phrase.
    if "旧楼" in text and "三楼" in text:
        if "楼道" in text:
            return "旧楼三楼楼道"
        if "走廊" in text:
            return "旧楼三楼走廊"
        if "门口" in text:
            return "旧楼三楼门口"
        return "旧楼三楼"
    if candidates:
        # Avoid overly generic single "门口" if a stronger candidate exists.
        candidates = sorted(dict.fromkeys(candidates), key=len, reverse=True)
        return candidates[0]
    return "-"


def infer_props_from_text(text: str) -> List[str]:
    text = text or ""
    props = []
    for item in COMMON_PROP_LEXICON:
        if item in text:
            props.append(item)
    return normalize_props(props)


def strip_chapter_prefix(title: str) -> str:
    title = str(title or "").strip()
    title = re.sub(r"^第\s*[\u4e00-\u9fa50-9]+\s*章\s*", "", title).strip()
    return title or "场景"
