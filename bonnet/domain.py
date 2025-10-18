"""Domain layer that returns Pydantic models after database fetches."""

from _models import Attribute, Entity, ContextTree
from _input_models import (
    GetEntityContextInput,
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
)
from . import database


def get_entity_context(input: GetEntityContextInput) -> ContextTree:
    """
    Get entity context from database and return as a ContextTree model.
    
    Args:
        input: GetEntityContextInput containing e_id
        
    Returns:
        ContextTree containing the entity and its attributes
    """
    context_data = database.get_entity_context(input.e_id)
    
    # Convert attributes from dicts to Attribute models
    attributes = [
        Attribute(
            type=attr['type'],
            subject=attr['subject'],
            detail=attr['detail']
        )
        for attr in context_data['attributes']
    ]
    
    # Create Entity model
    entity = Entity(
        e_id=context_data['e_id'],
        entity_name=context_data['entity_name'],
        attributes=attributes
    )
    
    # Wrap in ContextTree
    return ContextTree(entities=[entity])


def search_entities(input: SearchEntitiesInput) -> ContextTree:
    """
    Search for entities matching the query.
    
    Args:
        input: SearchEntitiesInput containing query string
        
    Returns:
        ContextTree containing all matching entities
    """
    results = database.search_entities(input.query)
    entities = []
    
    for result in results:
        # Get full context for each entity
        context_data = database.get_entity_context(result['e_id'])
        
        # Convert attributes from dicts to Attribute models
        attributes = [
            Attribute(
                type=attr['type'],
                subject=attr['subject'],
                detail=attr['detail']
            )
            for attr in context_data['attributes']
        ]
        
        # Create Entity model
        entity = Entity(
            e_id=context_data['e_id'],
            entity_name=context_data['entity_name'],
            attributes=attributes
        )
        
        entities.append(entity)
    
    return ContextTree(entities=entities)


def store_entity(input: StoreEntityInput) -> bool:
    """
    Store a master ENTITY record.
    
    Args:
        input: StoreEntityInput containing e_id, entity_name, and memo_search
        
    Returns:
        True if successful
    """
    return database.store_entity(input.e_id, input.entity_name, input.memo_search)


def store_attribute(input: StoreAttributeInput) -> bool:
    """
    Store a linked attribute (fact, task, rule, ref).
    
    Args:
        input: StoreAttributeInput containing e_id, attr_type, subject, and detail
        
    Returns:
        True if successful
    """
    return database.store_attribute(input.e_id, input.attr_type, input.subject, input.detail)

