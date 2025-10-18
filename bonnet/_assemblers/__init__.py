from typing import Protocol

from .._models import Entity, ContextTree


class Assembler(Protocol):
    def __call__(self, context: ContextTree) -> str:
        """Assemble a context into a string"""
        ...


def xml_assembler() -> Assembler:
    """Create an XML assembler that converts ContextTree to XML format."""
    
    def assemble_entity(entity: Entity) -> str:
        lines = [
            f"<entity id=\"{entity.e_id}\">",
            f"{entity.entity_name}",
            *[f"{x.type}:{x.subject}:{x.detail}" for x in entity.attributes],
            f"</entity>"
        ]
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