import click
import sys
from .database import BonnetDB

# Initialize database
db = BonnetDB()

def store_topic(e_id: str, topic_text: str) -> None:
    """Store a master ENTITY record."""
    try:
        db.store_entity(e_id, topic_text, topic_text)
        click.echo(f"Stored topic '{topic_text}' with ID {e_id}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

def store_fact(e_id: str, fact_text: str) -> None:
    """Store a FACT attribute."""
    try:
        # Parse fact as "subject=detail" format
        if '=' in fact_text:
            subject, detail = fact_text.split('=', 1)
            subject = subject.strip()
            detail = detail.strip()
        else:
            subject = "fact"
            detail = fact_text
        
        db.store_attribute(e_id, 'FACT', subject, detail)
        click.echo(f"Stored fact '{subject}={detail}' for entity {e_id}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

def store_ref(e_id: str, ref_text: str, ref_id: str) -> None:
    """Store a REF attribute."""
    try:
        db.store_attribute(e_id, 'REF', ref_text, ref_id)
        click.echo(f"Stored reference '{ref_text}' with ID {ref_id} for entity {e_id}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

def search_disambiguate(query: str) -> None:
    """Search and disambiguate entities."""
    try:
        results = db.search_entities(query)
        
        if not results:
            click.echo(f"No entities found for query: {query}")
            return
        
        if len(results) == 1:
            # Single result, generate context directly
            e_id = results[0]['e_id']
            generate_xml_context(e_id)
        else:
            # Multiple results, prompt for selection
            click.echo(f"Found {len(results)} entities matching '{query}':")
            for i, result in enumerate(results, 1):
                click.echo(f"{i}. {result['e_id']}: {result['subject']}")
            
            while True:
                try:
                    choice = click.prompt("Select entity number (or 'q' to quit)", default='q')
                    if choice.lower() == 'q':
                        return
                    
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(results):
                        e_id = results[choice_num - 1]['e_id']
                        generate_xml_context(e_id)
                        break
                    else:
                        click.echo(f"Please enter a number between 1 and {len(results)}")
                except ValueError:
                    click.echo("Please enter a valid number or 'q' to quit")
                except KeyboardInterrupt:
                    click.echo("\nExiting...")
                    return
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

def generate_xml_context(e_id: str) -> None:
    """Generate XML context for an entity."""
    try:
        context = db.get_entity_context(e_id)
        
        click.echo("<context>")
        click.echo(f"{context['e_id']}:\"{context['entity_name']}\"")
        
        for attr in context['attributes']:
            if attr['type'] == 'FACT':
                click.echo(f"Fact:{context['e_id']}:{attr['subject']}={attr['detail']}")
            elif attr['type'] == 'REF':
                click.echo(f"Ref:{context['e_id']}:{attr['subject']} (ID: {attr['detail']})")
        
        click.echo("</context>")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Bonnet - Knowledge Base Management CLI"""
    pass

@cli.command()
@click.option('--id', required=True, help='Unique Entity ID')
@click.argument('text')
def topic(id, text):
    """Store a master ENTITY record"""
    store_topic(id, text)

@cli.command()
@click.option('--about', required=True, help='Entity ID to link to')
@click.argument('text')
def fact(about, text):
    """Store a FACT attribute"""
    store_fact(about, text)

@cli.command()
@click.option('--about', required=True, help='Entity ID to link to')
@click.option('--id', 'ref_id', required=True, help='Reference ID')
@click.argument('text')
def ref(about, ref_id, text):
    """Store a REF attribute"""
    store_ref(about, text, ref_id)

@cli.command()
@click.option('--about', required=True, help='Search query')
def context(about):
    """Search and generate context"""
    search_disambiguate(about)