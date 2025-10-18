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


def resolve_record_identifier(identifier: str, record_type: str = None) -> Optional[Dict]:
    """
    Resolve a record identifier that could be either an ID or a search query.
    
    Args:
        identifier: Either a record ID or search query
        record_type: Optional filter for specific record type
        
    Returns:
        Record data or None if not found
    """
    return domain.resolve_record_identifier(identifier, record_type)


def find_record_with_feedback(identifier: str, record_type: str = None) -> Optional[str]:
    """
    Find a record and return its ID, with user feedback for ambiguous results.
    
    Args:
        identifier: Either a record ID or search query
        record_type: Optional filter for specific record type
        
    Returns:
        Record ID if found, None otherwise
    """
    record = resolve_record_identifier(identifier, record_type)
    
    if not record:
        # Try searching for similar records
        search_results = domain.search_records(identifier, record_type)
        if search_results:
            click.echo(f"No exact match found for '{identifier}'. Did you mean one of these?", err=True)
            for i, result in enumerate(search_results[:5], 1):  # Show top 5 results
                click.echo(f"  {i}. {result['display']} ({result['type']}:{result['id']})", err=True)
            click.echo("Please be more specific or use the exact ID.", err=True)
        else:
            click.echo(f"No records found matching '{identifier}'", err=True)
        return None
    
    return record['id']


def search_and_display_records(query: str, record_type: str = None, limit: int = 10):
    """
    Search for records and display them in a user-friendly format.
    
    Args:
        query: Search query
        record_type: Optional filter for specific record type
        limit: Maximum number of results to display
    """
    results = domain.search_records(query, record_type)
    
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

