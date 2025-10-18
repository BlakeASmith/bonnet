# Bonnet CLI

A Python CLI tool for managing structured knowledge base (memory) and preparing highly compressed XML context.

## Installation

```bash
pip install -e .
```

## Dependencies

- Python 3.7+
- Click 8.0+
- python-dateutil 2.8+

## Usage

### Store a topic (master ENTITY record)
```bash
bonnet topic "The Meaning of Life" --id M1
```

### Store attributes
```bash
# Store a fact
bonnet fact "Answer=42" --about M1

# Store a reference
bonnet ref "The hitchhikers guide to the galaxy" --about M1 --id R1
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
M1:"The Meaning of Life"
Fact:M1:Answer=42
Ref:M1:The hitchhikers guide to the galaxy (ID: R1)
</context>
```

## Features

- SQLite3 database with FTS5 full-text search
- Entity-based knowledge organization
- Support for facts and references
- Disambiguation for multiple search results
- Compressed XML context generation
- Error handling and validation