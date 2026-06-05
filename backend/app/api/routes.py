from fastapi import APIRouter

from app.models.schemas import ProjectStatus, WorkflowPreview, WorkflowStep


router = APIRouter()


@router.get("/status", response_model=ProjectStatus)
def get_project_status():
    return ProjectStatus(
        name="Novel2Script AI",
        stage="backend initialization",
        selected_topic="AI 小说转剧本工具",
        description="A multi-stage AI workflow for converting novels into structured YAML scripts.",
    )


@router.get("/workflow-preview", response_model=WorkflowPreview)
def get_workflow_preview():
    steps = [
        WorkflowStep(
            id="input_parser",
            name="小说输入解析",
            description="识别章节边界，并检查输入是否满足三个章节以上。",
            status="planned",
        ),
        WorkflowStep(
            id="memory_builder",
            name="小说事实记忆库",
            description="抽取角色、事件、场景、伏笔和时间线，降低长文本信息丢失。",
            status="planned",
        ),
        WorkflowStep(
            id="script_agent",
            name="剧本专家 Agent",
            description="根据事实记忆和剧作规则生成结构化剧本。",
            status="planned",
        ),
        WorkflowStep(
            id="yaml_validator",
            name="YAML Schema 校验",
            description="检查输出字段、格式和来源追溯信息。",
            status="planned",
        ),
        WorkflowStep(
            id="repair_agent",
            name="自动修复与准确性报告",
            description="修复格式错误，并生成事件覆盖率、角色一致性等报告。",
            status="planned",
        ),
    ]

    return WorkflowPreview(
        project="Novel2Script AI",
        steps=steps,
    )