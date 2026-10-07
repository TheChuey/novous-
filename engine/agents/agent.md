## role
engine component of the Novous application.

## purpose
Core Reasoning & Think-Loop Runtime. Runs chat turns, single agents and pipelines through the think loop.

## boundaries
- Only interface.py is visible to other components.
- Never reaches into another component's logic, code or data modules.
