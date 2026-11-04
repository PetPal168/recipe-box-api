# Security baseline – recipe API
Date: 2026-11-04

## Anonymous capabilities

- GET /recipes/1 → 200 OK, returns full recipe details (**no identity or permissions checked**)
- PUT /recipes/1 → 200 OK, allows **any anonymous user to overwrite existing recipe data** (no identity or authorization checked)
- DELETE /recipes/1 → 200 OK, recipe is removed; subsequent GET /recipes/1 → 404 (**anonymous user can delete recipes**)

## Summary

- The API returns correct data and success codes to completely anonymous callers.
- No identity or permissions are checked before reading, updating, or deleting recipes.
- Hiding or not linking the routes (like /recipes/1) would not protect them once an attacker discovers the URL.