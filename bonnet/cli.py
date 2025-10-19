import click

from ._assemblers import xml_assembler
from ._models import ContextTree
from ._input_models import (
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
    StoreFileInput,
    LinkInput,
)
from . import domain
from ._utils._cli_utils import handle_errors, find_record_with_feedback, search_and_display_records
from ._utils._completion import (
    complete_attribute_types,
    complete_attribute_subjects,
    complete_edge_types,
    complete_search_queries,
    complete_about,
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
    
    Shell Completion:
        Enable intelligent tab completion by running:
        bonnet completion --help
    """
    pass

@cli.command()
@click.option('--id', '-i', help='Unique Entity ID (auto-generated if not provided)')
@click.option('--short-name', '-x', help='Short name for the entity')
@click.argument('text')
@handle_errors
def topic(id, short_name, text):
    """Store a master ENTITY record"""
    input_model = StoreEntityInput(e_id=id, name=text, short_name=short_name)
    actual_id = domain.store_entity(input_model)
    short_name_msg = f" (short name: {short_name})" if short_name else ""
    click.echo(f"Stored topic '{text}'{short_name_msg} with ID {actual_id}")

@cli.command()
@click.option('--about', required=True, help='Record ID or search query to link to', shell_complete=complete_about)
@click.option('--type', 'attr_type', required=True, help='Attribute type (FACT, REF, etc.)', shell_complete=complete_attribute_types)
@click.option('--subject', required=True, help='Subject text', shell_complete=complete_attribute_subjects)
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
@click.option('--id', required=True, help='Unique File ID')
@click.option('--description', help='File description')
@click.option('--content', help='File content to include in context')
@click.option('--include-content', is_flag=True, help='Include file content in XML output')
@click.argument('file_path')
@handle_errors
def file(id, description, content, include_content, file_path):
    """Store a file reference
    
    Examples:
        file --id F1 --description "Config file" config.txt
        file --id F2 --description "Readme" --content "This is the readme content" --include-content readme.txt
        file --id F3 --description "Instructions" --content "Read this when setting up" --include-content instructions.txt
    """
    input_model = StoreFileInput(
        file_id=id, 
        file_path=file_path, 
        description=description,
        content=content,
        include_content=include_content
    )
    domain.store_file(input_model)
    content_msg = " (with content)" if include_content and content else ""
    click.echo(f"Stored file '{file_path}' with ID {id}{content_msg}")

@cli.command()
@click.option('--type', 'edge_type', default='references', help='Edge type (default: references)', shell_complete=complete_edge_types)
@click.option('--content', help='Edge content description')
@click.option('--no-interactive', is_flag=True, help='Automatically select first match when multiple records found')
@click.argument('from_identifier', shell_complete=complete_about)
@click.argument('to_identifier', shell_complete=complete_about)
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
@click.option('--about', required=True, help='Entity ID or search query', shell_complete=complete_about)
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
@click.argument('query', shell_complete=complete_about)
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
              help='Shell type for completion script (auto-detected from $SHELL if not specified)')
@click.option('--output', '-o', help='Output file path (default: stdout)')
def completion(shell, output):
    """Generate shell completion script for bonnet
    
    This command generates shell completion scripts that provide intelligent
    tab completion for all bonnet commands and options.
    
    Setup Instructions:
    
    For Bash:
        eval "$(bonnet completion --shell bash)"
        # Or add to ~/.bashrc:
        echo 'eval "$(bonnet completion --shell bash)"' >> ~/.bashrc
    
    For Zsh:
        # Option 1: Source directly (recommended)
        source <(bonnet completion --shell zsh)
        
        # Option 2: Add to ~/.zshrc
        echo 'source <(bonnet completion --shell zsh)' >> ~/.zshrc
        
        # Option 3: Use eval (if bonnet is in PATH)
        eval "$(bonnet completion --shell zsh)"
    
    For Fish:
        bonnet completion --shell fish > ~/.config/fish/completions/bonnet.fish
        # Fish automatically loads completions from this directory
    
    After setup, type 'bonnet ' and press TAB to see available completions.
    """
    import os
    import sys
    
    # Auto-detect shell if not specified
    if not shell:
        shell_env = os.environ.get('SHELL', '').lower()
        if 'bash' in shell_env:
            shell = 'bash'
        elif 'zsh' in shell_env:
            shell = 'zsh'
        elif 'fish' in shell_env:
            shell = 'fish'
        else:
            shell = 'bash'  # Default to bash
        click.echo(f"# Auto-detected shell: {shell}")
    
    # Generate the completion script using Click's built-in completion
    try:
        # Get the path to the bonnet executable
        import shutil
        bonnet_path = shutil.which('bonnet')
        if not bonnet_path:
            # Fallback to python module if bonnet not in PATH
            bonnet_path = 'python3 -m bonnet'
        
        if shell.lower() == 'bash':
            script = f"""# bash completion for bonnet
eval "$(_BONNET_COMPLETE=bash_source {bonnet_path})"
"""
        elif shell.lower() == 'zsh':
            script = f"""# zsh completion for bonnet
# Source this file in your ~/.zshrc or run: source <(bonnet completion --shell zsh)
eval "$(_BONNET_COMPLETE=zsh_source {bonnet_path})"
"""
        elif shell.lower() == 'fish':
            script = f"""# fish completion for bonnet
# Save this file to ~/.config/fish/completions/bonnet.fish
eval (env _BONNET_COMPLETE=fish_source {bonnet_path})
"""
        else:
            click.echo(f"Unsupported shell: {shell}", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error generating completion script: {e}", err=True)
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