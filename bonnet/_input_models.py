"""Input Pydantic models for domain functions."""

from typing import Optional
from pydantic import BaseModel


class GetEntityContextInput(BaseModel):
    e_id: str


class SearchInput(BaseModel):
    query: str
    include_related: bool = True
    max_depth: int = 1


class StoreEntityInput(BaseModel):
    e_id: str
    name: str


class StoreAttributeInput(BaseModel):
    attr_id: str
    attr_type: str
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
    file_id: str
    file_path: str
    description: Optional[str] = None


class LinkInput(BaseModel):
    from_type: str  # 'entity', 'file', 'attribute'
    from_id: str
    to_type: str    # 'entity', 'file', 'attribute'
    to_id: str
    edge_type: str = "references"
    content: Optional[str] = None

