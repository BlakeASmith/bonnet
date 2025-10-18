"""Input Pydantic models for domain functions."""

from typing import Optional
from pydantic import BaseModel


class GetEntityContextInput(BaseModel):
    e_id: str


class SearchEntitiesInput(BaseModel):
    query: str


class StoreEntityInput(BaseModel):
    e_id: str
    entity_name: str
    memo_search: str


class StoreAttributeInput(BaseModel):
    e_id: str
    attr_type: str
    subject: str
    detail: str


class GetGroupContextInput(BaseModel):
    group_id: str


class SearchGroupsInput(BaseModel):
    query: str


class StoreGroupInput(BaseModel):
    group_id: str
    group_name: str
    description: Optional[str] = None


class AddEntityToGroupInput(BaseModel):
    group_id: str
    e_id: str
    relationship_type: Optional[str] = None

