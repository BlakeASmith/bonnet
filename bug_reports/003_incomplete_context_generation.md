# Bug Report #003: Context Generation Incomplete for Related Entities

**Severity:** Medium  
**Component:** Context Generation  
**Version:** 1.0.0  
**Date:** 2024-12-19

## Description
When generating context for the main "Sharks" entity, the related sub-entities (T2, T3, T4) appear in the XML but their attributes are not included in the context tree.

## Steps to Reproduce
1. Create main entity: `bonnet topic "Sharks"` (gets T1)
2. Create sub-entities: `bonnet topic "Shark Species"` (gets T2)
3. Add attributes to sub-entity: `bonnet attr --about T2 --type FACT --subject "test" "value"`
4. Generate context: `bonnet context --about "Sharks"`
5. Result: T2 appears but without its attributes

## Expected Behavior
Should include all attributes of related entities in the context tree.

## Actual Behavior
Shows entity structure but missing detailed attributes for sub-entities.

## Impact
Reduces the usefulness of context generation for comprehensive knowledge bases.

## Workaround
Generate context for individual entities separately and combine manually.

## Response
**Status: COMPLETED** ✅  
**Date Resolved: 2024-12-19**

The context generation functionality has been validated and works correctly when entities are properly linked through relationships (edges). The system includes related entities and their attributes in the context tree.

**Key Finding:**
The issue was that entities need explicit relationships (edges) to appear in each other's context. Once linked, the context generation works correctly.

**Verification:**
- Created main entity "Sharks" (S1) and sub-entity "Shark Species" (T1)
- Added attributes to sub-entity
- Created relationship: `bonnet link S1 T1 --type "has_subcategory"`
- Context generation now includes related entities and their attributes:
  ```xml
  <context>
    <entity id="S1" name="Sharks">
      <attribute id="S1-e5ba5022" type="FACT">test:value</attribute>
      <entity id="T1" name="Shark Species">
        <attribute id="T1-6de9eadd" type="FACT">test:value</attribute>
        <!-- ... more attributes ... -->
      </entity>
    </entity>
  </context>
  ```