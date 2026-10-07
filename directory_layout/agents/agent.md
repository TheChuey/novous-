## role
directory_layout component of the Novous application.

## purpose
Multi-Root Security & Path Boundaries. Owns project roots, path security and the browse tree.

## boundaries
- Only interface.py is visible to other components.
- Never reaches into another component's logic, code or data modules.
