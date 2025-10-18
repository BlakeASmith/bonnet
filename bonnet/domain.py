"""Domain layer that returns Pydantic models after database fetches."""

from ._models import Attribute, Entity, ContextTree, Group, EntityReference, RelationshipType
from ._input_models import (
    GetEntityContextInput,
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
    GetGroupContextInput,
    SearchGroupsInput,
    StoreGroupInput,
    AddEntityToGroupInput,
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


def get_group_context(input: GetGroupContextInput) -> ContextTree:
    """
    Get group context from database and return as a ContextTree model.
    
    Args:
        input: GetGroupContextInput containing group_id
        
    Returns:
        ContextTree containing the group and its entities
    """
    context_data = database.get_group_context(input.group_id)
    
    # Convert entities from dicts to Entity models
    entities = []
    entity_references = []
    
    for entity_data in context_data['entities']:
        # Convert attributes from dicts to Attribute models
        attributes = [
            Attribute(
                type=attr['type'],
                subject=attr['subject'],
                detail=attr['detail']
            )
            for attr in entity_data['attributes']
        ]
        
        # Create Entity model
        entity = Entity(
            e_id=entity_data['e_id'],
            entity_name=entity_data['entity_name'],
            attributes=attributes
        )
        entities.append(entity)
    
    # Convert entity references
    for ref_data in context_data['entity_references']:
        entity_ref = EntityReference(
            e_id=ref_data['e_id'],
            relationship_type=RelationshipType(ref_data['relationship_type']) if ref_data['relationship_type'] else None
        )
        entity_references.append(entity_ref)
    
    # Create Group model
    group = Group(
        group_id=context_data['group_id'],
        group_name=context_data['group_name'],
        description=context_data['description'],
        entities=entities,
        entity_references=entity_references
    )
    
    # Wrap in ContextTree
    return ContextTree(entities=[group])


def search_groups(input: SearchGroupsInput) -> ContextTree:
    """
    Search for groups matching the query.
    
    Args:
        input: SearchGroupsInput containing query string
        
    Returns:
        ContextTree containing all matching groups
    """
    results = database.search_groups(input.query)
    groups = []
    
    for result in results:
        # Get full context for each group
        context_data = database.get_group_context(result['group_id'])
        
        # Convert entities from dicts to Entity models
        entities = []
        entity_references = []
        
        for entity_data in context_data['entities']:
            # Convert attributes from dicts to Attribute models
            attributes = [
                Attribute(
                    type=attr['type'],
                    subject=attr['subject'],
                    detail=attr['detail']
                )
                for attr in entity_data['attributes']
            ]
            
            # Create Entity model
            entity = Entity(
                e_id=entity_data['e_id'],
                entity_name=entity_data['entity_name'],
                attributes=attributes
            )
            entities.append(entity)
        
        # Convert entity references
        for ref_data in context_data['entity_references']:
            entity_ref = EntityReference(
                e_id=ref_data['e_id'],
                relationship_type=RelationshipType(ref_data['relationship_type']) if ref_data['relationship_type'] else None
            )
            entity_references.append(entity_ref)
        
        # Create Group model
        group = Group(
            group_id=context_data['group_id'],
            group_name=context_data['group_name'],
            description=context_data['description'],
            entities=entities,
            entity_references=entity_references
        )
        
        groups.append(group)
    
    return ContextTree(entities=groups)


def store_group(input: StoreGroupInput) -> bool:
    """
    Store a group record.
    
    Args:
        input: StoreGroupInput containing group_id, group_name, and description
        
    Returns:
        True if successful
    """
    return database.store_group(input.group_id, input.group_name, input.description)


def add_entity_to_group(input: AddEntityToGroupInput) -> bool:
    """
    Add an entity to a group with an optional relationship type.
    
    Args:
        input: AddEntityToGroupInput containing group_id, e_id, and relationship_type
        
    Returns:
        True if successful
    """
    return database.add_entity_to_group(input.group_id, input.e_id, input.relationship_type)

