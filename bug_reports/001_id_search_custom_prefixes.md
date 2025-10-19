# Bug Report #001: ID Search Not Working for Custom Prefixes

**Severity:** Medium  
**Component:** CLI Search Functionality  
**Version:** 1.0.0  
**Date:** 2024-12-19

## Description
The CLI search function fails to find entities with custom ID prefixes (e.g., "S1", "S2") that don't start with the expected prefixes ('T', 'A', 'F').

## Steps to Reproduce
1. Create an entity with custom ID: `bonnet topic --id S1 "Sharks"`
2. Try to search by ID: `bonnet search "S1"`
3. Result: "No records found matching 'S1'"

## Expected Behavior
Should find the entity with ID "S1" when searching by exact ID.

## Actual Behavior
Returns "No records found matching 'S1'" even though the entity exists.

## Root Cause
In `database.py` line 794, the search function only looks for IDs starting with ('T', 'A', 'F') or containing '-':
```python
if query.startswith(('T', 'A', 'F')) or '-' in query:
```

## Suggested Fix
Modify the condition to be more flexible or add support for custom prefixes.

## Workaround
Use entity names instead of custom IDs for searching.