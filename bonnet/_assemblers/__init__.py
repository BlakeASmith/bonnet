from typing import Protocol, Union

from .._models import Entity, ContextTree, KnowledgeGraphSearchResult, SearchResult, Attribute


class Assembler(Protocol):
    def __call__(self, context: Union[ContextTree, KnowledgeGraphSearchResult]) -> str:
        """Assemble a context into a string"""
        ...


def xml_assembler() -> Assembler:
    """Create an XML assembler that converts ContextTree or KnowledgeGraphSearchResult to XML format."""
    
    def assemble_entity(entity: Entity) -> str:
        # Group attributes by type
        attributes_by_type = {}
        for attr in entity.attributes:
            tag_name = attr.type.lower()
            if tag_name not in attributes_by_type:
                attributes_by_type[tag_name] = []
            attributes_by_type[tag_name].append(attr)
        
        lines = [f"<entity id=\"{entity.id}\">"]
        if entity.description:
            lines.append(f"  <description>{entity.description}</description>")
        if entity.tags:
            lines.append(f"  <tags>{entity.tags}</tags>")
        if entity.file_path:
            lines.append(f"  <file_path>{entity.file_path}</file_path>")
        
        for tag_name, attrs in attributes_by_type.items():
            for attr in attrs:
                lines.append(f"  <{tag_name}>{attr.subject}:{attr.detail}</{tag_name}>")
        lines.append("</entity>")
        
        return '\n'.join(lines)
    
    def assemble_attribute(attribute: Attribute) -> str:
        return f"<attribute id=\"{attribute.id}\" type=\"{attribute.type}\">{attribute.subject}:{attribute.detail}</attribute>"
    
    def assemble_search_result(result: SearchResult) -> str:
        if result.source == 'node':
            return f"<search_result type=\"node\" node_id=\"{result.node_id}\" table=\"{result.table_name}\">{result.searchable_content}</search_result>"
        else:  # edge
            return f"<search_result type=\"edge\" edge_id=\"{result.edge_id}\" from=\"{result.from_node_id}\" to=\"{result.to_node_id}\" edge_type=\"{result.edge_type}\">{result.searchable_content}</search_result>"
    
    def assemble(context: Union[ContextTree, KnowledgeGraphSearchResult]) -> str:
        if isinstance(context, ContextTree):
            return '\n'.join([
                f"<context>",
                    *[
                        line for entity 
                        in context.entities if isinstance(entity, Entity) 
                        for line in assemble_entity(entity).splitlines()
                    ],
                f"</context>"
            ])
        else:  # KnowledgeGraphSearchResult
            lines = ["<knowledge_graph_search>"]
            
            if context.search_results:
                lines.append("  <search_results>")
                for result in context.search_results:
                    lines.append(f"    {assemble_search_result(result)}")
                lines.append("  </search_results>")
            
            if context.related_records:
                lines.append("  <related_records>")
                for record in context.related_records:
                    if isinstance(record, Entity):
                        for line in assemble_entity(record).splitlines():
                            lines.append(f"    {line}")
                    elif isinstance(record, Attribute):
                        lines.append(f"    {assemble_attribute(record)}")
                lines.append("  </related_records>")
            
            lines.append("</knowledge_graph_search>")
            return '\n'.join(lines)
    
    return assemble