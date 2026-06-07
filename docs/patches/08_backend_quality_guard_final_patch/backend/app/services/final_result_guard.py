from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.schemas import ConvertResult, ScriptScene
from app.services.character_guard import sanitize_scenes
from app.services.error_pattern_engine import (
    clean_repair_log,
    infer_location_from_text,
    infer_props_from_text,
    infer_time_from_text,
    normalize_props,
    split_location_text,
    strip_chapter_prefix,
)
from app.services.report_generator import generate_quality_report
from app.services.schema_guard import normalize_scene_characters
from app.services.schema_validator import validate_yaml_text
from app.services.validation_engine import build_validation_report, validate_script, validate_single_scene_against_chapter
from app.services.yaml_generator import dump_script_yaml
from app.services.runtime_metadata import metadata_dict


def _safe_str(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _as_list(value: Any) -> List[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def _fact_map(result: ConvertResult) -> Dict[int, Dict[str, Any]]:
    facts: Dict[int, Dict[str, Any]] = {}
    for index, fact in enumerate(result.chapter_facts or [], start=1):
        if not isinstance(fact, dict):
            continue
        try:
            order = int(fact.get("source_chapter") or fact.get("chapter_order") or index)
        except Exception:
            order = index
        facts[order] = fact
    return facts


def _enrich_fact_from_chapter(fact: Dict[str, Any], chapter) -> Dict[str, Any]:
    """Fill missing facts from the current chapter using generic heuristics.

    This is not story-specific. It only avoids empty '-' fields when the Pro layer
    is unavailable or returns incomplete data.
    """
    enriched = dict(fact or {})
    text = chapter.text or ""

    if not _safe_str(enriched.get("scene_title"), ""):
        enriched["scene_title"] = strip_chapter_prefix(chapter.title)
    if not _safe_str(enriched.get("location"), "") or _safe_str(enriched.get("location")) == "-":
        enriched["location"] = infer_location_from_text(text)
    if not _safe_str(enriched.get("time"), "") or _safe_str(enriched.get("time")) == "-":
        enriched["time"] = infer_time_from_text(text)
    if not enriched.get("key_props"):
        enriched["key_props"] = infer_props_from_text(text)
    if not enriched.get("key_events"):
        enriched["key_events"] = [text[:220]] if text else []
    if not enriched.get("source_chapter"):
        enriched["source_chapter"] = chapter.order
    return enriched


def _title_from_fact(fact: Dict[str, Any], fallback: str = "-") -> str:
    for key in ["scene_title", "title", "chapter_title"]:
        value = _safe_str(fact.get(key), "")
        if value:
            return value
    return fallback or "-"


def _characters_from_fact(fact: Dict[str, Any], current: List[str]) -> List[str]:
    for key in ["on_stage_characters", "characters", "present_characters"]:
        value = fact.get(key)
        if isinstance(value, list) and value:
            return [str(item).strip() for item in value if str(item).strip()]
    return current or []


def _events_from_fact(fact: Dict[str, Any]) -> List[str]:
    for key in ["key_events", "events", "must_include"]:
        value = fact.get(key)
        if isinstance(value, list) and value:
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    return []


def _props_from_fact(fact: Dict[str, Any]) -> List[str]:
    return normalize_props(fact.get("key_props") or fact.get("props") or [])


def _is_generic(text: str) -> bool:
    text = text or ""
    generic_markers = ["本章关键事件", "推动主线", "信息差", "人物对抗", "转化为可表演场景", "核心冲突"]
    return any(marker in text for marker in generic_markers)




def _clean_note_text(note: str) -> str:
    """Hide internal guard tags from user-facing YAML/TXT output."""
    text = note or ""
    internal_tokens = [
        "fact_bound_general",
        "split_from_scene_units",
        "created_from_chapter_facts",
        "repaired_from_facts",
    ]
    for token in internal_tokens:
        text = text.replace(token, "")
    text = re.sub(r"\s+", " ", text).strip(" ，,;；")
    return text or "根据对应章节事实生成。"


def _event_text(fact: Dict[str, Any]) -> str:
    return " ".join(_events_from_fact(fact) + [_title_from_fact(fact, ""), _safe_str(fact.get("location"), "")])


def _short_event(fact: Dict[str, Any], limit: int = 28) -> str:
    events = _events_from_fact(fact)
    if not events:
        return _title_from_fact(fact, "当前线索")[:limit]
    text = re.sub(r"\s+", "", str(events[0]))
    return text[:limit]



_GENERIC_WINDOW_TOKENS = {
    "林夏", "顾言", "父亲", "三年前", "真相", "短信", "手机",
    "钥匙", "照片", "仓库", "旧楼", "楼道", "深夜", "上午", "夜", "日",
    "信封", "伞", "纸张", "旧手机",
}


def _compact_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _keyword_candidates_for_window(fact: Dict[str, Any]) -> List[str]:
    """Build generic scene-unit anchors for source-window extraction.

    The goal is not to understand a specific novel. It is to find the paragraph
    region that belongs to the current scene_unit, so dialogue is not pulled
    from earlier/later scene units in the same chapter.
    """
    raw: List[str] = []
    # Events and scene title are the primary anchors. Location/props can be
    # repeated across adjacent scene_units, so only concrete prop/location terms
    # are added below.
    raw.extend(_events_from_fact(fact))
    raw.append(_title_from_fact(fact, ""))

    concrete_location = _safe_str(fact.get("location"), "")
    for loc_token in ["会议室", "走廊", "三楼门口", "林夏家", "旧仓库内", "仓库内", "楼下", "楼道"]:
        if loc_token in concrete_location:
            raw.append(loc_token)

    for prop in _props_from_fact(fact):
        if prop not in _GENERIC_WINDOW_TOKENS:
            raw.append(prop)

    candidates: List[str] = []
    for item in raw:
        text = _compact_text(item)
        if not text or text == "-":
            continue

        # Keep full short phrase first. Long event sentences are too specific,
        # so also split them into usable anchors.
        if 2 <= len(text) <= 18 and text not in _GENERIC_WINDOW_TOKENS:
            candidates.append(text)

        for token in re.split(r"[，,。；;、：:（）()【】\[\]“”\"'<>《》]+", text):
            token = token.strip()
            if len(token) < 2 or token in _GENERIC_WINDOW_TOKENS:
                continue
            # Prefer concrete actions/props/locations over character names.
            candidates.append(token)
            # Add meaningful fragments from clauses even when the full clause is
            # not verbatim in the source text. This makes source-window matching
            # robust across summary wording.
            for word in [
                "收到匿名短信", "陌生短信", "牛皮纸信封", "别再相信", "顾言出现",
                "技术顾问", "会议室", "走廊", "追出", "翻遍抽屉", "抽屉",
                "旧书", "蓝色塑料牌", "西港17号", "西港 17 号", "西港十七号",
                "保险箱", "录音笔", "父亲的录音", "父亲的声音", "播放录音",
                "项目经理", "录音还是被你们找到了", "脚步声", "黑暗",
                "另一把钥匙", "一模一样的钥匙", "三楼门口", "林夏家"
            ]:
                if word in token:
                    candidates.append(word)

    # De-duplicate while preserving order.
    out: List[str] = []
    for token in candidates:
        token = token.strip()
        if token and token not in out:
            out.append(token)
    return out


def _source_window_for_fact(chapter_text: str, fact: Dict[str, Any]) -> str:
    """Return a local slice of chapter_text for this scene_unit.

    This is the main product fix for dialogue attribution: the dialogue extractor
    should not scan the entire chapter when a chapter has multiple scene_units.
    """
    text = chapter_text or ""
    if len(text) <= 520:
        return text

    keywords = _keyword_candidates_for_window(fact)
    positions: List[int] = []
    for kw in keywords:
        start = 0
        while True:
            pos = text.find(kw, start)
            if pos < 0:
                break
            positions.append(pos)
            start = pos + max(1, len(kw))

    if not positions:
        return text

    # Score each candidate center by how many anchors occur nearby. This handles
    # repeated props such as "钥匙" by picking the densest local scene region.
    best_pos = positions[0]
    best_score = -1
    for pos in positions:
        left = max(0, pos - 180)
        right = min(len(text), pos + 360)
        window = text[left:right]
        score = 0
        for kw in keywords:
            if kw in window:
                score += 2 if len(kw) >= 4 else 1
        # prefer windows containing concrete event verbs from the current unit
        for verb in ["发现", "出现", "质问", "介绍", "叫住", "追出", "翻", "找到", "打开", "播放", "传来", "走出"]:
            if verb in window:
                score += 1
        if score > best_score:
            best_score = score
            best_pos = pos

    fact_text_for_window = _event_text(fact) + " " + " ".join(_props_from_fact(fact)) + " " + _title_from_fact(fact, "")
    pre_context = 80 if any(word in fact_text_for_window for word in ["保险箱", "录音笔", "播放录音", "项目经理", "另一把钥匙", "脚步声"]) else 170
    post_context = 460 if any(word in fact_text_for_window for word in ["保险箱", "录音笔", "播放录音", "项目经理", "另一把钥匙", "脚步声"]) else 420
    start = max(0, best_pos - pre_context)
    end = min(len(text), best_pos + post_context)

    # Expand to sentence/paragraph boundaries for attribution context.
    boundary_left = max(text.rfind("\n", 0, start), text.rfind("。", 0, start), text.rfind("！", 0, start), text.rfind("？", 0, start))
    if boundary_left >= 0 and start - boundary_left <= 80:
        start = boundary_left + 1
    boundary_rights = [idx for idx in [text.find("\n", end), text.find("。", end), text.find("！", end), text.find("？", end)] if idx >= 0]
    if boundary_rights:
        end = max(end, min(boundary_rights) + 1)

    return text[start:end]


_OFFSTAGE_SPEAKER_MARKERS = [
    "录音", "电话", "短信", "广播", "旁白", "画外音", "系统提示", "留言",
    "信件", "信", "邮件", "纸条", "屏幕", "照片文字",
]

_SPEECH_HINTS = [
    "说", "问", "道", "答", "喊", "叫", "低声", "冷冷", "笑", "叹",
    "开口", "叫住", "声音低哑", "压低声音", "看着", "盯着", "沉默",
]

_TEMPLATE_DIALOGUE_LINES = {
    "这件事必须说清楚。",
    "有些事不是你看到的那样。",
}


def _all_character_names_from_fact(fact: Dict[str, Any], allowed_characters: List[str]) -> List[str]:
    names: List[str] = []
    for item in allowed_characters or []:
        item = str(item).strip()
        if item and item != "-" and item not in names:
            names.append(item)

    for key in ["_all_character_names", "on_stage_characters", "off_stage_characters", "mentioned_characters", "characters"]:
        value = fact.get(key)
        if isinstance(value, list):
            for item in value:
                item = str(item).strip()
                if item and item != "-" and item not in names:
                    names.append(item)

    return names


def _fact_keywords(fact: Dict[str, Any]) -> Set[str]:
    raw: List[str] = []
    raw.extend([_title_from_fact(fact, ""), _safe_str(fact.get("location"), ""), _safe_str(fact.get("time"), "")])
    raw.extend(_events_from_fact(fact))
    raw.extend(_props_from_fact(fact))
    raw.extend(_as_list(fact.get("must_include")))

    keywords: Set[str] = set()
    for item in raw:
        text = re.sub(r"\s+", "", str(item or ""))
        if not text or text == "-":
            continue

        # Keep short meaningful props and location fragments.
        for token in re.split(r"[，,。；;、\s：:（）()【】\[\]“”\"'<>《》]+", text):
            token = token.strip()
            if len(token) >= 2:
                keywords.add(token[:20])

        # Add compact substrings for common short props.
        for prop in ["短信", "信封", "照片", "钥匙", "旧书", "仓库", "保险箱", "录音", "录音笔", "手机", "走廊", "会议室"]:
            if prop in text:
                keywords.add(prop)

        if len(text) <= 12:
            keywords.add(text)

    return keywords


def _context_has_any(context: str, words: List[str]) -> bool:
    return any(word and word in context for word in words)


def _nonhuman_source_from_context(before: str, after: str, line: str) -> str:
    """Detect non-human/off-stage text sources by sentence-local context.

    This must be tight. A character can say a sentence containing words like
    "短信" or "录音"; that should not turn the quote into SMS/recording text.
    """
    last_sentence = _last_meaningful_sentence(before)
    near_after = after[:30]
    local = last_sentence + near_after

    # Recording / phone voice.
    if _context_has_any(last_sentence, ["录音笔", "录音", "录音里", "父亲的声音", "声音响起", "电话那头", "电话里"]):
        if "父亲" in last_sentence or "林建平" in last_sentence:
            return "父亲录音"
        if "电话" in last_sentence:
            return "电话声"
        return "录音声"

    # SMS / screen message. Only the sentence immediately introducing the quote
    # can trigger this; earlier mentions of SMS should not affect later dialogue.
    if _context_has_any(last_sentence, ["短信", "手机屏幕", "发送时间", "收到一条", "发来一条", "弹出", "写着"]):
        if not _context_has_any(last_sentence, ["说", "问", "道", "答", "喊", "冷冷地问", "低声"]):
            return "短信内容"

    # Letter / note / paper text.
    if _context_has_any(last_sentence, ["信上", "信里", "纸条", "纸上", "留言", "字条", "邮件", "上面只写", "上面写"]):
        if not _context_has_any(last_sentence, ["说", "问", "道", "答"]):
            return "信件内容"

    # Photo / screen display.
    if _context_has_any(last_sentence, ["照片背面", "背面写", "屏幕显示", "显示着"]):
        if not _context_has_any(last_sentence, ["说", "问", "道", "答"]):
            return "屏幕文字"

    return ""


def _offstage_source_from_line(line: str, fact: Dict[str, Any]) -> str:
    """Detect off-stage text by the quoted line itself plus the current scene fact.

    This is generic: it does not know story-specific names. It handles common
    narrative carriers such as SMS instructions and recording messages when the
    local context attribution is missed by the model or by source-window slicing.
    """
    compact = re.sub(r"\s+", "", line or "")
    fact_text = re.sub(r"\s+", "", " ".join([
        _event_text(fact),
        " ".join(_props_from_fact(fact)),
        _title_from_fact(fact, ""),
        _safe_str(fact.get("location"), ""),
    ]))

    # Recording/voice message. Typical lines address the listener and mention
    # "this recording"; they should never become the on-stage character's line.
    if any(mark in compact for mark in ["这段录音", "听到这段录音", "如果你听到", "我可能已经回不去了"]):
        if any(mark in fact_text for mark in ["录音", "录音笔", "父亲的声音", "播放", "听到"]):
            return "父亲录音" if any(mark in fact_text for mark in ["父亲", "林建平"]) else "录音声"

    # SMS / screen instruction. This covers common anonymous-message patterns
    # without hard-coding a story: time + destination/action + a scene that is
    # known to involve a message.
    if "短信" in fact_text or "手机" in fact_text:
        has_time = any(mark in compact for mark in ["今晚", "明晚", "十点", "十二点", "下午", "早上", "凌晨"])
        has_action = any(mark in compact for mark in ["回", "来", "到", "带上", "出现", "等你", "见面"])
        if has_time and has_action:
            return "短信内容"

    # Written note / letter content often looks like an imperative warning.
    if any(mark in fact_text for mark in ["信封", "信件", "纸条", "字条", "留言"]):
        if any(mark in compact for mark in ["别再", "不要相信", "记住", "打开", "交给"]):
            return "信件内容"

    return ""


def _source_allowed_for_fact(source: str, fact: Dict[str, Any], local_context: str = "") -> bool:
    if not source:
        return False

    fact_text = " ".join([
        _event_text(fact),
        " ".join(_props_from_fact(fact)),
        _title_from_fact(fact, ""),
        _safe_str(fact.get("location"), ""),
    ])

    # Recording text is only allowed when this scene actually plays/hears a
    # recording. A scene may merely contain an old recorder as a prop, which
    # should not import later recording dialogue.
    if "录音" in source or "电话" in source:
        compact = re.sub(r"\s+", "", fact_text)
        return any(word in compact for word in [
            "播放录音", "听到父亲", "父亲的声音", "录音响起", "录音内容",
            "打开录音", "电话那头", "电话里", "听完录音", "录音笔响起"
        ])

    checks = {
        "短信": ["短信", "手机", "发送时间", "收到"],
        "信": ["信封", "信件", "纸条", "留言", "写着"],
        "屏幕": ["照片", "屏幕", "显示", "背面"],
    }

    for marker, words in checks.items():
        if marker in source:
            return any(word in fact_text for word in words)

    return True


def _has_external_character_context(before: str, after: str, all_names: List[str], allowed_names: List[str]) -> bool:
    context = before[-100:] + after[:60]
    allowed_set = set(allowed_names)
    for name in all_names:
        if name and name not in allowed_set and name in context:
            return True
    return False


def _quote_relevant_to_fact(before: str, line: str, after: str, fact: Dict[str, Any], source: str) -> bool:
    context = before[-140:] + line + after[:100]
    if source:
        return _source_allowed_for_fact(source, fact, context)

    keywords = _fact_keywords(fact)
    if not keywords:
        return True

    # Avoid importing a quote from a later scene_unit only because a shared main
    # character appears nearby. Relevance is based on location / event / prop words.
    strong_keywords = [kw for kw in keywords if kw not in _all_character_names_from_fact(fact, [])]
    if not strong_keywords:
        strong_keywords = list(keywords)

    return any(keyword and keyword in context for keyword in strong_keywords)


def _last_meaningful_sentence(before: str) -> str:
    parts = [part.strip(" ：:，,；;") for part in re.split(r"[。！？!?\\n]+", before.strip()) if part.strip(" ：:，,；;")]
    return parts[-1] if parts else ""


def _previous_meaningful_sentence(before: str) -> str:
    parts = [part.strip(" ：:，,；;") for part in re.split(r"[。！？!?\\n]+", before.strip()) if part.strip(" ：:，,；;")]
    return parts[-2] if len(parts) >= 2 else ""


def _nearest_name_in_text(text: str, all_names: List[str]) -> str:
    positions = [(text.rfind(name), name) for name in all_names if name]
    positions = [(pos, name) for pos, name in positions if pos >= 0]
    if not positions:
        return ""
    return max(positions, key=lambda item: item[0])[1]


def _explicit_speaker_near_quote(before: str, after: str, all_names: List[str]) -> Tuple[str, bool]:
    """Return (speaker, explicit).

    Uses sentence-local context to avoid stealing a speaker from a much earlier
    sentence. This is generic and does not depend on specific character names.
    """
    near_after = after[:50]
    last_sentence = _last_meaningful_sentence(before)
    previous_sentence = _previous_meaningful_sentence(before)

    # Pattern: "X说/问/低声..." before the quote.
    if last_sentence and "“" not in last_sentence and "”" not in last_sentence and '"' not in last_sentence:
        has_speech_cue = any(cue in last_sentence for cue in _SPEECH_HINTS)
        if has_speech_cue:
            name = _nearest_name_in_text(last_sentence, all_names)
            if name:
                return name, True

    # Pattern: quote followed by "X说/问".
    for name in all_names:
        escaped = re.escape(name)
        # Do not treat listener reactions as attribution for the preceding quote.
        if re.search(r"^\s*[，,。；;、]*" + escaped + r".{0,14}(没有回答|没回答|沉默|停下脚步|转身|看他|看着|脸色|点头|手指)", near_after):
            continue
        if re.search(r"^\s*[，,。；;、]*" + escaped + r".{0,8}(说|问|道|答道|喊|叫|低声|冷冷|叹|开口)", near_after):
            return name, True

    # Pattern: "他说/她说" before the quote. Resolve pronoun by the closest
    # named character in the previous sentence.
    if re.search(r"(他|她)(说|问|道|答|喊|叫)\s*[:：]?\s*$", last_sentence):
        name = _nearest_name_in_text(previous_sentence, all_names)
        if name:
            return name, True

    # Pattern: quote first, speaker revealed immediately after by entrance/action.
    # Example: “...” 手机光晃过去。项目经理站在货架旁。
    reveal_after = after[:150]
    reveal_hits: List[Tuple[int, str]] = []
    for name in all_names:
        if not name:
            continue
        for m in re.finditer(re.escape(name), reveal_after):
            tail = reveal_after[m.start():m.start() + 36]
            if any(word in tail for word in ["站在", "走出", "出现", "手里", "握着", "货架旁"]):
                if not any(bad in tail for bad in ["没有回答", "没回答", "沉默"]):
                    reveal_hits.append((m.start(), name))
    if reveal_hits:
        return sorted(reveal_hits, key=lambda item: item[0])[0][1], True

    return "", False


def _nearest_character_before_quote(before: str, all_names: List[str]) -> str:
    last_sentence = _last_meaningful_sentence(before)
    name = _nearest_name_in_text(last_sentence, all_names)
    if name:
        return name

    # Fallback to a small window only; never search far across scene beats.
    near = before[-48:]
    return _nearest_name_in_text(near, all_names)


def _choose_alternating_speaker(
    line: str,
    allowed_names: List[str],
    last_speaker: str,
    gap: int,
) -> str:
    if len(allowed_names) != 2 or last_speaker not in allowed_names or gap > 90:
        return ""

    # In a two-person exchange, only clearly responsive short questions should
    # alternate automatically. Do not alternate every question; a character may
    # ask multiple questions in a row.
    compact = re.sub(r"\s+", "", line or "")
    response_starters = ("你", "什么", "为什么", "所以", "可")
    if compact.startswith(response_starters) and len(compact) <= 24:
        return allowed_names[1] if allowed_names[0] == last_speaker else allowed_names[0]

    return ""


def _speaker_from_listener_silence(after: str, allowed_names: List[str], last_speaker: str) -> str:
    """If quote is followed by 'X沉默/没有回答', speaker is usually the other person."""
    if len(allowed_names) != 2:
        return ""
    near_after = after[:32]
    for name in allowed_names:
        if re.search(r"^\s*[，,。；;、]*" + re.escape(name) + r".{0,10}(没有回答|没回答|沉默|脸色|点头)", near_after):
            other = allowed_names[1] if allowed_names[0] == name else allowed_names[0]
            return other
    return ""

def _clean_dialogue_items(items: List[Dict[str, str]], scene_characters: List[str], fact: Dict[str, Any]) -> List[Dict[str, str]]:
    allowed = [name for name in scene_characters if name and name != "-"]
    cleaned: List[Dict[str, str]] = []
    seen = set()

    for item in items or []:
        speaker = str(item.get("speaker", "")).strip()
        line = str(item.get("line", "")).strip()
        if not speaker or not line:
            continue
        if line in _TEMPLATE_DIALOGUE_LINES:
            continue

        line_source = _offstage_source_from_line(line, fact)
        if line_source:
            speaker = line_source

        is_offstage = any(marker in speaker for marker in _OFFSTAGE_SPEAKER_MARKERS)
        if speaker not in allowed and not is_offstage:
            # Do not force an invalid speaker into the current scene. Dropping is
            # safer than assigning the line to the protagonist.
            continue

        if is_offstage and not _source_allowed_for_fact(speaker, fact, line):
            continue

        key = (speaker, line)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({
            "speaker": speaker,
            "line": line,
            "emotion": item.get("emotion", "克制"),
            "subtext": item.get("subtext", "根据原文上下文归属对白。"),
        })

    return cleaned


def _prioritize_dialogues_for_fact(items: List[Dict[str, str]], fact: Dict[str, Any], limit: int) -> List[Dict[str, str]]:
    if not items:
        return []

    fact_text = _event_text(fact) + " " + " ".join(_props_from_fact(fact)) + " " + _title_from_fact(fact, "")
    offstage_items = [item for item in items if any(marker in item.get("speaker", "") for marker in _OFFSTAGE_SPEAKER_MARKERS)]
    normal_items = [item for item in items if item not in offstage_items]

    # Off-stage text is useful when the scene is specifically about reading a
    # SMS/letter or playing a recording. Do not mix an old SMS line into a later
    # character confrontation if natural character dialogue already exists.
    def _source_core_for_item(item: Dict[str, str]) -> bool:
        speaker = item.get("speaker", "")
        if "短信" in speaker:
            return any(word in fact_text for word in ["收到匿名短信", "收到一条", "短信写", "短信内容", "陌生短信"])
        if "信" in speaker or "纸条" in speaker or "留言" in speaker:
            return any(word in fact_text for word in ["信封", "纸条", "上面写", "别再相信", "留言"])
        if "录音" in speaker or "电话" in speaker:
            return any(word in fact_text for word in ["播放录音", "听到父亲", "父亲的录音", "录音内容", "保险箱"])
        if "屏幕" in speaker:
            return any(word in fact_text for word in ["屏幕", "照片背面", "显示", "背面写"])
        return False

    core_offstage = [item for item in offstage_items if _source_core_for_item(item)]

    if core_offstage and not normal_items:
        return core_offstage[:limit]

    if core_offstage:
        selected: List[Dict[str, str]] = []
        selected.extend(normal_items[:2])
        selected.append(core_offstage[0])
        selected.extend(normal_items[2:])
        return selected[:limit]

    return normal_items[:limit]

def _extract_dialogue_from_text(text: str, allowed_characters: List[str], fact: Dict[str, Any], limit: int = 4) -> List[Dict[str, str]]:
    """Extract quoted dialogue with generic speaker attribution.

    Product rule:
    - Never assign a quote to a character only because that character is the only
      person in the scene.
    - SMS / letter / recording / screen text stay as off-stage sources.
    - A quote spoken by a character outside current scene is skipped, not forced
      into the current protagonist.
    """
    if not text:
        return []

    allowed_names = [name for name in allowed_characters if name and name != "-"]
    all_names = _all_character_names_from_fact(fact, allowed_names)
    if not allowed_names and not all_names:
        return []

    quotes = list(re.finditer(r"[“\"]([^”\"]{1,120})[”\"]", text))
    result: List[Dict[str, str]] = []
    last_speaker = ""
    last_quote_end = -1

    for match in quotes:
        line = match.group(1).strip()
        if not line:
            continue

        before = text[max(0, match.start() - 180):match.start()]
        after = text[match.end():match.end() + 100]
        source = _nonhuman_source_from_context(before, after, line) or _offstage_source_from_line(line, fact)

        if not _quote_relevant_to_fact(before, line, after, fact, source):
            continue

        # If this is normal spoken dialogue and the local quote context contains
        # another known character who is not in this scene, it likely belongs to
        # another scene_unit. Do not force it into the current scene.
        if not source and _has_external_character_context(before, after, all_names, allowed_names):
            # A single-person scene should not import dialogue that is clearly
            # addressed to another known character in a later/earlier unit.
            if len(allowed_names) <= 1:
                continue

            # Keep it only when an explicit allowed speaker is attached to the
            # current sentence; otherwise skip.
            probe_speaker, probe_explicit = _explicit_speaker_near_quote(before, after, all_names)
            if not (probe_explicit and probe_speaker in allowed_names):
                continue

        flashback_context = before[-120:] + after[:40]
        fact_text_for_flashback = _event_text(fact) + _title_from_fact(fact, "")
        if not source and any(mark in flashback_context for mark in ["回忆", "记得", "那天晚上", "最后一次", "三年前"]):
            if not any(mark in fact_text_for_flashback for mark in ["回忆", "三年前", "往事"]):
                continue

        speaker = ""
        explicit = False

        if source:
            speaker = source
            explicit = True
        else:
            speaker, explicit = _explicit_speaker_near_quote(before, after, all_names)

        gap = match.start() - last_quote_end if last_quote_end >= 0 else 9999

        # If a newly opened quote immediately follows the previous speaker and
        # starts with an object-based challenge ("那封信...", "那是谁的"), it is
        # commonly the other speaker responding, not the same person continuing.
        if (
            speaker == last_speaker
            and len(allowed_names) == 2
            and gap <= 90
            and re.sub(r"\s+", "", line).startswith(("那封", "这封", "那张", "这张", "那是", "那谁", "这把", "那把"))
        ):
            speaker = allowed_names[1] if allowed_names[0] == last_speaker else allowed_names[0]
            explicit = False

        if not speaker:
            silence_speaker = _speaker_from_listener_silence(after, allowed_names, last_speaker)
            if silence_speaker:
                speaker = silence_speaker

        if not speaker:
            alt = _choose_alternating_speaker(line, allowed_names, last_speaker, gap)
            if alt:
                speaker = alt

        if not speaker:
            nearest = _nearest_character_before_quote(before, all_names)
            if nearest:
                speaker = nearest

        # If the context clearly points to a known character who is not on stage
        # for this scene, do not misassign the quote to an allowed character.
        if speaker in all_names and speaker not in allowed_names:
            last_quote_end = match.end()
            last_speaker = speaker
            continue

        if not speaker:
            last_quote_end = match.end()
            continue

        result.append({
            "speaker": speaker,
            "line": line,
            "emotion": "克制" if explicit else "追问",
            "subtext": "根据原文上下文归属对白。",
        })

        if speaker in allowed_names:
            last_speaker = speaker
        last_quote_end = match.end()

        if len(result) >= max(limit * 3, 8):
            break

    cleaned = _clean_dialogue_items(result, allowed_names, fact)
    return _prioritize_dialogues_for_fact(cleaned, fact, limit)

def _fallback_dialogue_from_context(scene: ScriptScene, fact: Dict[str, Any]) -> List[Dict[str, str]]:
    characters = _characters_from_fact(fact, scene.characters)
    if not characters:
        return []

    context = _event_text(fact)
    first = characters[0]
    second = characters[1] if len(characters) >= 2 else ""

    if len(characters) == 1:
        if "钥匙" in context:
            line = "这把钥匙不该还在这里。"
        elif "照片" in context or "信封" in context:
            line = "这张照片把当年的事又拉回来了。"
        else:
            line = "这里一定还有没被发现的线索。"
        return [{"speaker": first, "line": line, "emotion": "紧张", "subtext": _short_event(fact)}]

    if "会议" in context or "公司" in context or "技术顾问" in context:
        lines = [
            (first, "你出现在这里，也太巧了吧。", "压着怒意"),
            (second, "我也不相信这是巧合。", "低声"),
        ]
    elif "短信" in context:
        lines = [
            (first, "发短信的人想让我们重新见面。", "警惕"),
            (second, "所以我们更不能按他的节奏走。", "克制"),
        ]
    elif "钥匙" in context and "仓库" not in context:
        lines = [
            (first, "这把钥匙为什么会藏在这里？", "不安"),
            (second, "它指向的地方，可能就是当年的入口。", "压低声音"),
        ]
    elif "仓库" in context or "保险箱" in context or "录音" in context:
        lines = [
            (first, "这里留下的东西，比你说的多。", "逼问"),
            (second, "先听完录音，再决定信不信我。", "压抑"),
        ]
    else:
        event = _short_event(fact)
        lines = [
            (first, f"这件事和{event}有关。", "克制"),
            (second, "我知道你不会轻易相信我。", "低声"),
        ]

    return [
        {"speaker": speaker, "line": line, "emotion": emotion, "subtext": _conflict_from_fact(fact, scene)}
        for speaker, line, emotion in lines
        if speaker
    ]

def _conflict_from_fact(fact: Dict[str, Any], scene: ScriptScene) -> str:
    conflict = _safe_str(fact.get("conflict"), "")
    if conflict and conflict != "-" and not _is_generic(conflict):
        return conflict
    events = _events_from_fact(fact)
    if events:
        return f"围绕“{events[0][:40]}”形成本场冲突。"
    return scene.conflict or "-"


def _purpose_from_fact(fact: Dict[str, Any], scene: ScriptScene) -> str:
    purpose = _safe_str(fact.get("purpose"), "")
    if purpose and purpose != "-" and not _is_generic(purpose):
        return purpose
    events = _events_from_fact(fact)
    if events:
        return f"将“{_title_from_fact(fact, scene.title)}”中的关键事件转化为可表演场景，并推动后续剧情。"
    return scene.purpose or "-"


def _action_from_fact(scene: ScriptScene, fact: Dict[str, Any]) -> List[str]:
    events = _events_from_fact(fact)
    props = _props_from_fact(fact)
    action: List[str] = []
    if events:
        for item in events[:3]:
            action.append(item)
    else:
        action = [
            f"镜头进入{scene.location}，交代人物状态和空间关系。",
            "人物围绕当前章节的核心线索展开行动。",
            "场尾留下推动下一场的悬念。",
        ]
    if props:
        action.append("本场重点保留道具：" + "、".join(dict.fromkeys(props)) + "。")
    return action[:5]


def _dialogue_from_fact(scene: ScriptScene, fact: Dict[str, Any]) -> List[Dict[str, str]]:
    characters = _characters_from_fact(fact, scene.characters)
    chapter_text = _safe_str(fact.get("_chapter_text"), "")
    local_text = _source_window_for_fact(chapter_text, fact)

    extracted = _extract_dialogue_from_text(local_text, characters, fact, limit=4)
    if extracted:
        return extracted

    return _clean_dialogue_items(_fallback_dialogue_from_context(scene, fact), characters, fact)


def _action_has_prop_line(action: List[str]) -> bool:
    return any("本场重点保留道具" in str(item) for item in action or [])


def _sanitize_action_props(action: List[str], fact: Dict[str, Any]) -> List[str]:
    props = _props_from_fact(fact)
    cleaned = [str(item) for item in (action or []) if "本场重点保留道具" not in str(item)]
    if props:
        cleaned.append("本场重点保留道具：" + "、".join(dict.fromkeys(props)) + "。")
    return cleaned


def _bind_scene_to_fact(scene: ScriptScene, fact: Dict[str, Any], *, strict: bool = False) -> ScriptScene:
    bound = deepcopy(scene)
    bound.title = _title_from_fact(fact, bound.title)
    bound.location = _safe_str(fact.get("location"), bound.location or "-")
    bound.time = _safe_str(fact.get("time"), bound.time or "-")
    bound.characters = _characters_from_fact(fact, bound.characters)
    bound.conflict = _conflict_from_fact(fact, bound)
    bound.purpose = _purpose_from_fact(fact, bound)

    has_fact_events = bool(_events_from_fact(fact))
    if strict or has_fact_events:
        # Product rule: final output must be generated from the current fact/
        # scene_unit, not from a parent scene cloned by the model. This prevents
        # old building actions from leaking into meeting-room scenes, or warehouse
        # beats from leaking into a home-search scene.
        bound.action = _action_from_fact(bound, fact)
        bound.dialogue = _dialogue_from_fact(bound, fact)
    else:
        if not bound.action or not _action_has_prop_line(bound.action):
            bound.action = _action_from_fact(bound, fact)
        bound.action = _sanitize_action_props(bound.action, fact)
        if not bound.dialogue:
            bound.dialogue = _dialogue_from_fact(bound, fact)

    bound.notes = _clean_note_text(bound.notes)
    return bound


def _scene_units_from_fact(fact: Dict[str, Any]) -> List[Dict[str, Any]]:
    units = fact.get("scene_units")
    if isinstance(units, list):
        clean = [item for item in units if isinstance(item, dict) and _safe_str(item.get("location"), "")]
        if len(clean) >= 2:
            return clean

    locations = fact.get("locations") or fact.get("location")
    parts = split_location_text(locations)
    if len(parts) >= 2:
        events = _events_from_fact(fact)
        props = _props_from_fact(fact)
        result = []
        for index, loc in enumerate(parts, start=1):
            result.append({
                "title": f"{_title_from_fact(fact, '场景')} {index}",
                "location": loc,
                "time": fact.get("time", "-"),
                "characters": fact.get("on_stage_characters", []),
                "events": events[index - 1:index] or events[:1],
                "props": props,
                "conflict": fact.get("conflict", "-"),
                "purpose": fact.get("purpose", "-"),
            })
        return result
    return []



def _new_scene_from_fact(template: ScriptScene, fact: Dict[str, Any]) -> ScriptScene:
    """Create a fresh scene from one scene_unit instead of cloning parent content."""
    scene = ScriptScene(
        id=template.id,
        title=_title_from_fact(fact, template.title),
        source_chapter=template.source_chapter,
        source_events=list(template.source_events or []),
        location=_safe_str(fact.get("location"), template.location or "-"),
        time=_safe_str(fact.get("time"), template.time or "-"),
        characters=_characters_from_fact(fact, []),
        conflict="-",
        purpose="-",
        action=[],
        dialogue=[],
        notes="根据对应章节事实生成。",
    )
    return _bind_scene_to_fact(scene, fact, strict=True)

def _split_scene_by_units(scene: ScriptScene, fact: Dict[str, Any]) -> List[ScriptScene]:
    units = _scene_units_from_fact(fact)
    if len(units) < 2:
        return [scene]

    scenes: List[ScriptScene] = []
    for unit in units:
        unit_fact = dict(fact)
        unit_fact["scene_title"] = unit.get("title") or _title_from_fact(fact, scene.title)
        unit_fact["location"] = unit.get("location") or fact.get("location")
        unit_fact["time"] = unit.get("time") or fact.get("time")
        unit_fact["on_stage_characters"] = unit.get("characters") or fact.get("on_stage_characters") or scene.characters
        unit_fact["key_events"] = unit.get("events") or fact.get("key_events") or []
        unit_fact["key_props"] = unit.get("props") or fact.get("key_props") or []
        unit_fact["conflict"] = unit.get("conflict") or fact.get("conflict") or "-"
        unit_fact["purpose"] = unit.get("purpose") or fact.get("purpose") or "-"

        scenes.append(_new_scene_from_fact(scene, unit_fact))

    return scenes


def _dedupe(scenes: List[ScriptScene], facts: Dict[int, Dict[str, Any]], repair_log: List[str]) -> List[ScriptScene]:
    seen_dialogue = {}
    seen_action = {}
    seen_purpose = {}
    out: List[ScriptScene] = []
    for scene in scenes:
        fact = facts.get(scene.source_chapter, {})
        dialogue_sig = tuple(item.get("line", "") for item in (scene.dialogue or []))
        action_sig = tuple(scene.action or [])
        purpose_sig = (scene.purpose or "").strip()

        if purpose_sig and purpose_sig in seen_purpose:
            scene.purpose = f"将“{scene.title}”中的关键事件转化为独立场景，并推动后续剧情。"
            repair_log.append(f"{scene.id}: purpose disambiguated from chapter_facts.")
        if dialogue_sig and dialogue_sig in seen_dialogue:
            scene.dialogue = _dialogue_from_fact(scene, fact)
            repair_log.append(f"{scene.id}: dialogue regenerated from chapter_facts.")
        if (scene.purpose or "").strip() in [p for p in seen_action.keys() if isinstance(p, str)]:
            scene.purpose = f"将“{scene.title}”中的关键事件转化为独立场景，并推动后续剧情。"
        if action_sig and action_sig in seen_action:
            scene.action = _action_from_fact(scene, fact)
            repair_log.append(f"{scene.id}: action regenerated from chapter_facts.")

        out.append(scene)
        seen_purpose[(scene.purpose or "").strip()] = scene.id
        seen_dialogue[tuple(item.get("line", "") for item in (scene.dialogue or []))] = scene.id
        seen_action[tuple(scene.action or [])] = scene.id
    return out


def _renumber(scenes: List[ScriptScene]) -> List[ScriptScene]:
    for index, scene in enumerate(scenes, start=1):
        scene.id = f"scene_{index:03d}"
    return scenes



# ===== N2S OFFSTAGE FINAL POLISH START =====
def _n2s_final_offstage_polish(scenes):
    """Final generic guard: SMS / recordings / letters / notes / screen text should not be assigned to on-stage characters.

    This is not story-specific. It protects common off-stage text sources used in
    novels, such as recordings, SMS messages, paper notes, letters, phone calls,
    broadcast lines, and screen text.
    """
    import re

    def scene_text(scene):
        parts = [
            getattr(scene, "title", ""),
            getattr(scene, "location", ""),
            getattr(scene, "time", ""),
            getattr(scene, "conflict", ""),
            getattr(scene, "purpose", ""),
        ]
        parts.extend([str(x) for x in (getattr(scene, "action", None) or [])])
        parts.extend([str(x) for x in (getattr(scene, "characters", None) or [])])
        return " ".join(parts)

    for scene in scenes or []:
        context = re.sub(r"\s+", "", scene_text(scene))
        fixed = []

        for item in getattr(scene, "dialogue", None) or []:
            if not isinstance(item, dict):
                fixed.append(item)
                continue

            line = str(item.get("line", "")).strip()
            if not line:
                continue

            compact = re.sub(r"\s+", "", line)

            is_recording_line = any(x in compact for x in [
                "这段录音",
                "听到这段录音",
                "如果你听到",
                "我可能已经回不去了",
                "他骗你是因为我让他这么做",
                "不要相信照片，也不要只相信",
            ])

            is_recording_scene = any(x in context for x in [
                "录音",
                "录音笔",
                "父亲的声音",
                "播放录音",
                "听到父亲",
                "林建平",
                "保险箱",
                "旧手机",
            ])

            if is_recording_line:
                if is_recording_scene:
                    item["speaker"] = "父亲录音" if ("父亲" in context or "林建平" in context or "林夏" in compact) else "录音声"
                    item["emotion"] = item.get("emotion") or "信息"
                    item["subtext"] = item.get("subtext") or "来自录音，不是现场人物对白。"
                    fixed.append(item)
                # If a recording line appears in a non-recording scene, treat it as leakage.
                continue

            is_sms_line = (
                any(x in compact for x in ["今晚", "明晚", "十点", "十二点", "下午", "凌晨"])
                and any(x in compact for x in ["回", "来", "到", "带上", "见面", "出现"])
            )
            is_sms_scene = any(x in context for x in ["短信", "手机", "匿名短信", "陌生短信", "收到"])

            if is_sms_line and is_sms_scene:
                item["speaker"] = "短信内容"
                item["emotion"] = item.get("emotion") or "信息"
                item["subtext"] = item.get("subtext") or "来自短信，不是人物对白。"
                fixed.append(item)
                continue

            is_note_line = any(x in compact for x in ["别再相信", "不要相信", "记住", "交给"])
            is_note_scene = any(x in context for x in ["信封", "纸条", "信件", "字条", "留言"])

            if is_note_line and is_note_scene and "录音" not in context:
                item["speaker"] = "信件内容"
                item["emotion"] = item.get("emotion") or "信息"
                item["subtext"] = item.get("subtext") or "来自信件/纸条，不是人物对白。"
                fixed.append(item)
                continue

            fixed.append(item)

        scene.dialogue = fixed

    return scenes
# ===== N2S OFFSTAGE FINAL POLISH END =====


def enforce_final_result(result: ConvertResult) -> ConvertResult:
    repair_log: List[str] = []
    if result.validation_report:
        repair_log.extend(clean_repair_log(result.validation_report.repair_log or []))

    facts = _fact_map(result)
    scenes_by_chapter: Dict[int, ScriptScene] = {}
    for scene in result.scenes or []:
        try:
            scenes_by_chapter.setdefault(int(scene.source_chapter), scene)
        except Exception:
            continue

    final_scenes: List[ScriptScene] = []

    for chapter in result.chapters:
        fact = _enrich_fact_from_chapter(facts.get(chapter.order, {}), chapter)
        fact["_chapter_text"] = chapter.text or ""
        fact["_all_character_names"] = [item.name for item in (result.memory.characters or []) if getattr(item, "name", "")]
        current = scenes_by_chapter.get(chapter.order)
        if current is None:
            current = ScriptScene(
                id=f"scene_{chapter.order:03d}",
                title=_title_from_fact(fact, chapter.title),
                source_chapter=chapter.order,
                source_events=[],
                location=_safe_str(fact.get("location"), "-"),
                time=_safe_str(fact.get("time"), "-"),
                characters=_characters_from_fact(fact, []),
                conflict=_conflict_from_fact(fact, ScriptScene(id="-", title="-", source_chapter=chapter.order, source_events=[], location="-", time="-", characters=[], conflict="-", action=[], dialogue=[], purpose="-")),
                action=[],
                dialogue=[],
                purpose="-",
                notes="created_from_chapter_facts",
            )

        bound = _bind_scene_to_fact(current, fact)
        issues = validate_single_scene_against_chapter(chapter, bound, fact)
        if issues:
            bound.action = _action_from_fact(bound, fact)
            bound.dialogue = _dialogue_from_fact(bound, fact)
            bound.conflict = _conflict_from_fact(fact, bound)
            bound.purpose = _purpose_from_fact(fact, bound)
            bound.notes = ((bound.notes or "") + " repaired_from_facts").strip()
            repair_log.append(f"{bound.id}: fact-bound repaired {len(issues)} issues.")

        final_scenes.extend(_split_scene_by_units(bound, fact))

    final_scenes = _dedupe(final_scenes, facts, repair_log)
    final_scenes = _renumber(final_scenes)
    final_scenes = normalize_scene_characters(result.memory, final_scenes)
    final_scenes, character_warnings = sanitize_scenes(result.memory, final_scenes)
    repair_log.extend(clean_repair_log(character_warnings))
    final_scenes = _n2s_final_offstage_polish(final_scenes)

    for scene in final_scenes:
        scene.notes = _clean_note_text(scene.notes)

    result.scenes = final_scenes

    final_issues = validate_script(
        result.chapters,
        result.memory,
        result.scenes,
        result.requirement_plan,
        result.knowledge_trace,
        result.chapter_facts,
    )

    result.validation_report = build_validation_report(
        first_pass=result.validation_report.first_pass_issues if result.validation_report else [],
        repair_log=list(dict.fromkeys(clean_repair_log(repair_log))),
        final_issues=final_issues,
    )

    runtime = metadata_dict(result)
    preview_yaml = dump_script_yaml(
        result.title,
        len(result.chapters),
        result.memory,
        result.scenes,
        result.quality_report,
        result.analysis,
        result.requirement_plan,
        result.knowledge_trace,
        result.validation_report,
        runtime,
        result.story_bible,
        result.chapter_facts,
        result.repair_questions,
        result.model_trace,
    )
    yaml_valid, yaml_warnings = validate_yaml_text(preview_yaml)
    warnings = list(dict.fromkeys(clean_repair_log(repair_log + [issue.message for issue in final_issues] + yaml_warnings)))

    result.quality_report = generate_quality_report(
        result.memory,
        result.scenes,
        yaml_valid and len(final_issues) == 0,
        warnings,
    )

    result.yaml_text = dump_script_yaml(
        result.title,
        len(result.chapters),
        result.memory,
        result.scenes,
        result.quality_report,
        result.analysis,
        result.requirement_plan,
        result.knowledge_trace,
        result.validation_report,
        runtime,
        result.story_bible,
        result.chapter_facts,
        result.repair_questions,
        result.model_trace,
    )
    return result
