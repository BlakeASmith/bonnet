from typing import Protocol, Union

from .._models import Entity, ContextTree, SearchResult, Attribute


class Assembler(Protocol):
    def __call__(self, context: ContextTree) -> str:
        """Assemble a context into a string"""
        ...


def xml_assembler() -> Assembler:
    """Create an XML assembler that converts ContextTree to compact knowledge graph XML format with context root."""
    
    def assemble_entity(entity: Entity) -> str:
        # Group attributes by type
        attributes_by_type = {}
        for attr in entity.attributes:
            tag_name = attr.type.lower()
            if tag_name not in attributes_by_type:
                attributes_by_type[tag_name] = []
            attributes_by_type[tag_name].append(attr)
        
        lines = [f"<entity id=\"{entity.id}\">"]
        
        for tag_name, attrs in attributes_by_type.items():
            for attr in attrs:
                lines.append(f"  <{tag_name}>{attr.subject}:{attr.detail}</{tag_name}>")
        lines.append("</entity>")
        
        return '\n'.join(lines)
    
    def assemble_attribute(attribute: Attribute) -> str:
        return f"<attribute id=\"{attribute.id}\" type=\"{attribute.type}\">{attribute.subject}:{attribute.detail}</attribute>"
    
    
    def assemble(context: ContextTree) -> str:
        lines = ["<context>"]
        
        # Add entities from the context
        if context.entities:
            for entity in context.entities:
                if isinstance(entity, Entity):
                    for line in assemble_entity(entity).splitlines():
                        lines.append(f"  {line}")
        
        # Add related records as entities and attributes
        if context.related_records:
            for record in context.related_records:
                if isinstance(record, Entity):
                    for line in assemble_entity(record).splitlines():
                        lines.append(f"  {line}")
                elif isinstance(record, Attribute):
                    lines.append(f"  {assemble_attribute(record)}")
        
        lines.append("</context>")
        return '\n'.join(lines)
    
    return assemble