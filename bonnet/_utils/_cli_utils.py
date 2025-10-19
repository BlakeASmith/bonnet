import click
import sys
from functools import wraps
from typing import Optional, Dict, List
from .. import domain

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


def find_record_with_feedback(identifier: str, no_interactive: bool = False) -> Optional[str]:
    """
    Find a record and return its ID, with user feedback for ambiguous results.
    
    Args:
        identifier: Either a record ID or search query
        no_interactive: If True, automatically select the first match when ambiguous
        
    Returns:
        Record ID if found, None otherwise
    """
    results = domain.search_records(identifier)
    
    if not results:
        click.echo(f"No records found matching '{identifier}'", err=True)
        return None
    
    if len(results) == 1:
        return results[0]['id']
    
    # Multiple results - handle based on options
    if no_interactive:
        click.echo(f"Multiple records found for '{identifier}'. Auto-selecting first match: {results[0]['display']} ({results[0]['type']}:{results[0]['id']})", err=True)
        return results[0]['id']
    
    # Show them and ask for clarification
    click.echo(f"Multiple records found for '{identifier}'. Did you mean one of these?", err=True)
    for i, result in enumerate(results[:5], 1):  # Show top 5 results
        click.echo(f"  {i}. {result['display']} ({result['type']}:{result['id']})", err=True)
    click.echo("Please be more specific, use the exact ID, or use --no-interactive to auto-select the first match.", err=True)
    return None


def search_and_display_records(query: str, limit: int = 10):
    """
    Search for records and display them in a user-friendly format.
    
    Args:
        query: Search query
        limit: Maximum number of results to display
    """
    results = domain.search_records(query)
    
    if not results:
        click.echo(f"No records found matching '{query}'")
        return
    
    click.echo(f"Found {len(results)} record(s) matching '{query}':")
    click.echo()
    
    for i, result in enumerate(results[:limit], 1):
        click.echo(f"{i}. {result['display']}")
        click.echo(f"   Type: {result['type']}, ID: {result['id']}")
        if result.get('searchable_content'):
            # Truncate long content
            content = result['searchable_content']
            if len(content) > 100:
                content = content[:97] + "..."
            click.echo(f"   Content: {content}")
        click.echo()
    
    if len(results) > limit:
        click.echo(f"... and {len(results) - limit} more results")

