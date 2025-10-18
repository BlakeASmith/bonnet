from typing import List, Union, Optional
from enum import Enum

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    type: str
    subject: str
    detail: str


class Entity(BaseModel):
    e_id: str
    entity_name: str
    attributes: List[Attribute]


class RelationshipType(str, Enum):
    """Types of relationships between entities in a group."""
    CONTAINS = "contains"
    RELATES_TO = "relates_to"
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    IMPLEMENTS = "implements"


class EntityReference(BaseModel):
    """Reference to an entity within a group with optional relationship type."""
    e_id: str
    relationship_type: Optional[RelationshipType] = None


class Group(BaseModel):
    """A group that contains multiple entities and can be nested."""
    group_id: str
    group_name: str
    description: Optional[str] = None
    entities: List[Union[Entity, "Group"]] = Field(default_factory=list)
    entity_references: List[EntityReference] = Field(default_factory=list)


class ContextTree(BaseModel):
    """Root container that can hold entities, groups, or other context trees."""
    entities: List[Union[Entity, Group, "ContextTree"]] = Field(default_factory=list)

