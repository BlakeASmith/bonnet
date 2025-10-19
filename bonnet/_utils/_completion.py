"""
Shell completion utilities for the bonnet CLI.
"""
import click
from typing import List, Optional

from bonnet.database import get_all_short_names
from .. import domain


def complete_record_ids(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete record IDs for parameters that accept record identifiers.
    This works for both entity IDs and search queries.
    """
    try:
        # If incomplete is empty, get recent records instead of searching
        if not incomplete:
            recent_results = domain.database.get_recent_records(5)
            return [result['id'] for result in recent_results[:5]]
        
        # Search for records that match the incomplete string
        results = domain.search_records(incomplete)
        
        # Return a list of completion items with both ID and display name
        completions = []
        for result in results[:10]:  # Limit to 10 results
            # Use the ID as the completion value
            completions.append(result['id'])
        
        return completions
    except Exception:
        # If there's any error, return empty list
        return []


def complete_entity_ids(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete entity IDs specifically for entity-related parameters.
    """
    try:
        # If incomplete is empty, get recent entities
        if not incomplete:
            recent_results = domain.database.search_records_by_type('entity', '', 5)
            return [result['id'] for result in recent_results if result.get('id')]
        
        # Search for entities that match the incomplete string
        results = domain.database.search_records_by_type('entity', incomplete, 10)
        
        # Extract entity IDs from the results
        completions = []
        for result in results:
            if result.get('id'):
                completions.append(result['id'])
        
        return completions
    except Exception:
        return []


def complete_attribute_types(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete attribute types for the --type parameter.
    """
    try:
        # Get distinct attribute types from the database
        attribute_types = domain.database.get_distinct_attribute_types()
        
        # Filter to only include valid types from the input model
        valid_types = {'FACT', 'REF', 'TASK', 'RULE'}
        valid_attribute_types = [attr_type for attr_type in attribute_types if attr_type in valid_types]
        
        # If no valid types in database, use the default valid types
        if not valid_attribute_types:
            valid_attribute_types = ['FACT', 'REF', 'TASK', 'RULE']
        
        # Filter based on incomplete string
        return [attr_type for attr_type in valid_attribute_types if attr_type.lower().startswith(incomplete.lower())]
    except Exception:
        # Fallback to valid types if database query fails
        fallback_types = ['FACT', 'REF', 'TASK', 'RULE']
        return [attr_type for attr_type in fallback_types if attr_type.lower().startswith(incomplete.lower())]


def complete_attribute_subjects(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete attribute subjects for the --subject parameter in attr command.
    """
    try:
        # Get distinct attribute subjects from the database
        subjects = domain.database.get_distinct_attribute_subjects()
        
        # Filter based on incomplete string
        return [subject for subject in subjects if subject.lower().startswith(incomplete.lower())]
    except Exception:
        # Return empty list if database query fails
        return []


def complete_edge_types(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete edge types for the --type parameter in link command.
    """
    try:
        # Get distinct edge types from the database
        edge_types = domain.database.get_distinct_edge_types()
        
        # If no types in database, provide some common defaults
        if not edge_types:
            edge_types = ['references', 'relates_to', 'depends_on', 'contains', 'part_of']
        
        # Filter based on incomplete string
        return [edge_type for edge_type in edge_types if edge_type.lower().startswith(incomplete.lower())]
    except Exception:
        # Fallback to common types if database query fails
        fallback_types = ['references', 'relates_to', 'depends_on', 'contains', 'part_of']
        return [edge_type for edge_type in fallback_types if edge_type.lower().startswith(incomplete.lower())]



def complete_search_queries(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete search queries based on existing record content.
    """
    try:
        # If incomplete is empty, get recent records for suggestions
        if not incomplete:
            recent_results = domain.database.get_recent_records(5)
            completions = []
            seen = set()
            for result in recent_results:
                if result.get('searchable_content'):
                    content = result['searchable_content']
                    snippet = content[:50].strip()
                    if snippet and snippet not in seen:
                        seen.add(snippet)
                        completions.append(snippet)
            return completions
        
        # Search for records that match the incomplete string
        results = domain.search_records(incomplete)
        
        # Extract unique searchable content snippets
        completions = []
        seen = set()
        
        for result in results[:10]:
            if result.get('searchable_content'):
                content = result['searchable_content']
                # Take first 50 characters as completion suggestion
                snippet = content[:50].strip()
                if snippet and snippet not in seen:
                    seen.add(snippet)
                    completions.append(snippet)
        
        return completions
    except Exception:
        return []


def complete_file_ids(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete file IDs specifically for file-related parameters.
    """
    try:
        # If incomplete is empty, get recent files
        if not incomplete:
            recent_results = domain.database.search_records_by_type('file', '', 5)
            return [result['id'] for result in recent_results if result.get('id')]
        
        # Search for files that match the incomplete string
        results = domain.database.search_records_by_type('file', incomplete, 10)
        
        # Extract file IDs from the results
        completions = []
        for result in results:
            if result.get('id'):
                completions.append(result['id'])
        
        return completions
    except Exception:
        return []


def complete_stored_file_paths(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete file paths from stored file records in the database.
    Returns file paths that match the incomplete string.
    """
    try:
        import sqlite3
        
        # Query database directly for efficiency
        conn = sqlite3.connect(domain.database._db_path)
        cursor = conn.cursor()
        
        if not incomplete:
            # Get recent file paths
            cursor.execute('''
                SELECT file_path FROM files 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
        else:
            # Search for file paths matching the incomplete string
            cursor.execute('''
                SELECT file_path FROM files 
                WHERE file_path LIKE ?
                ORDER BY created_at DESC 
                LIMIT 20
            ''', (f'%{incomplete}%',))
        
        completions = []
        seen = set()
        
        for (file_path,) in cursor.fetchall():
            if file_path and file_path not in seen:
                seen.add(file_path)
                completions.append(file_path)
        
        conn.close()
        return completions
    except Exception:
        return []

def complete_short_names(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete short names for the --short-name parameter in topic command.
    """
    return [short_name for short_name in get_all_short_names() if short_name.lower().startswith(incomplete.lower())]

def complete_about(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete about for the --about parameter in attr and link commands.
    """
    # Get short names that match
    short_names = [short_name for short_name in get_all_short_names() if short_name.lower().startswith(incomplete.lower())]
    
    record_ids = complete_record_ids(ctx, param, incomplete)
    
    # Combine and return unique values
    return list(set(short_names + record_ids))
    