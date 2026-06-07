from app.models.schemas import ConvertResult, NovelInput, ParseResult
from app.services.chapter_parser import split_chapters, validate_min_chapters
from app.services.memory_store import build_memory
from app.services.report_generator import generate_quality_report
from app.services.rule_retriever import search_rules
from app.services.schema_validator import validate_yaml_text
from app.services.script_agent import generate_demo_scenes
from app.services.script_doctor import polish_scenes
from app.services.yaml_generator import dump_script_yaml


def parse_novel_input(payload: NovelInput) -> ParseResult:
    chapters = split_chapters(payload.text)
    valid, message = validate_min_chapters(chapters)
    return ParseResult(
        valid=valid,
        chapter_count=len(chapters),
        message=message,
        chapters=chapters,
    )


def build_novel_memory(payload: NovelInput):
    chapters = split_chapters(payload.text)
    return build_memory(chapters)


def convert_demo(payload: NovelInput) -> ConvertResult:
    chapters = split_chapters(payload.text)
    memory = build_memory(chapters)

    used_rules = search_rules(query="小说 改编 场景 对白 钩子", limit=18)
    scenes = generate_demo_scenes(chapters, memory)
    scenes = polish_scenes(scenes)

    draft_report = generate_quality_report(memory, scenes, True, [])
    yaml_text = dump_script_yaml(payload.title, len(chapters), memory, scenes, draft_report)

    format_valid, format_warnings = validate_yaml_text(yaml_text)
    report = generate_quality_report(memory, scenes, format_valid, format_warnings)
    yaml_text = dump_script_yaml(payload.title, len(chapters), memory, scenes, report)

    return ConvertResult(
        title=payload.title,
        chapters=chapters,
        memory=memory,
        used_rules=used_rules,
        scenes=scenes,
        yaml_text=yaml_text,
        quality_report=report,
    )
