from pydantic import BaseModel, Field


class JobGraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    sample_count: int = 0
    top_skills: list[str] = Field(default_factory=list)
    top_cities: list[str] = Field(default_factory=list)


class JobGraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str
    weight: float = 0
    reason: str = ''


class JobGraph(BaseModel):
    nodes: list[JobGraphNode] = Field(default_factory=list)
    edges: list[JobGraphEdge] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
