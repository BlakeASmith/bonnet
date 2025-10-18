from typing import Protocol, Union

from _models import Entity, ContextTree, SearchResult, Attribute
from typing import List


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
    
    return assemble
    
    
def assemble(context: ContextTree) -> str:
    """Assemble a ContextTree into XML format, recursively traversing the graph structure."""
    
    def assemble_attribute(attribute: Attribute) -> str:
        return f"<attribute id=\"{attribute.id}\" type=\"{attribute.type}\">{attribute.subject}:{attribute.detail}</attribute>"
    
    lines = ["<context>"]
    
    # Recursively assemble the tree structure
    def assemble_tree(tree: ContextTree, indent_level: int = 1) -> List[str]:
        result_lines = []
        indent = "  " * indent_level
        
        # Render based on the type
        if tree.type == 'entity' and tree.data:
            entity = tree.data
            result_lines.append(f"{indent}<entity id=\"{entity.id}\">")
            result_lines.append(f"{indent}  <name>{entity.name}</name>")
            
            # Add attributes if any
            if entity.attributes:
                for attr in entity.attributes:
                    result_lines.append(f"{indent}  {assemble_attribute(attr)}")
            
            # Add edges as relationships
            if tree.edges:
                for edge in tree.edges:
                    result_lines.append(f"{indent}  <relationship type=\"{edge.edge_type}\" to=\"{edge.to_node_id}\">")
                    if edge.searchable_content:
                        result_lines.append(f"{indent}    <content>{edge.searchable_content}</content>")
                    result_lines.append(f"{indent}  </relationship>")
            
            result_lines.append(f"{indent}</entity>")
        
        elif tree.type == 'attribute' and tree.data:
            attribute = tree.data
            result_lines.append(f"{indent}{assemble_attribute(attribute)}")
        
        # Recursively process children
        for child in tree.children:
            child_lines = assemble_tree(child, indent_level + 1)
            result_lines.extend(child_lines)
        
        return result_lines
    
    # Assemble the tree structure
    tree_lines = assemble_tree(context)
    lines.extend(tree_lines)
    
    lines.append("</context>")
    return '\n'.join(lines)
    
    return assemble