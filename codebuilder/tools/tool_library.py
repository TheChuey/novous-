"""Custom tools promoted from the Function Testing Workbench."""


def calculate_shipping(weight_kg: float, distance_km: float) -> dict:
    """Calculate shipping fee from package weight and distance."""
    base_rate = 5.0
    cost = base_rate + (weight_kg * 1.5) + (distance_km * 0.05)
    return {
        "weight_kg": weight_kg,
        "distance_km": distance_km,
        "shipping_cost": round(cost, 2)
    }
