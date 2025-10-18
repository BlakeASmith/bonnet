import click

from ._assemblers import xml_assembler
from ._models import ContextTree
from ._input_models import (
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
    CreateEdgeInput,
    StoreFileInput,
    LinkInput,
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
@click.option('--id', required=True, help='Unique Entity ID')
@click.argument('text')
@handle_errors
def topic(id, text):
    """Store a master ENTITY record"""
    input_model = StoreEntityInput(e_id=id, name=text)
    domain.store_entity(input_model)
    click.echo(f"Stored topic '{text}' with ID {id}")

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
@click.option('--id', required=True, help='Unique File ID')
@click.option('--description', help='File description')
@click.argument('file_path')
@handle_errors
def file(id, description, file_path):
    """Store a file reference"""
    input_model = StoreFileInput(file_id=id, file_path=file_path, description=description)
    domain.store_file(input_model)
    click.echo(f"Stored file '{file_path}' with ID {id}")

@cli.command()
@click.option('--from-type', required=True, type=click.Choice(['entity', 'file', 'attribute']), help='Source record type')
@click.option('--from-id', required=True, help='Source record ID')
@click.option('--to-type', required=True, type=click.Choice(['entity', 'file', 'attribute']), help='Target record type')
@click.option('--to-id', required=True, help='Target record ID')
@click.option('--type', 'edge_type', default='references', help='Edge type (default: references)')
@click.option('--content', help='Edge content description')
@handle_errors
def link(from_type, from_id, to_type, to_id, edge_type, content):
    """Create a link between any two records"""
    input_model = LinkInput(
        from_type=from_type,
        from_id=from_id,
        to_type=to_type,
        to_id=to_id,
        edge_type=edge_type,
        content=content
    )
    edge_id = domain.link(input_model)
    click.echo(f"Created edge {edge_id} linking {from_type}:{from_id} to {to_type}:{to_id}")

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