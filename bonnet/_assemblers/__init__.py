from typing import Protocol

from .._models import Entity, ContextTree


class Assembler(Protocol):
    def __call__(self, context: ContextTree) -> str:
        """Assemble a context into a string"""
        ...


def xml_assembler() -> Assembler:
    """Create an XML assembler that converts ContextTree to XML format."""
    
    def assemble_entity(entity: Entity) -> str:
        # Group attributes by type
        attributes_by_type = {}
        for attr in entity.attributes:
            tag_name = attr.type.lower()
            if tag_name not in attributes_by_type:
                attributes_by_type[tag_name] = []
            attributes_by_type[tag_name].append(attr)
        
        lines = []
        for tag_name, attrs in attributes_by_type.items():
            for attr in attrs:
                lines.append(f"<{tag_name} id=\"{entity.e_id}\">{attr.subject}:{attr.detail}</{tag_name}>")
        
        return '\n'.join(lines)
    
    def assemble(context: ContextTree) -> str:
        return '\n'.join([
            f"<context>",
                *[
                    line for entity 
                    in context.entities if isinstance(entity, Entity) 
                    for line in assemble_entity(entity).splitlines()
                ],
            f"</context>"
        ])
    
    return assemble