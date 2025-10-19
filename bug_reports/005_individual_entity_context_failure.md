# Bug Report #005: Context Generation Returns Empty for Individual Entities

**Severity:** Medium  
**Component:** Context Generation  
**Version:** 1.0.0  
**Date:** 2024-12-19

## Description
When generating context for individual entities by ID (e.g., T2, T3, T4), the command returns "No entities found" even though the entities exist.

## Steps to Reproduce
1. Create entity: `bonnet topic "Shark Species"` (gets T2)
2. Add attributes: `bonnet attr --about T2 --type FACT --subject "test" "value"`
3. Generate context: `bonnet context --about T2`
4. Result: "No entities found for query: T2"

## Expected Behavior
Should generate context for the entity T2 with its attributes.

## Actual Behavior
Returns "No entities found" message.

## Root Cause
The context generation function may not be properly handling ID-based queries in the search mechanism.

## Workaround
Use entity name instead of ID: `bonnet context --about "Shark Species"`

## Impact
Limits the ability to programmatically generate context for specific entities by ID.