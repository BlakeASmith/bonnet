import click
import sys
from functools import wraps
from .database import BonnetDB

# Initialize database
db = BonnetDB()

def handle_errors(func):
    """Decorator to handle common CLI errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    return wrapper

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
    db.store_entity(id, text, text)
    click.echo(f"Stored topic '{text}' with ID {id}")

@cli.command()
@click.option('--about', required=True, help='Entity ID to link to')
@click.argument('text')
@handle_errors
def fact(about, text):
    """Store a FACT attribute"""
    # Parse fact as "subject=detail" format
    if '=' in text:
        subject, detail = text.split('=', 1)
        subject = subject.strip()
        detail = detail.strip()
    else:
        subject = "fact"
        detail = text
    
    db.store_attribute(about, 'FACT', subject, detail)
    click.echo(f"Stored fact '{subject}={detail}' for entity {about}")

@cli.command()
@click.option('--about', required=True, help='Entity ID to link to')
@click.option('--id', 'ref_id', required=True, help='Reference ID')
@click.argument('text')
@handle_errors
def ref(about, ref_id, text):
    """Store a REF attribute"""
    db.store_attribute(about, 'REF', text, ref_id)
    click.echo(f"Stored reference '{text}' with ID {ref_id} for entity {about}")

@cli.command()
@click.option('--about', required=True, help='Search query')
@handle_errors
def context(about):
    """Search and generate context"""
    results = db.search_entities(about)
    
    if not results:
        click.echo(f"No entities found for query: {about}")
        return
    
    if len(results) == 1:
        # Single result, generate context directly
        e_id = results[0]['e_id']
        context_data = db.get_entity_context(e_id)
        
        click.echo("<context>")
        click.echo(f"{context_data['e_id']}:\"{context_data['entity_name']}\"")
        
        for attr in context_data['attributes']:
            if attr['type'] == 'FACT':
                click.echo(f"Fact:{context_data['e_id']}:{attr['subject']}={attr['detail']}")
            elif attr['type'] == 'REF':
                click.echo(f"Ref:{context_data['e_id']}:{attr['subject']} (ID: {attr['detail']})")
        
        click.echo("</context>")
    else:
        # Multiple results, prompt for selection
        click.echo(f"Found {len(results)} entities matching '{about}':")
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
                    context_data = db.get_entity_context(e_id)
                    
                    click.echo("<context>")
                    click.echo(f"{context_data['e_id']}:\"{context_data['entity_name']}\"")
                    
                    for attr in context_data['attributes']:
                        if attr['type'] == 'FACT':
                            click.echo(f"Fact:{context_data['e_id']}:{attr['subject']}={attr['detail']}")
                        elif attr['type'] == 'REF':
                            click.echo(f"Ref:{context_data['e_id']}:{attr['subject']} (ID: {attr['detail']})")
                    
                    click.echo("</context>")
                    break
                else:
                    click.echo(f"Please enter a number between 1 and {len(results)}")
            except ValueError:
                click.echo("Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                click.echo("\nExiting...")
                return