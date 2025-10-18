from typing import List, Union

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
    entities: List[Union[Entity, "ContextTree"]] = Field(default_factory=list)

