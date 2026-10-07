## role
configuration component of the Novous application.

## purpose
Models & Environment Management. Owns model discovery, models.json and engine configuration.

## boundaries
- Only interface.py is visible to other components.
- Never reaches into another component's logic, code or data modules.
