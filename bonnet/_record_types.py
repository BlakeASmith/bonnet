"""Centralized record type registry for the bonnet system.

This module defines all supported record types and their properties in one place,
enabling vertical slices and making it easy to add new record types.
"""

from typing import Dict, List, Literal, Optional, Any
from dataclasses import dataclass
from enum import Enum


class RecordType(Enum):
    """Enumeration of all supported record types."""
    ENTITY = "entity"
    ATTRIBUTE = "attribute" 
    FILE = "file"
    # Example: Adding a new record type is now just one line!
    # NOTE: COMMENTED OUT FOR DEMO - uncomment to add support for notes
    # NOTE = "note"


class AttributeType(Enum):
    """Enumeration of all supported attribute types."""
    FACT = "FACT"
    REF = "REF"
    TASK = "TASK"
    RULE = "RULE"


@dataclass
class RecordTypeConfig:
    """Configuration for a record type."""
    name: str
    table_name: str
    display_name: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]
    searchable_fields: List[str]
    # For attributes, define the valid types
    valid_types: Optional[List[str]] = None


# Central registry of all record types
RECORD_TYPES: Dict[RecordType, RecordTypeConfig] = {
    RecordType.ENTITY: RecordTypeConfig(
        name="entity",
        table_name="entities",
        display_name="Entity",
        description="A knowledge entity (topic, concept, etc.)",
        required_fields=["id", "name"],
        optional_fields=["short_name"],
        searchable_fields=["name", "short_name"]
    ),
    
    RecordType.ATTRIBUTE: RecordTypeConfig(
        name="attribute",
        table_name="attributes", 
        display_name="Attribute",
        description="An attribute of an entity (fact, reference, task, rule)",
        required_fields=["id", "type", "subject", "detail"],
        optional_fields=[],
        searchable_fields=["type", "subject", "detail"],
        valid_types=[attr_type.value for attr_type in AttributeType]
    ),
    
    RecordType.FILE: RecordTypeConfig(
        name="file",
        table_name="files",
        display_name="File", 
        description="A file reference with optional content",
        required_fields=["id", "file_path"],
        optional_fields=["description", "content", "include_content"],
        searchable_fields=["file_path", "description"]
    ),
    
    # Example: Adding a new record type configuration
    # NOTE: COMMENTED OUT FOR DEMO - uncomment to add support for notes
    # RecordType.NOTE: RecordTypeConfig(
    #     name="note",
    #     table_name="notes",
    #     display_name="Note",
    #     description="A simple note or annotation",
    #     required_fields=["id", "content"],
    #     optional_fields=["title", "tags"],
    #     searchable_fields=["title", "content", "tags"]
    # )
}


def get_record_type_config(record_type: str) -> RecordTypeConfig:
    """Get configuration for a record type by name."""
    for rt in RecordType:
        if rt.value == record_type:
            return RECORD_TYPES[rt]
    raise ValueError(f"Unknown record type: {record_type}")


def get_table_name(record_type: str) -> str:
    """Get database table name for a record type."""
    return get_record_type_config(record_type).table_name


def get_valid_attribute_types() -> List[str]:
    """Get list of valid attribute types."""
    return [attr_type.value for attr_type in AttributeType]


def get_all_record_types() -> List[str]:
    """Get list of all record type names."""
    return [rt.value for rt in RecordType]


def is_valid_record_type(record_type: str) -> bool:
    """Check if a record type is valid."""
    try:
        get_record_type_config(record_type)
        return True
    except ValueError:
        return False


def is_valid_attribute_type(attr_type: str) -> bool:
    """Check if an attribute type is valid."""
    return attr_type in get_valid_attribute_types()


# Type mappings for backward compatibility
TYPE_TO_TABLE = {
    record_type.value: config.table_name 
    for record_type, config in RECORD_TYPES.items()
}