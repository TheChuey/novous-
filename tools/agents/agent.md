## role
tools component of the Novous application.

## purpose
Central AI Tool Catalog & Dispatcher. Owns the tool registry, provider binding and the @tool catalog.

## boundaries
- Only interface.py is visible to other components.
- Never reaches into another component's logic, code or data modules.
