# Pydantic Knowledge Base Documentation

This document contains comprehensive information about Python development using Pydantic, generated from a structured knowledge base.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Data Validation](#data-validation)
3. [Models and Fields](#models-and-fields)
4. [Serialization](#serialization)
5. [Settings Management](#settings-management)
6. [Advanced Features](#advanced-features)
7. [Integration Patterns](#integration-patterns)
8. [Best Practices](#best-practices)
9. [Performance Optimization](#performance-optimization)
10. [Code Examples](#code-examples)
11. [Common Patterns](#common-patterns)

---

## Core Concepts

**Definition**: Pydantic is a data validation library for Python that uses Python type annotations to validate data and provide clear error messages.

**Key Features**:
- Type validation
- Automatic serialization/deserialization
- Clear error messages
- IDE support
- Performance optimization

**Main Use Cases**:
- API development
- Data parsing
- Configuration management
- Database models
- Data validation in Python applications

**Version**: Pydantic v2 is the current major version with significant performance improvements and new features.

---

## Data Validation

**Core Principle**: Pydantic validates data using Python type hints and provides detailed error messages when validation fails.

**Validation Types**: Built-in validators for str, int, float, bool, datetime, UUID, EmailStr, and custom types.

**Error Handling**: ValidationError provides detailed information about what went wrong and where in the data structure.

**Custom Validators**: Use `@field_validator` and `@model_validator` decorators to create custom validation logic.

---

## Models and Fields

**BaseModel**: BaseModel is the main class that all Pydantic models inherit from, providing validation and serialization capabilities.

**Field Types**: Fields can be defined with type hints, default values, Field() function for constraints, and validation rules.

**Field Constraints**: Use Field() with min_length, max_length, regex, gt, lt, ge, le for validation constraints.

**Optional Fields**: Use Optional[Type] or Type | None for optional fields, with default=None or custom defaults.

---

## Serialization

**JSON Serialization**: Use `.model_dump()` to convert models to dictionaries and `.model_dump_json()` for JSON strings.

**Model Creation**: Use ModelClass(**data) or ModelClass.model_validate(data) to create instances from dictionaries.

**Serialization Options**: Use exclude, include, and by_alias parameters to control what fields are serialized.

**Aliases**: Use Field(alias='name') or model_config['alias_generator'] to customize field names in serialization.

---

## Settings Management

**BaseSettings**: BaseSettings class provides automatic loading of settings from environment variables, .env files, and other sources.

**Environment Variables**: Settings are automatically loaded from environment variables with case-insensitive matching.

**Configuration Sources**: Supports .env files, environment variables, and custom sources with priority ordering.

**Nested Settings**: Use nested models for complex configuration structures with automatic validation.

---

## Advanced Features

**Field Validators**: Use `@field_validator` decorator to create custom validation logic for individual fields.

**Model Validators**: Use `@model_validator` decorator for validation that requires access to multiple fields.

**Generic Models**: Use Generic[TypeVar] to create reusable models with type parameters.

**Root Validators**: Use `@model_validator(mode='before')` for validation before field validation occurs.

---

## Integration Patterns

**FastAPI Integration**: Pydantic models are the foundation of FastAPI for request/response validation and automatic API documentation.

**Database Integration**: Use with SQLAlchemy, Tortoise ORM, or other ORMs for type-safe database operations.

**API Development**: Perfect for REST APIs, GraphQL, and microservices with automatic request/response validation.

**Data Processing**: Use for ETL pipelines, data transformation, and ensuring data quality in Python applications.

---

## Best Practices

**Model Design**: Keep models focused, use composition over inheritance, and prefer explicit field definitions.

**Validation Strategy**: Use built-in validators when possible, create custom validators for complex business logic.

**Error Handling**: Always handle ValidationError exceptions and provide meaningful error messages to users.

**Performance**: Use model_config for performance tuning, avoid unnecessary validation, and consider caching.

---

## Performance Optimization

**Model Config**: Use model_config to optimize performance with validate_assignment, arbitrary_types_allowed, and other options.

**Validation Modes**: Use mode='json' for faster JSON parsing, mode='python' for Python object validation.

**Caching**: Pydantic v2 includes built-in caching for validators and serializers to improve performance.

**Memory Usage**: Use __slots__ and avoid storing large objects in model instances to reduce memory footprint.

---

## Code Examples

### Basic Model
```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    email: str
    age: int = Field(gt=0, le=120)
```

### Validation Example
```python
user = User(name='John', email='john@example.com', age=25)
print(user.model_dump())
```

### Custom Validator
```python
@field_validator('email')
def validate_email(cls, v):
    return v.lower()
```

### Settings Example
```python
class Settings(BaseSettings):
    api_key: str
    debug: bool = False
    
    class Config:
        env_file = '.env'
```

---

## Common Patterns

**API Request/Response**: Use separate models for request and response data with different validation rules.

**Nested Models**: Create complex data structures by nesting Pydantic models for hierarchical data.

**Union Types**: Use Union[Type1, Type2] or Type1 | Type2 for fields that can accept multiple types.

**Model Inheritance**: Extend base models to create specialized versions with additional fields or validation.

---

## Knowledge Base Structure

This knowledge base is organized using a graph-based structure where:

- **Entities** represent main topics (P1-P11)
- **Attributes** contain specific facts and information
- **Relationships** connect related concepts
- **Search** allows finding information across all topics
- **Context Generation** provides comprehensive information about related topics

The knowledge base can be queried using the Bonnet CLI tool to get specific information, search across all content, or generate comprehensive context about any Pydantic-related topic.

---

*Generated from Pydantic Knowledge Base using Bonnet CLI*