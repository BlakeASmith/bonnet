"""Domain layer that returns Pydantic models after database fetches."""

from ._models import ContextTree, Node, Edge, build_model_from_record
from typing import Dict
from ._input_models import (
    SearchInput,
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
    CreateEdgeInput,
)
from . import database


def generate_topic_id() -> str:
    """
    Generate a simple topic ID with prefix and number.
    
    Returns:
        A simple ID like "T1", "T2", "T3", etc.
    """
    # Find the highest existing topic number
    max_number = database.get_max_topic_number()
    next_number = max_number + 1
    return f"T{next_number}"


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
        
        # Create edge models (for reference, but we'll follow them to get actual nodes)
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
        
        # Recursively build children (these are the actual connected nodes via edges)
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


def store_entity(input: StoreEntityInput) -> str:
    """
    Store a master ENTITY record.
    
    Args:
        input: StoreEntityInput containing e_id (optional) and name
        
    Returns:
        The entity ID used (either provided or generated)
    """
    # Generate simple topic ID if not provided
    e_id = input.e_id if input.e_id is not None else generate_topic_id()
    
    database.store_entity(e_id, input.name)
    return e_id


def store_attribute(input: StoreAttributeInput) -> bool:
    """
    Store an attribute (fact, task, rule, ref) and automatically link it to the entity.
    
    Args:
        input: StoreAttributeInput containing attr_id, attr_type, subject, and detail
        
    Returns:
        True if successful
    """
    return database.store_attribute(
        input.attr_id,
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


def search_entities(input: SearchEntitiesInput) -> ContextTree:
    """
    Search for entities using the knowledge graph.
    
    Args:
        input: SearchEntitiesInput containing query
        
    Returns:
        ContextTree containing matching entities and their context
    """
    # Use the existing search function with default parameters
    search_input = SearchInput(query=input.query, include_related=True, max_depth=1)
    return search(search_input)


def get_entity_node_id(entity_id: str) -> str:
    """
    Get the node ID for an entity.
    
    Args:
        entity_id: The entity ID
        
    Returns:
        The node ID if found, None otherwise
    """
    return database.get_entity_node_id(entity_id)

