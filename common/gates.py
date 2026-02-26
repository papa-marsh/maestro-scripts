from collections.abc import Callable
from datetime import datetime, timedelta
from enum import StrEnum, auto
from functools import wraps
from typing import Any

from maestro.domains import ON
from maestro.integrations import StateChangeEvent, StateManager
from maestro.registry import input_boolean, input_datetime, input_select
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import JobScheduler, local_now, log, resolve_timestamp

GATE_EXPIRY_CACHE_PREFIX = "GATE_EXPIRY"
PLACEHOLDER_OPTION = "Select a gate..."
GATE_SELECTOR_RESET_JOB_ID = "gate_selector_reset"


class Gate(StrEnum):
    CRITICAL_DOOR_NOTIFS = auto()
    NOTIF_ON_EMILY_ZONE_CHANGE = auto()
    NOTIF_ON_MARSHALL_ZONE_CHANGE = auto()


class GateManager:
    """Manages gate state in Redis for dynamically enabling/disabling functions"""

    state_manager = StateManager()
    redis = state_manager.redis_client

    @classmethod
    def _build_gate_key(cls, gate: Gate) -> str:
        return cls.redis.build_key(GATE_EXPIRY_CACHE_PREFIX, gate)

    @classmethod
    def is_closed(cls, gate: Gate) -> datetime | None:
        """
        Check cache to see if gate key is present (not set = gate open).
        Returns the expiry datetime if closed, otherwise None.
        """
        key = cls._build_gate_key(gate)
        state = cls.redis.get(key)

        return datetime.fromisoformat(state) if state else None

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
        value = (local_now() + timedelta(seconds=ttl_seconds)).isoformat()
        cls.redis.set(key, value, ttl_seconds)
        log.info("Gate closed", gate=gate)

    @classmethod
    def get_gates(cls) -> dict[str, datetime | None]:
        return {gate: cls.is_closed(gate) for gate in sorted(Gate)}


def gate_check(gate: Gate) -> Callable:
    """
    Decorator to add dynamic enable/disable capability to a function.

    The decorated function will only execute if the gate is open. Gates are
    open by default, and their state is persisted in Redis.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not GateManager.is_closed(gate):
                log.info(
                    "Function execution skipped - gate closed",
                    gate=gate,
                    function=func.__name__,
                )
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


@maestro_trigger(MaestroEvent.STARTUP)
@hass_trigger(HassEvent.STARTUP)
def reset_gate_selector() -> None:
    gates_dict = GateManager.get_gates()
    options = [PLACEHOLDER_OPTION, *list(gates_dict.keys())]

    input_select.gate_selector.set_options(options)


@state_change_trigger(
    input_select.gate_selector,
    input_boolean.gate_state,
    input_datetime.gate_expiry,
)
def schedule_reset_timeout() -> None:
    if input_select.gate_selector.state == PLACEHOLDER_OPTION:
        return

    JobScheduler().schedule_job(
        run_time=local_now() + timedelta(minutes=2),
        func=reset_gate_selector,
        job_id=GATE_SELECTOR_RESET_JOB_ID,
    )


@state_change_trigger(input_select.gate_selector)
def select_gate(state_change: StateChangeEvent) -> None:
    gate = state_change.new.state
    tomorrow_morning = (local_now() + timedelta(days=1)).replace(hour=7, minute=0, second=0)

    if gate == PLACEHOLDER_OPTION:
        input_boolean.gate_state.turn_off()
        input_datetime.gate_expiry.set_datetime(tomorrow_morning)
        return

    gate = Gate(gate)
    if expiry := GateManager.is_closed(gate):
        input_boolean.gate_state.turn_off()
        input_datetime.gate_expiry.set_datetime(expiry)
        return

    input_boolean.gate_state.turn_on()
    input_datetime.gate_expiry.set_datetime(tomorrow_morning)


@state_change_trigger(input_boolean.gate_state)
def toggle_gate(state_change: StateChangeEvent) -> None:
    gate = input_select.gate_selector.state
    if gate == PLACEHOLDER_OPTION:
        if state_change.new.state == ON:
            input_boolean.gate_state.turn_off()
        return

    gate = Gate(gate)
    if state_change.new.state == ON:
        GateManager.open(gate)
        return

    expiry = resolve_timestamp(input_datetime.gate_expiry.state)
    ttl_seconds = int((expiry - local_now()).total_seconds())
    GateManager.close(gate, ttl_seconds)


@state_change_trigger(input_datetime.gate_expiry)
def set_gate_expiry(state_change: StateChangeEvent) -> None:
    gate = input_select.gate_selector.state
    if gate == PLACEHOLDER_OPTION:
        return

    gate = Gate(gate)
    if not GateManager.is_closed(gate):
        return

    expiry = resolve_timestamp(state_change.new.state)
    ttl_seconds = int((expiry - local_now()).total_seconds())
    GateManager.close(gate, ttl_seconds)
