"""Input Pydantic models for domain functions."""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class GetEntityContextInput(BaseModel):
    e_id: str


class SearchInput(BaseModel):
    query: str
    include_related: bool = True
    max_depth: int = 1


class StoreEntityInput(BaseModel):
    e_id: Optional[str] = None
    name: str
    short_name: Optional[str] = None


class StoreAttributeInput(BaseModel):
    attr_id: str
    attr_type: Literal["FACT", "REF", "TASK", "RULE"] = Field(..., description="Attribute type must be one of: FACT, REF, TASK, RULE")
    subject: str
    detail: str


class CreateEdgeInput(BaseModel):
    from_node_id: str
    to_node_id: str
    edge_type: str
    searchable_content: Optional[str] = None


class SearchEntitiesInput(BaseModel):
    query: str


class StoreFileInput(BaseModel):
    file_id: Optional[str] = None
    file_path: str
    description: Optional[str] = None
    content: Optional[str] = None
    include_content: bool = False


class StoreSnippetInput(BaseModel):
    snippet_id: Optional[str] = None
    file_path: str


class LinkInput(BaseModel):
    from_type: str  # 'entity', 'file', 'attribute'
    from_id: str
    to_type: str    # 'entity', 'file', 'attribute'
    to_id: str
    edge_type: str = "references"
    content: Optional[str] = None

