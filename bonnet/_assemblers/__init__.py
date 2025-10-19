from typing import Protocol, Union

from .._models import Entity, ContextTree, SearchResult, Attribute, File
from typing import List


class Assembler(Protocol):
    def __call__(self, context: ContextTree) -> str:
        """Assemble a context into a string"""
        ...


def xml_assembler() -> Assembler:
    """Create an XML assembler that converts ContextTree to compact knowledge graph XML format with context root."""
    
    def assemble(context: ContextTree) -> str:
        """Assemble a ContextTree into XML format, following edges to render actual node types."""
        
        def assemble_attribute(attribute: Attribute) -> str:
            return f"<attribute id=\"{attribute.id}\" type=\"{attribute.type}\">{attribute.subject}:{attribute.detail}</attribute>"
        
        def assemble_file(file: File) -> str:
            return f"<file id=\"{file.id}\" path=\"{file.file_path}\">{file.description}</file>"
        
        lines = ["<context>"]
        
        # Recursively assemble the tree structure
        def assemble_tree(tree: ContextTree, indent_level: int = 1) -> List[str]:
            result_lines = []
            indent = "  " * indent_level
            
            # Render based on the type
            if tree.type == 'entity' and tree.data:
                entity = tree.data
                short_name_attr = f" short_name=\"{entity.short_name}\"" if entity.short_name else ""
                result_lines.append(f"{indent}<entity id=\"{entity.id}\" name=\"{entity.name}\"{short_name_attr}>")
                
                # Process children (which are the actual connected nodes via edges)
                for child in tree.children:
                    child_lines = assemble_tree(child, indent_level + 1)
                    result_lines.extend(child_lines)
                
                result_lines.append(f"{indent}</entity>")
            
            elif tree.type == 'attribute' and tree.data:
                attribute = tree.data
                result_lines.append(f"{indent}{assemble_attribute(attribute)}")
            
            elif tree.type == 'file' and tree.data:
                file = tree.data
                result_lines.append(f"{indent}{assemble_file(file)}")
            
            elif tree.type == 'root':
                # For root nodes, process all children
                for child in tree.children:
                    child_lines = assemble_tree(child, indent_level)
                    result_lines.extend(child_lines)
            
            return result_lines
        
        # Assemble the tree structure
        tree_lines = assemble_tree(context)
        lines.extend(tree_lines)
        
        lines.append("</context>")
        return '\n'.join(lines)
    
    return assemble