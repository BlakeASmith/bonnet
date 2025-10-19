from typing import List, Union, Optional, Dict, Any, Callable

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    id: str
    type: str
    subject: str
    detail: str


class Entity(BaseModel):
    id: str
    name: str
    short_name: Optional[str] = None


class File(BaseModel):
    id: str
    file_path: str
    description: Optional[str] = None


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
    type: str  # 'entity', 'attribute', 'file', or 'root'
    data: Union[Entity, Attribute, File, None]  # None for root nodes
    node: Node
    children: List["ContextTree"] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)


# Registry pattern for building Pydantic models from database records
MODEL_BUILDERS: Dict[str, Callable[[Dict[str, Any]], Union[Entity, Attribute]]] = {}


def model_builder(record_type: str) -> Callable[[Callable], Callable]:
    """Decorator to register a function that builds a Pydantic model from a database record."""
    def decorator(func: Callable[[Dict[str, Any]], Union[Entity, Attribute]]) -> Callable:
        MODEL_BUILDERS[record_type] = func
        return func
    return decorator


@model_builder('entity')
def build_entity_model(record_data: Dict[str, Any]) -> Entity:
    """Build an Entity model from database record data."""
    return Entity(
        id=record_data['id'],
        name=record_data['name'],
        short_name=record_data.get('short_name')
    )


@model_builder('attribute')
def build_attribute_model(record_data: Dict[str, Any]) -> Attribute:
    """Build an Attribute model from database record data."""
    return Attribute(
        id=record_data['id'],
        type=record_data['attr_type'],
        subject=record_data['subject'],
        detail=record_data['detail']
    )


@model_builder('file')
def build_file_model(record_data: Dict[str, Any]) -> File:
    """Build a File model from database record data."""
    return File(
        id=record_data['id'],
        file_path=record_data['file_path'],
        description=record_data['description']
    )


def build_model_from_record(record_data: Dict[str, Any]) -> Union[Entity, Attribute, File]:
    """Build the appropriate Pydantic model from a database record using the registry."""
    record_type = record_data.get('type')
    if record_type not in MODEL_BUILDERS:
        raise ValueError(f"Unknown record type: {record_type}")
    
    return MODEL_BUILDERS[record_type](record_data)

