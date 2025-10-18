import click

from ._assemblers import xml_assembler
from ._models import ContextTree
from ._input_models import (
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
    CreateEdgeInput,
)
from . import domain
from ._utils._cli_utils import handle_errors


assembler = xml_assembler()

def display_context(context: ContextTree):
    """Display XML context for an entity"""
    click.echo(assembler(context))

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Bonnet - Knowledge Base Management CLI"""
    pass

@cli.command()
@click.option('--id', help='Unique Entity ID (auto-generated if not provided)')
@click.argument('text')
@handle_errors
def topic(id, text):
    """Store a master ENTITY record"""
    input_model = StoreEntityInput(e_id=id, name=text)
    actual_id = domain.store_entity(input_model)
    click.echo(f"Stored topic '{text}' with ID {actual_id}")

@cli.command()
@click.option('--about', required=True, help='Entity ID to link to')
@click.option('--type', 'attr_type', required=True, help='Attribute type (FACT, REF, etc.)')
@click.option('--subject', required=True, help='Subject text')
@click.argument('detail')
@handle_errors
def attr(about, attr_type, subject, detail):
    """Store an attribute"""
    input_model = StoreAttributeInput(attr_id=about, attr_type=attr_type, subject=subject, detail=detail)
    domain.store_attribute(input_model)
    click.echo(f"Stored {attr_type} attribute for entity {about}")

@cli.command()
@click.option('--from', 'from_entity', required=True, help='Source entity ID')
@click.option('--to', 'to_entity', required=True, help='Target entity ID')
@click.option('--type', 'edge_type', required=True, help='Edge type')
@click.option('--content', help='Edge content')
@handle_errors
def link(from_entity, to_entity, edge_type, content):
    """Create a link between two entities"""
    # Get node IDs for the entities
    from_node_id = domain.get_entity_node_id(from_entity)
    to_node_id = domain.get_entity_node_id(to_entity)
    
    if not from_node_id or not to_node_id:
        click.echo("One or both entities not found")
        return
    
    input_model = CreateEdgeInput(
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        edge_type=edge_type,
        searchable_content=content
    )
    edge_id = domain.create_edge(input_model)
    click.echo(f"Created edge {edge_id} from {from_entity} to {to_entity}")

@cli.command()
@click.option('--about', required=True, help='Search query')
@handle_errors
def context(about):
    """Search and generate context"""
    input_model = SearchEntitiesInput(query=about)
    context_tree = domain.search_entities(input_model)
    
    # Check if we have any results
    if not context_tree.children and context_tree.type == 'root':
        click.echo(f"No entities found for query: {about}")
        return
    
    # Display the context tree
    display_context(context_tree)