from typing import Dict, List

from app.models.schemas import Chapter, EventMemory, NovelAnalysis, NovelMemory, RequirementPlan, ScriptScene
from app.services.time_format_engine import classify_scene_time


PROP_WORDS = ["匿名信", "信封", "照片", "旧钥匙", "钥匙", "录音笔", "录音", "旧手机", "短信", "仓库", "保险箱", "西港 17 号"]


def _contains(text: str, words: List[str]) -> bool:
    return any(word in text for word in words)


def _props_in_chapter(text: str, analysis: NovelAnalysis) -> List[str]:
    candidates = list(dict.fromkeys(list(analysis.key_props) + PROP_WORDS))
    props = []
    for item in candidates:
        if item in text and item not in props:
            props.append(item)
    # 避免“旧钥匙”和“钥匙”重复堆叠；保留更具体的道具。
    if "旧钥匙" in props and "钥匙" in props:
        props.remove("钥匙")
    if "录音笔" in props and "录音" in props:
        # 录音可作为信息，不直接当道具重复显示。
        pass
    return props


def _location_time(chapter: Chapter) -> Dict[str, str]:
    text = chapter.text

    if "会议室" in text or "公司" in text or "技术顾问" in text:
        location = "公司会议室 / 走廊"
    elif "仓库" in text or "西港" in text or "保险箱" in text:
        location = "西港十七号仓库"
    elif "旧楼" in text or "楼道" in text or "三楼" in text:
        location = "旧楼三楼走廊"
    else:
        location = "主要场景"

    return {
        "location": location,
        "time": classify_scene_time(text, location),
    }


def _title_for(chapter: Chapter, index: int) -> str:
    text = chapter.text
    if "旧楼" in text and ("信封" in text or "匿名信" in text or "照片" in text):
        return "雨夜旧楼"
    if "会议室" in text or "技术顾问" in text or "重逢" in chapter.title:
        return "会议室重逢"
    if "仓库" in text or "西港" in text:
        return "西港仓库"
    return f"{chapter.title} 分场"


def _characters_for_chapter(chapter: Chapter, memory: NovelMemory) -> List[str]:
    text = chapter.text
    known = [item.name for item in memory.characters]
    names = [name for name in known if name in text]

    # 父亲/林建平以录音出现，不作为现场人物；保留在 notes。
    if "林建平" in names and ("录音" in text or "录音笔" in text):
        names.remove("林建平")

    # 项目经理只有在本章实际出现才进入人物。
    if "项目经理" in known and "项目经理" in text and "项目经理" not in names:
        names.append("项目经理")

    if not names:
        names = [name for name in ["林夏", "顾言"] if name in known]

    return names[:4]


def _conflict_for(chapter: Chapter) -> str:
    text = chapter.text
    if "别再相信顾言" in text or "信封" in text or "照片" in text:
        return "林夏收到指向顾言的匿名线索，顾言突然出现，信任被再次撕开。"
    if "会议室" in text or "技术顾问" in text:
        return "顾言以技术顾问身份重回林夏身边，林夏逼问三年前的隐瞒。"
    if "仓库" in text or "录音笔" in text or "保险箱" in text:
        return "林夏和顾言打开仓库证据，父亲录音改写旧案判断，项目经理现身制造反转。"
    if "短信" in text:
        return "陌生短信推动人物进入新的追查节点。"
    return "人物围绕关键信息发生冲突。"


def _purpose_for(chapter: Chapter) -> str:
    text = chapter.text
    if "信封" in text or "照片" in text:
        return "用匿名信和照片重新打开三年前旧案，并让林夏与顾言被迫重逢。"
    if "会议室" in text:
        return "把私人旧怨转入公开工作场景，让林夏和顾言的关系进入正面冲突。"
    if "仓库" in text or "录音笔" in text:
        return "让旧钥匙、保险箱和录音笔集中兑现伏笔，并引出项目经理反转。"
    return f"将{chapter.title}的关键事件转化为可表演场景。"


