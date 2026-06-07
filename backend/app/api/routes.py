from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ConvertResult,
    NovelInput,
    ParseResult,
    ProjectStatus,
    RuleSearchResult,
    WorkflowPreview,
    WorkflowStep,
    ScriptRevisionRequest,
    ScriptRevisionResult,
)
from app.services.memory_store import build_memory
from app.services.rule_retriever import search_rules, summarize_rules
from app.services.workflow import convert_demo, parse_novel_input
from app.services.workflow_ai import convert_ai
from app.services.job_manager import create_job, get_job, get_result
from app.services.output_gate import OutputQualityError, assert_final_payload_is_clean, finalize_result_payload
from app.services.script_reviser import revise_script_result
from app.version import APP_VERSION
from app.services.debug_status import get_runtime_status


router = APIRouter()


@router.get("/status", response_model=ProjectStatus)
def get_project_status():
    return ProjectStatus(
        name="Novel2Script AI",
        stage="backend technical implementation",
        selected_topic="AI 小说转剧本工具",
        description="A multi-stage AI workflow for converting Chinese novels into structured YAML scripts.",
    )


@router.get("/workflow-preview", response_model=WorkflowPreview)
def get_workflow_preview():
    steps = [
        WorkflowStep(
            id="input_parser",
            name="小说输入解析",
            description="识别章节边界，并检查输入是否满足三个章节以上。",
            status="ready",
        ),
        WorkflowStep(
            id="memory_builder",
            name="小说事实记忆库",
            description="抽取角色、事件、关系、伏笔和时间线。",
            status="ready",
        ),
        WorkflowStep(
            id="rule_retriever",
            name="剧本知识库检索",
            description="按任务检索剧本基础、短剧节奏、对白和导演视角规则。",
            status="ready",
        ),
        WorkflowStep(
            id="script_agent",
            name="剧本专家 Agent",
            description="生成结构化分场剧本。",
            status="draft",
        ),
        WorkflowStep(
            id="script_doctor",
            name="剧本医生 Agent",
            description="优化对白、动作、潜台词和场尾钩子。",
            status="draft",
        ),
        WorkflowStep(
            id="yaml_validator",
            name="YAML Schema 校验",
            description="检查输出字段、格式和来源追溯信息。",
            status="ready",
        ),
        WorkflowStep(
            id="report_generator",
            name="准确性报告",
            description="生成事件覆盖率、角色一致性、伏笔保留率和格式合规结果。",
            status="ready",
        ),
    ]

    return WorkflowPreview(
        project="Novel2Script AI",
        steps=steps,
    )


@router.get("/rules/summary")
def rules_summary():
    return summarize_rules()


@router.get("/rules/search", response_model=RuleSearchResult)
def rules_search(
    query: str = Query(default=""),
    module: Optional[str] = Query(default=None),
    limit: int = Query(default=12, ge=1, le=50),
):
    rules = search_rules(query=query, module=module, limit=limit)
    return RuleSearchResult(
        query=query,
        module=module,
        count=len(rules),
        rules=rules,
    )


@router.post("/parse-chapters", response_model=ParseResult)
def parse_chapters(payload: NovelInput):
    return parse_novel_input(payload)


@router.post("/build-memory")
def build_memory_endpoint(payload: NovelInput):
    parsed = parse_novel_input(payload)
    memory = build_memory(parsed.chapters)
    return {
        "chapter_count": parsed.chapter_count,
        "valid": parsed.valid,
        "message": parsed.message,
        "memory": memory,
    }


@router.post("/convert-demo", response_model=ConvertResult)
def convert_to_script_demo(payload: NovelInput):
    return convert_demo(payload)


@router.post("/revise-script", response_model=ScriptRevisionResult)
def revise_script(payload: ScriptRevisionRequest):
    revised = revise_script_result(payload.result, payload.instruction)
    return ScriptRevisionResult(
        result=revised,
        message="已根据修改要求更新剧本。"
    )


@router.post("/convert-ai")
async def convert_to_script_ai(payload: NovelInput):
    try:
        result = await convert_ai(payload)
        return assert_final_payload_is_clean(finalize_result_payload(result))
    except OutputQualityError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/schema")
def get_yaml_schema():
    return {
        "metadata": {
            "title": "string",
            "source_chapters": "number",
            "adaptation_style": "string",
            "genre": "string",
            "language": "zh-CN"
        },
        "analysis": "NovelAnalysis",
        "requirement_plan": "RequirementPlan",
        "characters": "CharacterMemory[]",
        "memory": {
            "timeline": "event_id[]",
            "foreshadows": "ForeshadowMemory[]",
            "unresolved_conflicts": "EventMemory[]"
        },
        "scenes": "ScriptScene[]",
        "quality_report": "QualityReport"
    }


@router.post("/convert-ai/start")
async def start_convert_ai_job(payload: NovelInput):
    job_id = create_job(payload)
    return {"job_id": job_id}


@router.get("/jobs/{job_id}/status")
def get_convert_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"status": "not_found", "job_id": job_id}
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "stage": job["stage"],
        "stage_text": job["stage_text"],
        "progress": job["progress"],
        "elapsed_seconds": job["elapsed_seconds"],
        "error": job["error"],
    }


@router.get("/jobs/{job_id}/result")
def get_convert_job_result(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"status": "not_found", "job_id": job_id}
    if job["status"] != "done":
        return {"status": job["status"], "job_id": job_id, "error": job.get("error")}
    result = get_result(job_id)
    if not result:
        return {"status": "error", "job_id": job_id, "error": "结果不存在或未通过校验。"}
    try:
        return assert_final_payload_is_clean(finalize_result_payload(result))
    except OutputQualityError as exc:
        return {"status": "quality_failed", "job_id": job_id, "error": str(exc)}

@router.get("/version")
def get_version():
    return {"version": APP_VERSION}


@router.get("/debug/runtime")
def debug_runtime():
    return get_runtime_status()
