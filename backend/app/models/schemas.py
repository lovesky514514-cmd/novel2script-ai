from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    id: str
    name: str
    description: str
    status: str = "pending"


class ProjectStatus(BaseModel):
    name: str
    stage: str
    selected_topic: str
    description: str


class WorkflowPreview(BaseModel):
    project: str
    steps: List[WorkflowStep]


class NovelInput(BaseModel):
    title: str = Field(default="Untitled Novel")
    text: str
    adaptation_style: str = Field(default="auto")
    user_instruction: str = Field(default="")


class Chapter(BaseModel):
    id: str
    title: str
    order: int
    text: str
    word_count: int


class ParseResult(BaseModel):
    valid: bool
    chapter_count: int
    message: str
    chapters: List[Chapter]


class NovelAnalysis(BaseModel):
    genre: str = ""
    adaptation_direction: str = ""
    logline: str = ""
    core_conflict: str = ""
    tone: str = ""
    main_characters: List[str] = []
    key_props: List[str] = []
    must_preserve: List[str] = []
    avoid: List[str] = []


class RequirementPlan(BaseModel):
    raw_instruction: str = ""
    focus_chapters: List[int] = []
    focus_keywords: List[str] = []
    expand_level: str = "normal"
    max_new_scenes: int = 0
    max_expansion_ratio: float = 1.0
    style_constraints: Dict[str, str] = {}
    preserve: List[str] = []
    avoid: List[str] = []


class CharacterMemory(BaseModel):
    id: str
    name: str
    role: str = "角色"
    traits: List[str] = []
    motivation: str = ""
    first_seen: str = ""
    current_state: str = ""


class RelationshipMemory(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    evidence: str = ""


class EventMemory(BaseModel):
    id: str
    chapter_id: str
    summary: str
    characters: List[str] = []
    location: str = ""
    conflict: str = ""
    consequence: str = ""


class ForeshadowMemory(BaseModel):
    id: str
    chapter_id: str
    description: str
    status: str = "unresolved"
    importance: int = 3


class NovelMemory(BaseModel):
    characters: List[CharacterMemory]
    relationships: List[RelationshipMemory]
    events: List[EventMemory]
    foreshadows: List[ForeshadowMemory]
    timeline: List[str]


class KnowledgeRule(BaseModel):
    id: str
    category: str
    title: str
    rule: str
    apply_when: List[str]
    check_points: List[str] = []
    example_before: str = ""
    example_after: str = ""
    source_note: str = ""


class RuleSearchResult(BaseModel):
    query: str
    module: Optional[str] = None
    count: int
    rules: List[KnowledgeRule]


class AppliedRuleTrace(BaseModel):
    rule_id: str
    title: str
    applied_to: List[str] = []
    effect: str = ""


class KnowledgeTrace(BaseModel):
    warmup: Dict[str, Any] = {}
    retrieval_query: List[str] = []
    used_rules: List[Dict[str, Any]] = []
    applied_rules: List[AppliedRuleTrace] = []
    cold_start_ms: int = 0


class ValidationIssue(BaseModel):
    level: str = "warning"
    code: str
    target: str = ""
    message: str


class ValidationReport(BaseModel):
    first_pass_issues: List[ValidationIssue] = []
    repair_log: List[str] = []
    final_issues: List[ValidationIssue] = []
    final_status: str = "pass"
    pass_count: int = 2


class ScriptScene(BaseModel):
    id: str
    title: str
    source_chapter: int
    source_events: List[str]
    location: str
    time: str
    characters: List[str]
    conflict: str
    purpose: str
    action: List[str]
    dialogue: List[Dict[str, Any]]
    notes: str = ""


class QualityReport(BaseModel):
    event_coverage: float
    character_consistency: float
    foreshadow_retention: float
    format_valid: bool
    warnings: List[str]
    suggestions: List[str]


class ConvertResult(BaseModel):
    title: str
    chapters: List[Chapter]
    analysis: Optional[NovelAnalysis] = None
    requirement_plan: Optional[RequirementPlan] = None
    memory: NovelMemory
    used_rules: List[KnowledgeRule]
    scenes: List[ScriptScene]
    yaml_text: str
    quality_report: QualityReport
    knowledge_trace: Optional[KnowledgeTrace] = None
    validation_report: Optional[ValidationReport] = None
    run_id: Optional[str] = None
    generated_at: Optional[str] = None
    model_status: Optional[str] = None
    input_hash: Optional[str] = None
    guard_mode: Optional[str] = None
    story_bible: Optional[Dict[str, Any]] = None
    chapter_facts: List[Dict[str, Any]] = []
    repair_questions: List[Dict[str, Any]] = []
    model_trace: Dict[str, Any] = {}


class ScriptRevisionRequest(BaseModel):
    result: ConvertResult
    instruction: str


class ScriptRevisionResult(BaseModel):
    result: ConvertResult
    message: str
