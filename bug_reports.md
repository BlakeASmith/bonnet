# Bonnet CLI Bug Reports

## Bug Report #1: ID Search Not Working for Custom Prefixes

**Severity:** Medium  
**Component:** CLI Search Functionality  
**Version:** 1.0.0

### Description
The CLI search function fails to find entities with custom ID prefixes (e.g., "S1", "S2") that don't start with the expected prefixes ('T', 'A', 'F').

### Steps to Reproduce
1. Create an entity with custom ID: `bonnet topic --id S1 "Sharks"`
2. Try to search by ID: `bonnet search "S1"`
3. Result: "No records found matching 'S1'"

### Expected Behavior
Should find the entity with ID "S1" when searching by exact ID.

### Actual Behavior
Returns "No records found matching 'S1'" even though the entity exists.

### Root Cause
In `database.py` line 794, the search function only looks for IDs starting with ('T', 'A', 'F') or containing '-':
```python
if query.startswith(('T', 'A', 'F')) or '-' in query:
```

### Suggested Fix
Modify the condition to be more flexible or add support for custom prefixes.

---

## Bug Report #2: Ambiguous Search Results Not Handled Gracefully

**Severity:** Low  
**Component:** CLI Attribute Command  
**Version:** 1.0.0

### Description
When multiple entities match a search query, the CLI shows all matches but doesn't provide a way to select one programmatically, making it impossible to use in scripts.

### Steps to Reproduce
1. Create multiple entities with similar names: `bonnet topic "Sharks"`, `bonnet topic "Shark Species"`
2. Try to add attribute: `bonnet attr --about "Sharks" --type FACT --subject "test" "value"`
3. Result: Shows multiple matches and asks user to be more specific

### Expected Behavior
Should either:
- Allow specifying which match to use (e.g., by index)
- Have a flag to auto-select the first match
- Provide a way to disambiguate programmatically

### Actual Behavior
Shows all matches and exits with error, requiring manual intervention.

### Workaround
Use exact entity names or create unique identifiers.

---

## Bug Report #3: Context Generation Incomplete for Related Entities

**Severity:** Medium  
**Component:** Context Generation  
**Version:** 1.0.0

### Description
When generating context for the main "Sharks" entity, the related sub-entities (T2, T3, T4) appear in the XML but their attributes are not included in the context tree.

### Steps to Reproduce
1. Create main entity: `bonnet topic "Sharks"` (gets T1)
2. Create sub-entities: `bonnet topic "Shark Species"` (gets T2)
3. Add attributes to sub-entity: `bonnet attr --about T2 --type FACT --subject "test" "value"`
4. Generate context: `bonnet context --about "Sharks"`
5. Result: T2 appears but without its attributes

### Expected Behavior
Should include all attributes of related entities in the context tree.

### Actual Behavior
Shows entity structure but missing detailed attributes for sub-entities.

### Impact
Reduces the usefulness of context generation for comprehensive knowledge bases.

---

## Bug Report #4: Inconsistent ID Generation and Search

**Severity:** Low  
**Component:** ID Management  
**Version:** 1.0.0

### Description
The system generates IDs with "T" prefix by default, but the search function expects this format. However, when users provide custom IDs with different prefixes, the search breaks.

### Steps to Reproduce
1. Create entity with custom ID: `bonnet topic --id S1 "Test"`
2. Try to search: `bonnet search "S1"`
3. Result: Not found

### Expected Behavior
Should support custom ID prefixes or clearly document the supported formats.

### Actual Behavior
Only works with system-generated IDs or specific prefixes.

### Suggested Fix
Either:
- Support all ID formats in search
- Clearly document supported ID formats
- Prevent custom ID creation with unsupported prefixes

---

## Bug Report #5: Context Generation Returns Empty for Individual Entities

**Severity:** Medium  
**Component:** Context Generation  
**Version:** 1.0.0

### Description
When generating context for individual entities by ID (e.g., T2, T3, T4), the command returns "No entities found" even though the entities exist.

### Steps to Reproduce
1. Create entity: `bonnet topic "Shark Species"` (gets T2)
2. Add attributes: `bonnet attr --about T2 --type FACT --subject "test" "value"`
3. Generate context: `bonnet context --about T2`
4. Result: "No entities found for query: T2"

### Expected Behavior
Should generate context for the entity T2 with its attributes.

### Actual Behavior
Returns "No entities found" message.

### Workaround
Use entity name instead of ID: `bonnet context --about "Shark Species"`

---

## Bug Report #6: Missing Error Handling for Invalid Attribute Types

**Severity:** Low  
**Component:** Attribute Storage  
**Version:** 1.0.0

### Description
The CLI doesn't validate attribute types before attempting to store them, potentially leading to database errors.

### Steps to Reproduce
1. Try to create attribute with invalid type: `bonnet attr --about T1 --type INVALID --subject "test" "value"`
2. Result: May cause database error or unclear error message

### Expected Behavior
Should validate attribute types and provide clear error messages for invalid types.

### Actual Behavior
Unclear error handling for invalid attribute types.

### Suggested Fix
Add validation for supported attribute types (FACT, REF, TASK, RULE) and provide clear error messages.

---

## Summary

The main issues are:
1. **ID search limitations** - Only works with specific prefixes
2. **Context generation incompleteness** - Missing related entity attributes
3. **Ambiguous search handling** - No programmatic way to disambiguate
4. **Inconsistent ID management** - Custom IDs not searchable
5. **Individual entity context failure** - ID-based context generation broken

These issues primarily affect the usability and completeness of the CLI tool, especially for automated workflows and comprehensive knowledge base management.