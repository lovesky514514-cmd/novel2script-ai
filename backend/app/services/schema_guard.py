from typing import List, Tuple

from app.models.schemas import NovelMemory, ScriptScene
from app.services.character_extractor import invalid_character_reasons, normalize_character_list, normalize_speaker

BANNED_WORDS = ["Demo 模式", "待剧本专家", "待更新", "unknown", "待识别", "AI 模式下"]
INVALID_CHARACTER_TOKENS = ["目经理", "技术顾", "一句地", "他却只", "夏猛地", "言同时", "人轻轻", "短信", "照片", "钥匙", "没有", "冷冷地"]


def normalize_scene_characters(memory: NovelMemory, scenes: List[ScriptScene]) -> List[ScriptScene]:
    known_names = [item.name for item in memory.characters if item.name != "核心人物"]
    for scene in scenes:
        scene.characters = normalize_character_list(scene.characters, known_names)
        if not scene.characters and known_names:
            scene.characters = [name for name in ["林夏", "顾言"] if name in known_names] or known_names[:2]
        for item in scene.dialogue or []:
            item["speaker"] = normalize_speaker(item.get("speaker", ""), scene.characters, known_names)
    return scenes


def validate_scenes(memory: NovelMemory, scenes: List[ScriptScene]) -> Tuple[bool, List[str]]:
    warnings: List[str] = []
    known_characters = {item.name for item in memory.characters}
    for index, scene in enumerate(scenes, start=1):
        if scene.id != f"scene_{index:03d}":
            warnings.append(f"{scene.id}: scene id is not sequential.")
        if not scene.characters:
            warnings.append(f"{scene.id}: characters is empty.")
        if not scene.action:
            warnings.append(f"{scene.id}: action is empty.")
        if not scene.dialogue:
            warnings.append(f"{scene.id}: dialogue is empty.")
        for char in scene.characters:
            if char not in known_characters and char != "核心人物":
                warnings.append(f"{scene.id}: character {char} not found in memory.")
            if char in INVALID_CHARACTER_TOKENS:
                warnings.append(f"{scene.id}: invalid character token found: {char}")
        joined = " ".join([scene.title, scene.location, scene.time, scene.conflict, scene.purpose, scene.notes, " ".join(scene.action)])
        for word in BANNED_WORDS:
            if word in joined:
                warnings.append(f"{scene.id}: banned placeholder word found: {word}")
        for item in scene.dialogue:
            speaker = item.get("speaker", "")
            if speaker and speaker not in scene.characters:
                warnings.append(f"{scene.id}: speaker {speaker} not in scene characters.")
    return len(warnings) == 0, warnings


def clean_scene_placeholders(scenes: List[ScriptScene]) -> List[ScriptScene]:
    for scene in scenes:
        for word in BANNED_WORDS:
            scene.title = scene.title.replace(word, "")
            scene.location = scene.location.replace(word, "-")
            scene.time = scene.time.replace(word, "-")
            scene.conflict = scene.conflict.replace(word, "-")
            scene.purpose = scene.purpose.replace(word, "-")
            scene.notes = scene.notes.replace(word, "")
        scene.action = [line for line in scene.action if not any(word in line for word in BANNED_WORDS)]
        if not scene.action:
            scene.action = ["-"]
        if not scene.dialogue:
            speaker = scene.characters[0] if scene.characters else "角色"
            scene.dialogue = [{"speaker": speaker or "-", "line": "-", "emotion": "-", "subtext": "-"}]
    return scenes
