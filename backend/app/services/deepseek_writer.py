from typing import List, Tuple, Dict, Any

from app.models.schemas import Chapter, KnowledgeRule, NovelAnalysis, NovelMemory, RequirementPlan, ScriptScene
from app.services.accuracy_pipeline import generate_scenes_accuracy_pipeline


async def generate_scenes_with_deepseek(
    chapters: List[Chapter],
    memory: NovelMemory,
    analysis: NovelAnalysis,
    requirement_plan: RequirementPlan,
    used_rules: List[KnowledgeRule],
) -> Tuple[List[ScriptScene], Dict[str, Any]]:
    return await generate_scenes_accuracy_pipeline(chapters, memory, analysis, requirement_plan, used_rules)
