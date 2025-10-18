# Architecture

## Overview

Bonnet is a knowledge base CLI with a layered architecture that enforces separation of concerns through Pydantic models.

## Layers

```
CLI → Domain → Database
```

### CLI Layer (`cli.py`)
- Click-based commands
- Creates input models from user arguments
- Displays output using assemblers

### Domain Layer (`domain.py`)
- **Input**: Pydantic models from `_input_models.py`
- **Output**: `ContextTree` models
- Converts database dicts to typed models
- No direct CLI dependencies

### Database Layer (`database.py`)
- SQLite operations with FTS5 search
- Returns raw dicts
- No model dependencies

## Models

### `_models/`
- `ContextTree` - Root container for entities
- `Entity` - Knowledge base entity with attributes
- `Attribute` - Entity attribute (FACT, REF, etc.)

### `_input_models.py`
- Request models for domain functions
- One model per domain operation

## Supporting Modules

- `_assemblers/` - Convert `ContextTree` to output formats (XML)
- `_utils/` - CLI utilities (error handling, etc.)

## Data Flow

```
User Input → Input Model → Domain → Database
                                      ↓
Output ← Assembler ← ContextTree ← Dict
```

