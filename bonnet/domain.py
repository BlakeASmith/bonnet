"""Domain layer that returns Pydantic models after database fetches."""

from _models import Attribute, Entity, ContextTree, SearchResult, Node, Edge, build_model_from_record
from typing import Dict
from _input_models import (
    GetEntityContextInput,
    SearchInput,
    StoreEntityInput,
    StoreAttributeInput,
    CreateEdgeInput,
)
import database


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



def search(input: SearchInput) -> ContextTree:
    """
    Search the knowledge graph using FTS and optionally include related nodes.
    
    Args:
        input: SearchInput containing query, include_related, and max_depth
        
    Returns:
        ContextTree containing the graph structure
    """
    # Get the graph structure
    graph_structure = database.get_graph_structure(
        input.query, 
        input.include_related, 
        input.max_depth
    )
    
    # Convert graph structure to ContextTree
    def build_context_tree(node_data: Dict) -> ContextTree:
        # Create the node model
        node = Node(
            id=node_data['node']['id'],
            table_name=node_data['node']['table_name'],
            record_id=node_data['node']['record_id'],
            searchable_content=node_data['node']['searchable_content']
        )
        
        # Create the record model (entity or attribute) and determine type using registry
        data = None
        node_type = 'root'
        
        if node_data['record']['type'] in ['entity', 'attribute']:
            data = build_model_from_record(node_data['record'])
            node_type = node_data['record']['type']
        
        # Create edge models
        edges = []
        for edge_data in node_data['edges']:
            edge = Edge(
                id=edge_data['id'],
                from_node_id=edge_data['from_node_id'],
                to_node_id=edge_data['to_node_id'],
                edge_type=edge_data['edge_type'],
                searchable_content=edge_data['searchable_content']
            )
            edges.append(edge)
        
        # Recursively build children
        children = []
        for child_data in node_data['children']:
            child_tree = build_context_tree(child_data)
            children.append(child_tree)
        
        return ContextTree(
            type=node_type,
            data=data,
            node=node,
            children=children,
            edges=edges
        )
    
    # Build the root context tree
    if not graph_structure:
        # Create an empty root node
        return ContextTree(
            type='root',
            data=None,
            node=Node(id='', table_name='', record_id='', searchable_content=''),
            children=[],
            edges=[]
        )
    
    # If multiple root nodes, create a wrapper tree
    if len(graph_structure) == 1:
        return build_context_tree(graph_structure[0])
    else:
        # Multiple root nodes - create a wrapper
        children = []
        for node_data in graph_structure:
            child_tree = build_context_tree(node_data)
            children.append(child_tree)
        
        return ContextTree(
            type='root',
            data=None,
            node=Node(id='', table_name='', record_id='', searchable_content=''),
            children=children,
            edges=[]
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