def _actions_for(chapter: Chapter, characters: List[str], props: List[str], requirement_plan: RequirementPlan) -> List[str]:
    text = chapter.text
    actions: List[str] = []

    if "旧楼" in text:
        actions.extend([
            "雨水沿着旧楼台阶流下，林夏停在三楼门口，发现被塑料袋包住的牛皮纸信封。",
            "她拆开信封，照片背面的日期把三年前父亲失踪的夜晚重新拉回眼前。",
            "楼梯口传来脚步声，顾言带着雨水出现在黑暗里，两人的距离被照片和旧案隔开。",
        ])
    elif "会议室" in text or "技术顾问" in text:
        actions.extend([
            "会议室里，项目经理介绍新来的技术顾问，林夏在众人面前认出顾言。",
            "会议结束后，林夏压低声音追问三年前的消失，顾言拿出手机短信作为反证。",
            "手机再次震动，新的短信把线索指向旧仓库，也把两人的对峙推向下一步。",
        ])
    elif "仓库" in text or "西港" in text:
        actions.extend([
            "深夜的西港仓库外，林夏用旧钥匙打开锈锁，铁门发出刺耳声响。",
            "仓库角落的保险箱被打开，旧手机和录音笔露出，父亲的声音从杂音中传出。",
            "录音指出顾言的隐瞒另有原因，林夏刚抬头，项目经理便拿着另一把钥匙从货架后出现。",
        ])
    else:
        names = "、".join(characters[:2]) if characters else "人物"
        actions.extend([
            f"{names}进入场景，围绕本章关键线索展开行动。",
            "道具或空间变化推动信息揭露，场尾留下下一场钩子。",
        ])

    if props:
        actions.append(f"本场重点保留道具：{'、'.join(props[:4])}。")

    if chapter.order in requirement_plan.focus_chapters or any(k in text for k in requirement_plan.focus_keywords):
        actions.append("按用户要求加强本场细节，但不新增无关角色，不改变核心真相。")

    return actions


def _dialogue_for(chapter: Chapter, characters: List[str]) -> List[Dict[str, str]]:
    text = chapter.text
    linxia = "林夏"
    guyan = "顾言"

    if "旧楼" in text or "信封" in text:
        return [
            {"speaker": linxia, "line": "你怎么会在这里？", "emotion": "警惕", "subtext": "她怀疑顾言和匿名信有关。"},
            {"speaker": guyan, "line": "那封信不是我放的。", "emotion": "克制", "subtext": "他急于否认，却没有说出全部真相。"},
            {"speaker": linxia, "line": "那你为什么会来？", "emotion": "压抑", "subtext": "她逼他给出合理解释。"},
            {"speaker": guyan, "line": "因为我也收到了短信。", "emotion": "沉重", "subtext": "两人都被同一个人引回旧楼。"},
        ]
    if "会议室" in text or "技术顾问" in text:
        return [
            {"speaker": linxia, "line": "三年前我也需要一个解释，你给了吗？", "emotion": "克制", "subtext": "她把工作场景下的平静当作防线。"},
            {"speaker": guyan, "line": "我以为不告诉你，你就能安全。", "emotion": "愧疚", "subtext": "他承认隐瞒，但仍试图证明动机。"},
            {"speaker": linxia, "line": "你凭什么替我决定？", "emotion": "受伤", "subtext": "她真正愤怒的是被排除在真相之外。"},
        ]
    if "仓库" in text or "录音笔" in text:
        return [
            {"speaker": linxia, "line": "这把钥匙能打开这里，说明当年的事从来没结束。", "emotion": "坚定", "subtext": "她决定直面真相。"},
            {"speaker": guyan, "line": "进去以后，你可能不会再相信任何人。", "emotion": "沉重", "subtext": "他知道录音会改变她的判断。"},
            {"speaker": "项目经理" if "项目经理" in characters else characters[-1], "line": "录音还是被你们找到了。", "emotion": "冷静", "subtext": "真正的操盘者现身。"},
        ]
    speaker = characters[0] if characters else "角色"
    return [{"speaker": speaker, "line": "我需要知道真相。", "emotion": "克制", "subtext": "推动本场冲突。"}]


def build_scene_from_chapter(
    chapter: Chapter,
    event: EventMemory,
    memory: NovelMemory,
    analysis: NovelAnalysis,
    requirement_plan: RequirementPlan,
) -> ScriptScene:
    meta = _location_time(chapter)
    characters = _characters_for_chapter(chapter, memory)
    props = _props_in_chapter(chapter.text, analysis)

    notes = "根据对应章节事实生成。"
    if "录音" in chapter.text or "录音笔" in chapter.text:
        notes += " 林建平通过录音出现，不作为现场出场人物。"

    return ScriptScene(
        id=f"scene_{chapter.order:03d}",
        title=_title_for(chapter, chapter.order),
        source_chapter=chapter.order,
        source_events=[event.id] if event else [],
        location=meta["location"],
        time=meta["time"],
        characters=characters,
        conflict=_conflict_for(chapter),
        purpose=_purpose_for(chapter),
        action=_actions_for(chapter, characters, props, requirement_plan),
        dialogue=[d for d in _dialogue_for(chapter, characters) if d["speaker"] in characters],
        notes=notes,
    )
