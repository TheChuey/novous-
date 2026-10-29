"""Pattern registry lookup."""

from typing import Dict, Type

from orchestration.orchestration_patterns import (
    BasePattern,
    FanOutPattern,
    RouterPattern,
    SequentialPattern,
)

_PATTERNS: Dict[str, Type[BasePattern]] = {
    "sequential": SequentialPattern,
    "fanout": FanOutPattern,
    "router": RouterPattern,
}


def get_pattern(pattern_name: str) -> BasePattern:
    key = pattern_name.lower().strip()
    pattern_cls = _PATTERNS.get(key, SequentialPattern)
    return pattern_cls()
