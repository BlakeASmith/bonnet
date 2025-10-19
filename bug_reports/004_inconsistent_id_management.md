# Bug Report #004: Inconsistent ID Generation and Search

**Severity:** Low  
**Component:** ID Management  
**Version:** 1.0.0  
**Date:** 2024-12-19

## Description
The system generates IDs with "T" prefix by default, but the search function expects this format. However, when users provide custom IDs with different prefixes, the search breaks.

## Steps to Reproduce
1. Create entity with custom ID: `bonnet topic --id S1 "Test"`
2. Try to search: `bonnet search "S1"`
3. Result: Not found

## Expected Behavior
Should support custom ID prefixes or clearly document the supported formats.

## Actual Behavior
Only works with system-generated IDs or specific prefixes.

## Root Cause
The search function in `database.py` has hardcoded prefix checking that doesn't account for user-provided custom IDs.

## Suggested Fix
Either:
- Support all ID formats in search
- Clearly document supported ID formats
- Prevent custom ID creation with unsupported prefixes

## Workaround
Use system-generated IDs or entity names for searching.