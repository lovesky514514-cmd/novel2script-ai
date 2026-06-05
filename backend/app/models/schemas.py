from pydantic import BaseModel
from typing import List


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