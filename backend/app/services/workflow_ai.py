from app.models.schemas import ConvertResult, NovelInput
from app.services.final_result_guard import enforce_final_result
from app.services.runtime_metadata import attach_runtime_metadata
from app.services.input_guard import validate_source_novel_text
from app.services.chapter_parser import split_chapters
from app.services.knowledge_engine import build_knowledge_trace, retrieve_rules_for_story, warmup_knowledge_base
from app.services.validation_engine import build_validation_report, validate_script
from app.services.character_guard import sanitize_analysis, sanitize_memory, sanitize_scenes
from app.services.memory_store import build_memory
from app.services.novel_analyzer import analyze_novel
from app.services.requirement_parser import parse_requirement
from app.services.deepseek_writer import generate_scenes_with_deepseek
from app.services.schema_guard import clean_scene_placeholders, normalize_scene_characters, validate_scenes
from app.services.report_generator import generate_quality_report
from app.services.schema_validator import validate_yaml_text
from app.services.scene_quality_guard import enforce_chapter_bound_scenes, force_chapter_bound_final_scenes, repair_scenes_by_chapter
from app.services.yaml_generator import dump_script_yaml


async def convert_ai(payload: NovelInput) -> ConvertResult:
    source_ok, source_message = validate_source_novel_text(payload.text)
    if not source_ok:
        raise ValueError(source_message)

    chapters = split_chapters(payload.text)
    memory = build_memory(chapters)
    memory, memory_warnings = sanitize_memory(memory, payload.text)
    analysis = await analyze_novel(chapters, memory)
    analysis = sanitize_analysis(analysis, memory)
    requirement_plan = parse_requirement(payload.user_instruction, analysis)

    warmup_info = warmup_knowledge_base()
    used_rules, retrieval_queries = retrieve_rules_for_story(analysis, requirement_plan)

    scenes, accuracy_trace = await generate_scenes_with_deepseek(
        chapters=chapters,
        memory=memory,
        analysis=analysis,
        requirement_plan=requirement_plan,
        used_rules=used_rules,
    )

    first_knowledge_trace = build_knowledge_trace(warmup_info, retrieval_queries, used_rules, scenes)
    first_pass_issues = validate_script(chapters, memory, scenes, requirement_plan, first_knowledge_trace)

    scenes = clean_scene_placeholders(scenes)
    scenes, repair_warnings = repair_scenes_by_chapter(chapters, memory, analysis, requirement_plan, scenes)
    scenes = normalize_scene_characters(memory, scenes)
    scenes, character_warnings = sanitize_scenes(memory, scenes)
    scenes, enforce_warnings = enforce_chapter_bound_scenes(chapters, memory, analysis, requirement_plan, scenes)
    scenes = normalize_scene_characters(memory, scenes)

    final_rebuild_warnings = []
    final_character_warnings = []

    knowledge_trace = build_knowledge_trace(warmup_info, retrieval_queries, used_rules, scenes)

    scene_valid, scene_warnings = validate_scenes(memory, scenes)
    scene_warnings = list(dict.fromkeys(memory_warnings + repair_warnings + character_warnings + enforce_warnings + final_rebuild_warnings + final_character_warnings + scene_warnings))
    final_issues = validate_script(chapters, memory, scenes, requirement_plan, knowledge_trace)

    draft_report = generate_quality_report(memory, scenes, scene_valid and not final_issues, scene_warnings + [issue.message for issue in final_issues])
    yaml_text = dump_script_yaml(payload.title, len(chapters), memory, scenes, draft_report, analysis, requirement_plan, knowledge_trace, None)

    yaml_valid, yaml_warnings = validate_yaml_text(yaml_text)
    all_warnings = scene_warnings + yaml_warnings + [issue.message for issue in final_issues]
    report = generate_quality_report(memory, scenes, yaml_valid and scene_valid and not final_issues, all_warnings)

    validation_report = build_validation_report(
        first_pass=first_pass_issues,
        repair_log=repair_warnings + character_warnings + enforce_warnings + final_rebuild_warnings + final_character_warnings,
        final_issues=final_issues,
    )

    yaml_text = dump_script_yaml(payload.title, len(chapters), memory, scenes, report, analysis, requirement_plan, knowledge_trace, validation_report)

    result = ConvertResult(
        title=payload.title,
        chapters=chapters,
        analysis=analysis,
        requirement_plan=requirement_plan,
        memory=memory,
        used_rules=used_rules,
        scenes=scenes,
        yaml_text=yaml_text,
        quality_report=report,
        knowledge_trace=knowledge_trace,
        validation_report=validation_report,
        story_bible=accuracy_trace.get("story_bible", {}),
        chapter_facts=accuracy_trace.get("chapter_facts", []),
        repair_questions=accuracy_trace.get("repair_questions", []),
        model_trace=accuracy_trace.get("model_trace", {}),
    )
    model_status = f'chat={accuracy_trace.get("model_trace", {}).get("chat_model", "-")}; pro={accuracy_trace.get("model_trace", {}).get("pro_model", "-")}'
    result = attach_runtime_metadata(result, payload.text, model_status=model_status)
    return enforce_final_result(result)
