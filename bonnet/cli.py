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
from ._utils._completion import (
    complete_record_ids,
    complete_entity_ids,
    complete_attribute_types,
    complete_edge_types,
    complete_file_paths,
    complete_search_queries,
)


assembler = xml_assembler()

def display_context(context: ContextTree):
    """Display XML context for an entity"""
    click.echo(assembler(context))

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Bonnet - Knowledge Base Management CLI
    
    A CLI tool for managing structured knowledge base (memory) and preparing 
    highly compressed XML context.
    
    For shell completion setup, run:
        bonnet completion --help
    """
    pass

@cli.command()
@click.option('--id', help='Unique Entity ID (auto-generated if not provided)', shell_complete=complete_entity_ids)
@click.argument('text', shell_complete=complete_search_queries)
@handle_errors
def topic(id, text):
    """Store a master ENTITY record"""
    input_model = StoreEntityInput(e_id=id, name=text)
    actual_id = domain.store_entity(input_model)
    click.echo(f"Stored topic '{text}' with ID {actual_id}")

@cli.command()
@click.option('--about', required=True, help='Record ID or search query to link to', shell_complete=complete_record_ids)
@click.option('--type', 'attr_type', required=True, help='Attribute type (FACT, REF, etc.)', shell_complete=complete_attribute_types)
@click.option('--subject', required=True, help='Subject text', shell_complete=complete_search_queries)
@click.option('--no-interactive', is_flag=True, help='Automatically select first match when multiple records found')
@click.argument('detail', shell_complete=complete_search_queries)
@handle_errors
def attr(about, attr_type, subject, detail, no_interactive):
    """Store an attribute
    
    You can use either a record ID or search query for the --about option.
    The system will automatically find the matching record.
    
    Examples:
        attr --about T1 --type FACT --subject color "red"     # Using record ID
        attr --about "car" --type FACT --subject color "red"  # Using search query
        attr --about "bike" --type FACT --subject type "mountain"  # Link to any record
        attr --about "shark" --type FACT --subject species "great white" --no-interactive  # Auto-select first match
    """
    # Find the target record using the enhanced function
    target_record_id = find_record_with_feedback(about, no_interactive)
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
@click.option('--id', required=True, help='Unique File ID', shell_complete=complete_record_ids)
@click.option('--description', help='File description', shell_complete=complete_search_queries)
@click.argument('file_path', shell_complete=complete_file_paths)
@handle_errors
def file(id, description, file_path):
    """Store a file reference"""
    input_model = StoreFileInput(file_id=id, file_path=file_path, description=description)
    domain.store_file(input_model)
    click.echo(f"Stored file '{file_path}' with ID {id}")

@cli.command()
@click.option('--type', 'edge_type', default='references', help='Edge type (default: references)', shell_complete=complete_edge_types)
@click.option('--content', help='Edge content description', shell_complete=complete_search_queries)
@click.option('--no-interactive', is_flag=True, help='Automatically select first match when multiple records found')
@click.argument('from_identifier', shell_complete=complete_record_ids)
@click.argument('to_identifier', shell_complete=complete_record_ids)
@handle_errors
def link(from_identifier, to_identifier, edge_type, content, no_interactive):
    """Create a link between any two records
    
    You can use either record IDs or search queries for the source and target.
    The system will automatically detect the record types.
    
    Examples:
        link "car" "black"                    # Link car entity to black attribute
        link T1 T2                           # Link entity T1 to entity T2
        link "bike" "red color"              # Link bike to red color attribute
        link "shark" "fish" --no-interactive  # Auto-select first matches
    """
    # Find source record using the enhanced function
    from_record_id = find_record_with_feedback(from_identifier, no_interactive)
    if not from_record_id:
        return
    
    # Get the full source record details
    from_results = domain.search_records(from_identifier)
    from_record = next((r for r in from_results if r['id'] == from_record_id), None)
    if not from_record:
        click.echo(f"Error: Could not find source record with ID {from_record_id}", err=True)
        return
    
    # Find target record using the enhanced function
    to_record_id = find_record_with_feedback(to_identifier, no_interactive)
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
@click.option('--about', required=True, help='Entity ID or search query', shell_complete=complete_record_ids)
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
@click.argument('query', shell_complete=complete_search_queries)
@handle_errors
def search(limit, query):
    """Search for records by content across all record types
    
    Examples:
        search "car"      # Search for records containing "car"
        search "color"    # Search for records containing "color"
    """
    search_and_display_records(query, limit)


@cli.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish'], case_sensitive=False), 
              default='bash', help='Shell type for completion script')
@click.option('--output', '-o', help='Output file path (default: stdout)')
def completion(shell, output):
    """Generate shell completion script for bonnet
    
    Examples:
        bonnet completion --shell bash > ~/.bonnet-complete.bash
        bonnet completion --shell zsh > ~/.bonnet-complete.zsh
        bonnet completion --shell fish > ~/.config/fish/completions/bonnet.fish
    """
    import os
    import sys
    
    # Generate the completion script
    if shell.lower() == 'bash':
        script = cli.get_completion_script('bash')
    elif shell.lower() == 'zsh':
        script = cli.get_completion_script('zsh')
    elif shell.lower() == 'fish':
        script = cli.get_completion_script('fish')
    else:
        click.echo(f"Unsupported shell: {shell}", err=True)
        sys.exit(1)
    
    # Output the script
    if output:
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output), exist_ok=True)
            with open(output, 'w') as f:
                f.write(script)
            click.echo(f"Completion script written to {output}")
        except Exception as e:
            click.echo(f"Error writing to {output}: {e}", err=True)
            sys.exit(1)
    else:
        click.echo(script)