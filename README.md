# Bonnet CLI

A Python CLI tool for managing structured knowledge base (memory) and preparing highly compressed XML context using a knowledge graph architecture.

## Installation

```bash
pip install -e .
```

## Usage

The CLI can be run in two ways:
- `bonnet` (if installed and in PATH)
- `python -m bonnet` (from the project directory)

## Dependencies

- Python 3.7+
- Click 8.0.0+
- python-dateutil 2.8.0+
- pydantic 2.0.0+

## Usage Examples

### Store a topic (master ENTITY record)
```bash
# With explicit ID
bonnet topic --id M1 "The Meaning of Life"

# With auto-generated ID
bonnet topic "The Meaning of Life"
```

### Store attributes
```bash
# Store a fact
bonnet attr --about M1 --type FACT --subject "Answer" "42"

# Store a reference
bonnet attr --about M1 --type REF --subject "Source" "The hitchhikers guide to the galaxy"
```

### Search and generate context
```bash
# Search for entities and generate context
bonnet context --about M1

# Search by text (will prompt for disambiguation if multiple matches)
bonnet context --about "life"
```

## Output Format

The context command generates XML output in the following format:

```xml
<context>
  <entity id="M1">
    <name>The Meaning of Life</name>
    <relationship type="has_attribute" to="A1">
      <content>FACT:Answer:42</content>
    </relationship>
    <relationship type="has_attribute" to="A2">
      <content>REF:Source:The hitchhikers guide to the galaxy</content>
    </relationship>
  </entity>
</context>
```

## Architecture

Bonnet uses a knowledge graph architecture with:
- **Entities**: Master records representing topics or concepts
- **Attributes**: Facts, references, tasks, or rules linked to entities
- **Nodes**: Graph nodes representing both entities and attributes
- **Edges**: Relationships between nodes in the knowledge graph
- **FTS Search**: Full-text search across the knowledge base using SQLite FTS5
