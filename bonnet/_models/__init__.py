from typing import List

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    type: str
    subject: str
    detail: str


class Entity(BaseModel):
    e_id: str
    entity_name: str
    attributes: List[Attribute]


class ContextTree(BaseModel):
    entities: List[Entity | "ContextTree"] = Field(default_factory=list)

