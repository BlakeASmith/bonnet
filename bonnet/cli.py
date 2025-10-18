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
from ._utils._cli_utils import handle_errors, find_record_with_feedback, search_and_display_records, resolve_record_identifier


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
@click.option('--type', 'edge_type', default='references', help='Edge type (default: references)')
@click.option('--content', help='Edge content description')
@click.argument('from_identifier')
@click.argument('to_identifier')
@handle_errors
def link(from_identifier, to_identifier, edge_type, content):
    """Create a link between any two records
    
    You can use either record IDs or search queries for the source and target.
    The system will automatically detect the record types.
    
    Examples:
        link "car" "black"                    # Link car entity to black attribute
        link T1 T2                           # Link entity T1 to entity T2
        link "bike" "red color"              # Link bike to red color attribute
    """
    # Resolve source record
    from_record = resolve_record_identifier(from_identifier)
    if not from_record:
        # Try searching for similar records
        search_results = domain.search_records(from_identifier)
        if search_results:
            click.echo(f"No exact match found for '{from_identifier}'. Did you mean one of these?", err=True)
            for i, result in enumerate(search_results[:5], 1):  # Show top 5 results
                click.echo(f"  {i}. {result['display']} ({result['type']}:{result['id']})", err=True)
            click.echo("Please be more specific or use the exact ID.", err=True)
        else:
            click.echo(f"No records found matching '{from_identifier}'", err=True)
        return
    
    # Resolve target record
    to_record = resolve_record_identifier(to_identifier)
    if not to_record:
        # Try searching for similar records
        search_results = domain.search_records(to_identifier)
        if search_results:
            click.echo(f"No exact match found for '{to_identifier}'. Did you mean one of these?", err=True)
            for i, result in enumerate(search_results[:5], 1):  # Show top 5 results
                click.echo(f"  {i}. {result['display']} ({result['type']}:{result['id']})", err=True)
            click.echo("Please be more specific or use the exact ID.", err=True)
        else:
            click.echo(f"No records found matching '{to_identifier}'", err=True)
        return
    
    input_model = LinkInput(
        from_type=from_record['type'],
        from_id=from_record['id'],
        to_type=to_record['type'],
        to_id=to_record['id'],
        edge_type=edge_type,
        content=content
    )
    edge_id = domain.link(input_model)
    click.echo(f"Created edge {edge_id} linking {from_record['type']}:{from_record['id']} to {to_record['type']}:{to_record['id']}")

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

@cli.command()
@click.option('--limit', default=10, help='Maximum number of results to show (default: 10)')
@click.argument('query')
@handle_errors
def search(limit, query):
    """Search for records by content across all record types
    
    Examples:
        search "car"      # Search for records containing "car"
        search "color"    # Search for records containing "color"
    """
    search_and_display_records(query, limit)