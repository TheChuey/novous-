## role
project_manager component of the Novous application.

## purpose
Editor Operations & Filesystem Authority. Owns editor sessions, file IO, the event bus and HTTP editor API.

## boundaries
- Only interface.py is visible to other components.
- Never reaches into another component's logic, code or data modules.
