# Bug Report #006: Missing Error Handling for Invalid Attribute Types

**Severity:** Low  
**Component:** Attribute Storage  
**Version:** 1.0.0  
**Date:** 2024-12-19

## Description
The CLI doesn't validate attribute types before attempting to store them, potentially leading to database errors.

## Steps to Reproduce
1. Try to create attribute with invalid type: `bonnet attr --about T1 --type INVALID --subject "test" "value"`
2. Result: May cause database error or unclear error message

## Expected Behavior
Should validate attribute types and provide clear error messages for invalid types.

## Actual Behavior
Unclear error handling for invalid attribute types.

## Expected Attribute Types
Based on the codebase, valid types appear to be:
- FACT
- REF
- TASK
- RULE

## Suggested Fix
Add validation for supported attribute types and provide clear error messages with list of valid types.

## Impact
Poor user experience when using invalid attribute types.