## role
agents component of the Novous application.

## purpose
Agent Discovery, Registry & Lifecycle. Owns agent roots, loading, validation and the agent library.

## boundaries
- Only interface.py is visible to other components.
- Never reaches into another component's logic, code or data modules.
