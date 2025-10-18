"""Input Pydantic models for domain functions."""

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

