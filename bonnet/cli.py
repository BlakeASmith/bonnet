import click

from ._assemblers import xml_assembler
from ._models import ContextTree
from ._input_models import (
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
    GetGroupContextInput,
    SearchGroupsInput,
    StoreGroupInput,
    AddEntityToGroupInput,
)
from . import domain
from ._utils._cli_utils import handle_errors


assembler = xml_assembler()

def display_context(context: ContextTree):
    """Display XML context for an entity"""
    click.echo(assembler(context))

def handle_disambiguation(context_tree, query):
    """Handle disambiguation when multiple entities are found"""
    entities = context_tree.entities
    click.echo(f"Found {len(entities)} items matching '{query}':")
    for i, item in enumerate(entities, 1):
        if hasattr(item, 'e_id'):
            click.echo(f"{i}. Entity: {item.e_id}: {item.entity_name}")
        elif hasattr(item, 'group_id'):
            click.echo(f"{i}. Group: {item.group_id}: {item.group_name}")
    
    while True:
        try:
            choice = click.prompt("Select item number (or 'q' to quit)", default='q')
            if choice.lower() == 'q':
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(entities):
                selected_item = entities[choice_num - 1]
                # Create a ContextTree with just the selected item
                single_context = ContextTree(entities=[selected_item])
                display_context(single_context)
                break
            else:
                click.echo(f"Please enter a number between 1 and {len(entities)}")
        except ValueError:
            click.echo("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            click.echo("\nExiting...")
            return

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
    input_model = StoreEntityInput(e_id=id, entity_name=text, memo_search=text)
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
    input_model = StoreAttributeInput(e_id=about, attr_type=attr_type, subject=subject, detail=detail)
    domain.store_attribute(input_model)
    click.echo(f"Stored {attr_type} attribute for entity {about}")

@cli.command()
@click.option('--about', required=True, help='Search query')
@handle_errors
def context(about):
    """Search and generate context"""
    input_model = SearchEntitiesInput(query=about)
    context_tree = domain.search_entities(input_model)
    
    if not context_tree.entities:
        click.echo(f"No entities found for query: {about}")
        return
    
    if len(context_tree.entities) == 1:
        display_context(context_tree)
    else:
        handle_disambiguation(context_tree, about)


@cli.group()
def group():
    """Group management commands"""
    pass


@group.command()
@click.option('--id', required=True, help='Unique Group ID')
@click.option('--name', required=True, help='Group name')
@click.option('--description', help='Group description')
@handle_errors
def create(id, name, description):
    """Create a new group"""
    input_model = StoreGroupInput(group_id=id, group_name=name, description=description)
    domain.store_group(input_model)
    click.echo(f"Created group '{name}' with ID {id}")


@group.command()
@click.option('--group-id', required=True, help='Group ID')
@click.option('--entity-id', required=True, help='Entity ID to add')
@click.option('--relationship', help='Relationship type (contains, relates_to, depends_on, part_of, implements)')
@handle_errors
def add_entity(group_id, entity_id, relationship):
    """Add an entity to a group"""
    input_model = AddEntityToGroupInput(group_id=group_id, e_id=entity_id, relationship_type=relationship)
    domain.add_entity_to_group(input_model)
    click.echo(f"Added entity {entity_id} to group {group_id}")


@group.command()
@click.option('--id', required=True, help='Group ID')
@handle_errors
def show(id):
    """Show group context"""
    input_model = GetGroupContextInput(group_id=id)
    context_tree = domain.get_group_context(input_model)
    display_context(context_tree)


@group.command()
@click.option('--query', required=True, help='Search query')
@handle_errors
def search(query):
    """Search for groups"""
    input_model = SearchGroupsInput(query=query)
    context_tree = domain.search_groups(input_model)
    
    if not context_tree.entities:
        click.echo(f"No groups found for query: {query}")
        return
    
    if len(context_tree.entities) == 1:
        display_context(context_tree)
    else:
        handle_disambiguation(context_tree, query)