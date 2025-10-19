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
from ._utils._cli_utils import handle_errors, find_record_with_feedback, search_and_display_records


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
@click.option('--about', required=True, help='Record ID or search query to link to')
@click.option('--type', 'attr_type', required=True, help='Attribute type (FACT, REF, etc.)')
@click.option('--subject', required=True, help='Subject text')
@click.option('--select-index', type=int, help='Select specific match by index when multiple records found')
@click.argument('detail')
@handle_errors
def attr(about, attr_type, subject, detail, select_index):
    """Store an attribute
    
    You can use either a record ID or search query for the --about option.
    The system will automatically find the matching record.
    
    Examples:
        attr --about T1 --type FACT --subject color "red"     # Using record ID
        attr --about "car" --type FACT --subject color "red"  # Using search query
        attr --about "bike" --type FACT --subject type "mountain"  # Link to any record
        attr --about "shark" --type FACT --subject species "great white" --select-index 1  # Select first match
    """
    # Find the target record using the enhanced function
    target_record_id = find_record_with_feedback(about, select_index)
    if not target_record_id:
        return
    
    # Get the full record details
    results = domain.search_records(about)
    target_record = next((r for r in results if r['id'] == target_record_id), None)
    if not target_record:
        click.echo(f"Error: Could not find record with ID {target_record_id}", err=True)
        return
    
    input_model = StoreAttributeInput(attr_id=target_record['id'], attr_type=attr_type, subject=subject, detail=detail)
    domain.store_attribute(input_model)
    click.echo(f"Stored {attr_type} attribute for {target_record['type']} {target_record['id']} ({target_record['display']})")

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
@click.option('--from-select-index', type=int, help='Select specific match by index for source record when multiple found')
@click.option('--to-select-index', type=int, help='Select specific match by index for target record when multiple found')
@click.argument('from_identifier')
@click.argument('to_identifier')
@handle_errors
def link(from_identifier, to_identifier, edge_type, content, from_select_index, to_select_index):
    """Create a link between any two records
    
    You can use either record IDs or search queries for the source and target.
    The system will automatically detect the record types.
    
    Examples:
        link "car" "black"                    # Link car entity to black attribute
        link T1 T2                           # Link entity T1 to entity T2
        link "bike" "red color"              # Link bike to red color attribute
        link "shark" "fish" --from-select-index 1 --to-select-index 2  # Select specific matches
    """
    # Find source record using the enhanced function
    from_record_id = find_record_with_feedback(from_identifier, from_select_index)
    if not from_record_id:
        return
    
    # Get the full source record details
    from_results = domain.search_records(from_identifier)
    from_record = next((r for r in from_results if r['id'] == from_record_id), None)
    if not from_record:
        click.echo(f"Error: Could not find source record with ID {from_record_id}", err=True)
        return
    
    # Find target record using the enhanced function
    to_record_id = find_record_with_feedback(to_identifier, to_select_index)
    if not to_record_id:
        return
    
    # Get the full target record details
    to_results = domain.search_records(to_identifier)
    to_record = next((r for r in to_results if r['id'] == to_record_id), None)
    if not to_record:
        click.echo(f"Error: Could not find target record with ID {to_record_id}", err=True)
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
@click.option('--about', required=True, help='Entity ID or search query')
@handle_errors
def context(about):
    """Search and generate context for entities
    
    You can use either an entity ID or search query for the --about option.
    The system will find matching entities and display their context.
    
    Examples:
        context --about T1                    # Using entity ID
        context --about "car"                 # Using search query
        context --about "red color"           # Using search query
    """
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