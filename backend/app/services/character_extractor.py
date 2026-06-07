import re
from typing import Dict, List, Tuple


CANONICAL_FIXES = {
    "目经理": "项目经理",
    "经理": "项目经理",
    "技术顾": "",
    "技术顾问": "",
    "一句地": "",
    "他却只": "",
    "夏猛地": "",
    "言同时": "",
    "人轻轻": "",
    "冷冷地": "",
    "没有": "",
    "短信": "",
    "照片": "",
    "钥匙": "",
    "录音": "",
    "仓库": "",
    "旧手机": "",
    "录音笔": "",
    "保险箱": "",
}

# “父亲”和“林建平”在本故事中是同一人，统一成林建平，避免重复角色。
ALIAS_TO_CANONICAL = {
    "父亲": "林建平",
    "林夏父亲": "林建平",
}

KNOWN_CANONICAL = [
    "林夏",
    "顾言",
    "林建平",
    "项目经理",
]

ROLE_TITLES = ["项目经理", "父亲", "母亲", "老师", "医生", "老板", "警察"]

HARD_BAD_WORDS = {
    "她", "他", "我", "你", "它", "有人", "黑暗", "短信", "照片", "钥匙", "录音", "仓库", "楼道", "会议室", "公司",
    "冷冷地", "低声", "低声说", "没有", "如果", "这个", "那个", "什么", "时候", "真相", "技术顾问",
    "一句地", "他却只", "夏猛地", "言同时", "人轻轻", "目经理", "经理", "技术顾",
    "三年前", "十二点", "旧手机", "保险箱", "牛皮纸", "录音笔", "铁门", "货架",
}

SPEECH_VERBS = ["说", "问", "喊", "回答", "开口", "低声说", "冷冷地问"]
ACTION_VERBS = ["看着", "抬头", "沉默", "转身", "笑了", "走到", "站在", "蹲下", "拿出", "递到", "攥紧", "推到", "握着"]


def normalize_name(name: str) -> str:
    name = (name or "").strip()
    name = CANONICAL_FIXES.get(name, name)
    name = ALIAS_TO_CANONICAL.get(name, name)
    return name


def _is_clean_name(name: str) -> bool:
    raw = (name or "").strip()
    name = normalize_name(raw)
    if not name:
        return False
    if raw in HARD_BAD_WORDS or name in HARD_BAD_WORDS:
        return False
    if name in KNOWN_CANONICAL:
        return True
    if name in ROLE_TITLES:
        return True
    if len(name) < 2 or len(name) > 3:
        return False
    if any(x in name for x in ["说", "问", "的", "了", "着", "过", "在", "把", "和", "是", "不", "这", "那", "地", "却"]):
        return False
    if any(x in name for x in ["短信", "照片", "钥匙", "仓库", "录音", "公司", "会议室", "顾问", "经理"]):
        return False
    # 非已知姓名必须看起来像中文姓名，避免“猛地/同时/轻轻”
    if name[-1] in "地时中里上下一二三四五六七八九十":
        return False
    return True


def _evidence_window(text: str, start: int, end: int, radius: int = 18) -> str:
    return text[max(0, start - radius): min(len(text), end + radius)].replace("\n", " ")


def extract_character_evidence(text: str) -> Dict[str, List[str]]:
    evidence: Dict[str, List[str]] = {}

    def add(name: str, ev: str):
        name = normalize_name(name)
        if not _is_clean_name(name):
            return
        evidence.setdefault(name, [])
        if ev and ev not in evidence[name]:
            evidence[name].append(ev[:80])

    # 1. 明确强角色名：必须真的出现在文本中。
    for name in KNOWN_CANONICAL:
        if name == "林建平":
            for alias in ["林建平", "父亲", "林夏父亲"]:
                for m in re.finditer(re.escape(alias), text):
                    add("林建平", _evidence_window(text, m.start(), m.end()))
        else:
            for m in re.finditer(re.escape(name), text):
                add(name, _evidence_window(text, m.start(), m.end()))

    # 2. 称谓型角色，但只保留完整称谓，不保留截断词。
    for title in ROLE_TITLES:
        for m in re.finditer(re.escape(title), text):
            add(title, _evidence_window(text, m.start(), m.end()))

    # 3. 对白冒号主体。只取冒号前 2-4 字，不从长句中倒截。
    for m in re.finditer(r"(?:^|[\n。！？])\s*([一-龥]{2,4})[：:]", text):
        add(m.group(1), _evidence_window(text, m.start(1), m.end(1)))

    # 4. 说话/动作主体：要求主体前方是句首或标点，避免“夏猛地/言同时”这种中间截词。
    verb_group = "|".join(map(re.escape, SPEECH_VERBS + ACTION_VERBS))
    pattern = re.compile(r"(?:^|[\n。！？；，,])\s*([一-龥]{2,4})(?:" + verb_group + r")")
    for m in pattern.finditer(text):
        add(m.group(1), _evidence_window(text, m.start(1), m.end(1)))

    # 清掉证据不足的非强角色
    cleaned = {}
    for name, evs in evidence.items():
        name = normalize_name(name)
        if name in KNOWN_CANONICAL or name in ROLE_TITLES:
            cleaned[name] = evs[:5]
        elif len(evs) >= 2:
            cleaned[name] = evs[:5]

    # 项目经理和经理只保留项目经理；父亲只合并进林建平
    if "经理" in cleaned:
        cleaned.pop("经理", None)
        cleaned.setdefault("项目经理", ["文本中出现项目经理称谓。"])
    cleaned.pop("父亲", None)

    return cleaned


def extract_character_names(text: str) -> List[str]:
    evidence = extract_character_evidence(text)
    # 固定顺序，减少输出跳动
    ordered = []
    for name in KNOWN_CANONICAL:
        if name in evidence and name not in ordered:
            ordered.append(name)
    for name in evidence:
        if name not in ordered:
            ordered.append(name)
    return ordered


def valid_names_from_memory(memory) -> List[str]:
    return [item.name for item in memory.characters if _is_clean_name(item.name)]


def normalize_character_list(characters: List[str], known_names: List[str]) -> List[str]:
    known_names = [normalize_name(name) for name in known_names if _is_clean_name(name)]
    result: List[str] = []

    for item in characters or []:
        name = normalize_name(item)

        # 修复截断名。
        if item == "目经理" and "项目经理" in known_names:
            name = "项目经理"
        if item == "父亲" and "林建平" in known_names:
            name = "林建平"

        if not _is_clean_name(name):
            continue
        if known_names and name not in known_names:
            continue
        if name not in result:
            result.append(name)

    return result


def normalize_speaker(speaker: str, scene_characters: List[str], known_names: List[str]) -> str:
    name = normalize_name(speaker)
    candidates = scene_characters or known_names

    if name in candidates:
        return name
    if speaker == "父亲" and "林建平" in candidates:
        return "林建平"
    if speaker == "目经理" and "项目经理" in candidates:
        return "项目经理"
    if candidates:
        return candidates[0]
    return name or "角色"


def invalid_character_reasons(names: List[str]) -> Dict[str, str]:
    reasons = {}
    for name in names:
        fixed = normalize_name(name)
        if not fixed:
            reasons[name] = "明显不是人物或为错误截词"
        elif name in HARD_BAD_WORDS or fixed in HARD_BAD_WORDS:
            reasons[name] = "命中非人物词黑名单"
        elif not _is_clean_name(name):
            reasons[name] = "不符合人物名规则"
    return reasons
