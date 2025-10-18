from typing import List, Union, Optional, Dict, Any

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    id: str
    type: str
    subject: str
    detail: str


class Entity(BaseModel):
    id: str
    name: str
    attributes: List[Attribute] = Field(default_factory=list)


class Node(BaseModel):
    id: str
    table_name: str
    record_id: str
    searchable_content: str


class Edge(BaseModel):
    id: str
    from_node_id: str
    to_node_id: str
    edge_type: str
    searchable_content: str


class SearchResult(BaseModel):
    node_id: Optional[str] = None
    table_name: Optional[str] = None
    record_id: Optional[str] = None
    searchable_content: str
    source: str  # 'node' or 'edge'
    # Edge-specific fields
    edge_id: Optional[str] = None
    from_node_id: Optional[str] = None
    to_node_id: Optional[str] = None
    edge_type: Optional[str] = None


class ContextTree(BaseModel):
    """Represents a node in the knowledge graph with its data and relationships."""
    node: Optional[Node] = None
    entity: Optional[Entity] = None
    attribute: Optional[Attribute] = None
    children: List["ContextTree"] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)

