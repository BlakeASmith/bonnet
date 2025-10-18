import click

from _assemblers import xml_assembler
from _models import ContextTree
from _input_models import (
    SearchEntitiesInput,
    StoreEntityInput,
    StoreAttributeInput,
)
from . import domain
from _utils._cli_utils import handle_errors


assembler = xml_assembler()

def display_context(context: ContextTree):
    """Display XML context for an entity"""
    click.echo(assembler(context))

def handle_disambiguation(context_tree, query):
    """Handle disambiguation when multiple entities are found"""
    entities = context_tree.entities
    click.echo(f"Found {len(entities)} entities matching '{query}':")
    for i, entity in enumerate(entities, 1):
        click.echo(f"{i}. {entity.e_id}: {entity.entity_name}")
    
    while True:
        try:
            choice = click.prompt("Select entity number (or 'q' to quit)", default='q')
            if choice.lower() == 'q':
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(entities):
                selected_entity = entities[choice_num - 1]
                # Create a ContextTree with just the selected entity
                single_context = ContextTree(entities=[selected_entity])
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