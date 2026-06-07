import json
import re
from typing import List

from app.models.schemas import Chapter, NovelAnalysis, NovelMemory
from app.services.ai_client import AIClient


def _text_of(chapters: List[Chapter], limit: int = 5000) -> str:
    return "\n\n".join(f"{c.title}\n{c.text}" for c in chapters)[:limit]


def _unique(items):
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def heuristic_analyze(chapters: List[Chapter], memory: NovelMemory) -> NovelAnalysis:
    text = _text_of(chapters, 8000)
    genre = "都市悬疑 / 情感悬疑"
    if any(k in text for k in ["仙门", "灵力", "修为", "妖", "魔"]):
        genre = "玄幻 / 仙侠"
    elif any(k in text for k in ["校园", "老师", "同桌", "教室"]):
        genre = "校园 / 青春"
    elif any(k in text for k in ["案件", "警察", "尸体", "凶手"]):
        genre = "悬疑 / 犯罪"

    direction = "短剧式影视剧本" if any(k in text for k in ["短信", "匿名信", "钥匙", "录音", "仓库", "真相"]) else "影视分场剧本"

    key_props = []
    for word in ["匿名信", "信封", "照片", "旧钥匙", "钥匙", "录音笔", "录音", "旧手机", "短信", "仓库"]:
        if word in text:
            key_props.append(word)

    must_preserve = _unique([
        item.description.replace(" 出现", "：出现") for item in memory.foreshadows[:8]
    ])
    avoid = ["新增无关主角", "改变核心真相", "删除关键伏笔", "过度煽情", "让对白只解释剧情"]

    main_characters = [c.name for c in memory.characters if c.name != "核心人物"]

    return NovelAnalysis(
        genre=genre,
        adaptation_direction=direction,
        logline="主人公被一条线索引回旧事现场，在重逢和追查中逼近被隐瞒的真相。",
        core_conflict="人物想查明真相，但过往隐瞒、误会和危险线索不断阻碍推进。",
        tone="克制、悬疑、带情绪张力",
        main_characters=main_characters,
        key_props=_unique(key_props),
        must_preserve=must_preserve,
        avoid=avoid,
    )


async def analyze_novel(chapters: List[Chapter], memory: NovelMemory) -> NovelAnalysis:
    client = AIClient()
    fallback = heuristic_analyze(chapters, memory)
    if client.provider == "mock" or not client.api_key:
        return fallback

    prompt = {
        "task": "分析中文小说，返回 JSON，不要解释。",
        "schema": {
            "genre": "题材类型",
            "adaptation_direction": "适合改编方向",
            "logline": "一句话梗概",
            "core_conflict": "核心冲突",
            "tone": "整体气质",
            "main_characters": ["人物名"],
            "key_props": ["关键道具"],
            "must_preserve": ["必须保留的伏笔或事实"],
            "avoid": ["改编时需要避免的事"]
        },
        "novel": _text_of(chapters, 7000),
        "known_characters": [c.name for c in memory.characters],
        "known_foreshadows": [f.description for f in memory.foreshadows],
    }

    try:
        response = await client.chat_json([
            {"role": "system", "content": "你是中文小说改编剧本分析师。只输出 JSON。"},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ])
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        data = json.loads(content) if isinstance(content, str) else content
        return NovelAnalysis(**{**fallback.model_dump(), **data})
    except Exception:
        return fallback


def clean_analysis_characters(analysis: NovelAnalysis, memory: NovelMemory) -> NovelAnalysis:
    allowed = [c.name for c in memory.characters if c.name != "核心人物"]
    analysis.main_characters = [name for name in allowed if name in ["林夏", "顾言", "林建平", "项目经理"]] or allowed
    return analysis
