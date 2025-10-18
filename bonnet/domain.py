"""Domain layer that returns Pydantic models after database fetches."""

from ._models import Attribute, Entity, ContextTree, SearchResult, KnowledgeGraphSearchResult
from ._input_models import (
    GetEntityContextInput,
    SearchEntitiesInput,
    SearchKnowledgeGraphInput,
    StoreEntityInput,
    StoreAttributeInput,
    CreateEdgeInput,
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
            id=attr['id'],
            type=attr['type'],
            subject=attr['subject'],
            detail=attr['detail']
        )
        for attr in context_data['attributes']
    ]
    
    # Create Entity model
    entity = Entity(
        id=context_data['e_id'],
        name=context_data['entity_name'],
        attributes=attributes
    )
    
    # Wrap in ContextTree
    return ContextTree(entities=[entity])


def search_entities(input: SearchEntitiesInput) -> ContextTree:
    """
    Search for entities matching the query using the old search method.
    This is kept for backward compatibility.
    
    Args:
        input: SearchEntitiesInput containing query string
        
    Returns:
        ContextTree containing all matching entities
    """
    # For now, use the knowledge graph search and filter for entities only
    kg_results = search_knowledge_graph(SearchKnowledgeGraphInput(query=input.query))
    
    entities = []
    for record in kg_results.related_records:
        if isinstance(record, Entity):
            entities.append(record)
    
    return ContextTree(entities=entities)

def search_knowledge_graph(input: SearchKnowledgeGraphInput) -> KnowledgeGraphSearchResult:
    """
    Search the knowledge graph using FTS and optionally include related nodes.
    
    Args:
        input: SearchKnowledgeGraphInput containing query, include_related, and max_depth
        
    Returns:
        KnowledgeGraphSearchResult containing search results and related records
    """
    # Search the knowledge graph
    search_data = database.search_knowledge_graph(
        input.query, 
        input.include_related, 
        input.max_depth
    )
    
    # Convert search results to SearchResult models
    search_results = []
    for result in search_data['search_results']:
        search_result = SearchResult(
            searchable_content=result['searchable_content'],
            source=result['source']
        )
        
        if result['source'] == 'node':
            search_result.node_id = result['node_id']
            search_result.table_name = result['table_name']
            search_result.record_id = result['record_id']
        else:  # edge
            search_result.edge_id = result['edge_id']
            search_result.from_node_id = result['from_node_id']
            search_result.to_node_id = result['to_node_id']
            search_result.edge_type = result['edge_type']
        
        search_results.append(search_result)
    
    # Convert related records to appropriate models
    related_records = []
    for record_data in search_data['related_records']:
        if record_data['type'] == 'entity':
            entity = Entity(
                id=record_data['id'],
                name=record_data['name']
            )
            related_records.append(entity)
        elif record_data['type'] == 'attribute':
            attribute = Attribute(
                id=record_data['id'],
                type=record_data['attr_type'],
                subject=record_data['subject'],
                detail=record_data['detail']
            )
            related_records.append(attribute)
    
    return KnowledgeGraphSearchResult(
        search_results=search_results,
        related_records=related_records
    )


def store_entity(input: StoreEntityInput) -> bool:
    """
    Store a master ENTITY record.
    
    Args:
        input: StoreEntityInput containing e_id and name
        
    Returns:
        True if successful
    """
    return database.store_entity(
        input.e_id, 
        input.name
    )


def store_attribute(input: StoreAttributeInput) -> bool:
    """
    Store a linked attribute (fact, task, rule, ref).
    
    Args:
        input: StoreAttributeInput containing attr_id, entity_id, attr_type, subject, and detail
        
    Returns:
        True if successful
    """
    return database.store_attribute(
        input.attr_id,
        input.entity_id, 
        input.attr_type, 
        input.subject, 
        input.detail
    )


def create_edge(input: CreateEdgeInput) -> str:
    """
    Create an edge between two nodes.
    
    Args:
        input: CreateEdgeInput containing from_node_id, to_node_id, edge_type, and searchable_content
        
    Returns:
        Edge ID if successful
    """
    return database.create_edge(
        input.from_node_id,
        input.to_node_id,
        input.edge_type,
        input.searchable_content or ""
    )

