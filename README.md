# Bonnet CLI

A Python CLI tool for managing structured knowledge base (memory) and preparing highly compressed XML context.

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
- Click 8.0+
- python-dateutil 2.8+
- pydantic 2.0+

## Usage Examples

### Store a topic (master ENTITY record)
```bash
bonnet topic "The Meaning of Life" --id M1
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
<entity>
M1:The Meaning of Life
FACT:Answer:42
REF:Source:The hitchhikers guide to the galaxy
</entity>
</context>
```

## Features

- SQLite3 database with FTS5 full-text search
- Entity-based knowledge organization
- Support for custom attribute types (FACT, REF, etc.)
- Disambiguation for multiple search results
- XML context generation
- Error handling and validation