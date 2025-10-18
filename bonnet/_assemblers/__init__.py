from typing import Protocol, Union

from .._models import Entity, ContextTree, Group


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
    
    def assemble_group(group: Group) -> str:
        lines = [
            f"<group id=\"{group.group_id}\">",
            f"<name>{group.group_name}</name>",
        ]
        
        if group.description:
            lines.append(f"<description>{group.description}</description>")
        
        # Add entity references
        if group.entity_references:
            lines.append("<entity_references>")
            for ref in group.entity_references:
                rel_type = f" relationship=\"{ref.relationship_type}\"" if ref.relationship_type else ""
                lines.append(f"<entity_ref e_id=\"{ref.e_id}\"{rel_type}/>")
            lines.append("</entity_references>")
        
        # Add nested entities and groups
        if group.entities:
            lines.append("<entities>")
            for item in group.entities:
                if isinstance(item, Entity):
                    lines.extend(assemble_entity(item).splitlines())
                elif isinstance(item, Group):
                    lines.extend(assemble_group(item).splitlines())
            lines.append("</entities>")
        
        lines.append("</group>")
        return '\n'.join(lines)
    
    def assemble_item(item: Union[Entity, Group]) -> str:
        if isinstance(item, Entity):
            return assemble_entity(item)
        elif isinstance(item, Group):
            return assemble_group(item)
        else:
            return ""
    
    def assemble(context: ContextTree) -> str:
        return '\n'.join([
            f"<context>",
                *[
                    line for item in context.entities 
                    for line in assemble_item(item).splitlines()
                ],
            f"</context>"
        ])
    
    return assemble