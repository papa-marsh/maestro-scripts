from collections.abc import Callable
from enum import StrEnum, auto
from functools import wraps
from typing import Any

from maestro.integrations.redis import RedisClient
from maestro.utils.dates import local_now
from maestro.utils.logging import log

GATE_CACHE_PREFIX = "GATE"


class Gate(StrEnum):
    CRITICAL_DOOR_NOTIFS = auto()
    NOTIF_ON_EMILY_ZONE_CHANGE = auto()
    NOTIF_ON_MARSHALL_ZONE_CHANGE = auto()


class GateManager:
    """Manages gate state in Redis for dynamically enabling/disabling functions"""

    redis = RedisClient()

    @classmethod
    def _build_gate_key(cls, gate: Gate) -> str:
        return cls.redis.build_key(GATE_CACHE_PREFIX, gate)

    @classmethod
    def is_open(cls, gate: Gate) -> bool:
        """Check cache to see if gate key is present (not set = gate open)"""
        key = cls._build_gate_key(gate)
        state = cls.redis.get(key)

        return state is None

    @classmethod
    def open(cls, gate: Gate) -> None:
        """Open gate (enable function)"""
        key = cls._build_gate_key(gate)
        cls.redis.delete(key)
        log.info("Gate opened", gate=gate)

    @classmethod
    def close(cls, gate: Gate, ttl_seconds: int) -> None:
        """Close gate (disable function)"""
        key = cls._build_gate_key(gate)
        value = local_now().isoformat()
        cls.redis.set(key=key, value=value, ttl_seconds=ttl_seconds)
        log.info("Gate closed", gate=gate)


def gate_check_needed(gate: Gate) -> Callable:
    """
    Decorator to add dynamic enable/disable capability to a function.

    The decorated function will only execute if the gate is open. Gates are
    open by default, and their state is persisted in Redis.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not GateManager.is_open(gate):
                log.info(
                    "Function execution skipped - gate closed",
                    gate=gate,
                    function=func.__name__,
                )
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator
