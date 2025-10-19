"""
Shell completion utilities for the bonnet CLI.
"""
import click
from typing import List, Optional
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


def complete_file_paths(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
    """
    Complete file paths for file-related parameters.
    """
    import os
    import glob
    
    # If incomplete is empty, start from current directory
    if not incomplete:
        incomplete = "./"
    
    # Handle tilde expansion
    incomplete = os.path.expanduser(incomplete)
    
    # Get the directory and pattern
    if os.path.isdir(incomplete):
        # If it's a directory, add a trailing slash and glob for all files
        pattern = os.path.join(incomplete, "*")
    else:
        # If it's a file pattern, use it as is
        pattern = incomplete + "*"
    
    try:
        # Get matching files and directories
        matches = glob.glob(pattern)
        
        # Convert to relative paths and add directories with trailing slash
        completions = []
        for match in matches:
            if os.path.isdir(match):
                completions.append(match + "/")
            else:
                completions.append(match)
        
        return completions[:20]  # Limit to 20 results
    except Exception:
        return []


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