# Maestro Scripts

Personal Home Assistant automations built on the Maestro framework. This repo lives inside the maestro project at `scripts/` and is loaded at runtime by the framework.

## Framework

This project depends on the Maestro framework, which lives in the parent directory (`../`). Maestro's architecture, code style, type system, and testing infrastructure are documented in `../AGENTS.md` -- read it for full context on how the framework works. Everything in that file (code style, naming conventions, type annotations, error handling, logging, etc.) applies here too.

## Build / Lint / Test Commands

All commands are run from the **parent maestro directory** (`../`), not from `scripts/`.

```bash
# Run all script tests
pytest scripts

# Run tests for a specific domain
pytest scripts/home/tests

# Run a single test file
pytest scripts/home/tests/test_thermostat.py

# Run a single test function
pytest scripts/home/tests/test_thermostat.py::test_check_thermostat_hold

# Run tests matching a keyword
pytest scripts -k "test_charging"

# Lint and type check (covers scripts too when run from parent)
ruff check scripts
ruff format scripts
mypy scripts
```

## Project Structure

Automations are organized into thematic directories (e.g., `home/`, `vehicles/`, `family/`). Three special directories exist at the top level:

- **`common/`** -- Shared utilities used across domains (gate system, event types, finance API, DB column types)
- **`config/`** -- Secrets and zone metadata (**gitignored** -- contains personal data)
- **`custom_domains/`** -- Domain subclasses injected into `maestro.domains` (see maestro's AGENTS.md for how this works)

New automation domains should follow this layout:
```
domain/
  __init__.py              # Empty
  models.py                # SQLAlchemy models (if domain persists data)
  queries.py               # DB or Redis query functions (if needed)
  <automation>.py          # Trigger-decorated automation functions
  tests/
    __init__.py            # Empty
    test_<automation>.py   # Tests mirroring each automation module
```

## Imports

### From Maestro (always via top-level package re-exports)

```python
from maestro.domains import ON, OFF, HOME, AWAY, UNAVAILABLE, UNKNOWN
from maestro.integrations import StateChangeEvent, FiredEvent, Domain, EntityId
from maestro.registry import person, switch, sensor, climate, binary_sensor, cover
from maestro.triggers import state_change_trigger, cron_trigger, event_fired_trigger
from maestro.utils import Notif, JobScheduler, local_now, format_duration, log
from maestro.testing import MaestroTest
```

Never import from deep submodules like `maestro.domains.entity` or `maestro.triggers.trigger_manager`. The one exception is custom domain files that must import from `maestro.domains.<module>` directly (e.g., `from maestro.domains.climate import Climate`) to avoid circular imports, since `maestro.domains.__init__` wildcard-imports from `scripts.custom_domains`.

### From Scripts (cross-package)

```python
from scripts.common.event_type import EventType, UIEvent, ui_event_trigger
from scripts.common.gates import GateManager, gate_check, Gate
from scripts.config.secrets import USER_ID_TO_PERSON, PERSON_TO_USER_ID
from scripts.custom_domains.climate import Thermostat
```

Within a domain, use relative imports for sibling modules:

```python
from .common import Nyx, Tess, get_vehicle_config
from .door_left_open import EXTERIOR_DOORS
```

## Custom Domains (`custom_domains/`)

Custom domain subclasses extend maestro's base domain classes with device-specific functionality. They are wildcard-imported into `maestro.domains` at framework startup, which allows the auto-generated registry to use them as parent classes.

The pattern:
```python
from maestro.domains.climate import Climate  # Direct module import (not package)

class Thermostat(Climate):
    class HVACMode(StrEnum):
        OFF = auto()
        COOL = auto()
        HEAT = auto()

    @override
    def set_hvac_mode(self, mode: HVACMode) -> None:  # type:ignore[override]
        self.perform_action("set_hvac_mode", hvac_mode=mode)
```

- Nested `StrEnum` classes define typed mode/preset constants
- `@override` + `# type:ignore[override]` on methods that narrow parameter types
- Export via `__all__` in `custom_domains/__init__.py` using `ClassName.__name__`

Current custom domains: `Thermostat`, `BathroomFloor`, `TeslaHVAC`, `SonosSpeaker`, `SprinklerZone`, `ZoneExtended`, `GoogleCalendar`, `Marshall`, `Emily`

## Automation Patterns

### Trigger Decorators

```python
# State change -- single entity with filter
@state_change_trigger(switch.space_heater, to_state=ON)
def handler(state_change: StateChangeEvent) -> None: ...

# State change -- spread a list of entities
@state_change_trigger(*EXTERIOR_DOORS, to_state=ON)
def handler(state_change: StateChangeEvent) -> None: ...

# Cron -- daily at specific hour
@cron_trigger(hour=19)
def nightly_check() -> None: ...

# Cron -- stacked for multiple schedules
@cron_trigger(hour=8)
@cron_trigger(hour=20)
def check_twice_daily() -> None: ...

# Custom event
@event_fired_trigger(EventType.BATHROOM_FLOOR)
def handler(event: FiredEvent) -> None: ...

# HA lifecycle (runs on HA restart AND maestro restart)
@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize() -> None: ...
```

Functions can accept event parameters or take no parameters -- the framework uses `inspect.signature()` to match.

### Guard Clauses

Always guard against `UNAVAILABLE`/`UNKNOWN` states and irrelevant conditions early:

```python
if state_change.old.state == UNAVAILABLE:
    return
if not person.emily.is_home:
    return
```

### Entity State Access

Entity state is always a string. Cast for numeric comparisons:

```python
temp = float(climate.thermostat.current_temperature)
battery = int(sensor.nyx_battery.state)
```

Use convenience properties where available: `.is_on`, `.is_home`, `.friendly_name`.

### Push Notifications

```python
Notif(
    title="Alert Title",
    message="Alert message",
    priority=Notif.Priority.TIME_SENSITIVE,
    tag="unique_tag",
).send(person.marshall, person.emily)
```

### Job Scheduler (Debounce / Delayed Execution)

```python
JOB_ID = "descriptive_job_id"

# Schedule
JobScheduler().schedule_job(
    run_time=local_now() + timedelta(minutes=30),
    func=callback_function,
    func_params={"key": value},
    job_id=JOB_ID,
)

# Cancel
JobScheduler().cancel_job(JOB_ID)
```

Job IDs are module-level `SCREAMING_SNAKE_CASE` constants. `JobScheduler()` is instantiated per-use (auto-detects test mode).

### Database Models

```python
class ZoneChange(db.Model):  # type:ignore[name-defined]
    __tablename__ = "zone_change"
    __table_args__: ClassVar = {"extend_existing": True}

    person = db.Column(db.String, primary_key=True, nullable=False)
    arrived_at = db.Column(TZDateTime, primary_key=True, nullable=False)
```

- `# type:ignore[name-defined]` on `db.Model` (dynamic base class)
- `__tablename__` is explicit, `snake_case`, singular
- `__table_args__: ClassVar = {"extend_existing": True}` required
- Use `TZDateTime` from `scripts.common.db_types` for timezone-aware datetime columns
- `__repr__` for debug output

### Redis Queries

```python
redis = entity.state_manager.redis_client
key = redis.build_key(PREFIX, identifier)
redis.set(key=key, value=value.isoformat(), ttl_seconds=IntervalSeconds.TWO_WEEKS)
result = redis.get(key=key)
```

Key prefixes are module-level constants. TTLs use `IntervalSeconds` enum values. Timestamps serialize as ISO strings.

## Testing

### Structure

- Test files mirror automation modules: `test_thermostat.py` tests `thermostat.py`
- All test functions are module-level (no test classes)
- Every test takes `mt: MaestroTest` as its first parameter (except pure logic tests)
- Return type always `-> None`
- Import the script module via relative import to register its triggers:
  ```python
  from .. import thermostat
  ```

### Pattern: Setup / Trigger / Assert

```python
def test_high_charge_limit(mt: MaestroTest) -> None:
    # Setup
    mt.set_state(binary_sensor.nyx_charger, OFF)
    mt.set_state(number.nyx_charge_limit, str(DEFAULT_CHARGE_LIMIT))

    # Trigger
    mt.trigger_state_change(binary_sensor.nyx_charger, new=ON)

    # Assert
    mt.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)
```

### Multi-Scenario Tests

Use `mt.clear_action_calls()` between scenarios within a single test:

```python
def test_meeting_notifications(mt: MaestroTest) -> None:
    # Scenario 1: Emily away -- no notification
    mt.set_state(person.emily, AWAY)
    mt.trigger_state_change(maestro.meeting_active, new=ON)
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    # Scenario 2: Emily arrives -- notification sent
    mt.trigger_state_change(person.emily, new=HOME)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
    mt.clear_action_calls()
```

### Key Assertions

```python
mt.assert_action_called(Domain.LIGHT, "turn_on", entity_id=light.bedroom.id)
mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)
mt.assert_job_scheduled(JOB_ID, target_function)
mt.assert_job_not_scheduled(JOB_ID)
mt.assert_state(maestro.meeting_active, ON)
mt.assert_entity_exists(maestro.meeting_active)
```

Notifications are asserted as action calls on `Domain.NOTIFY` with the person's `notify_action_name`.

### Calling Non-Triggered Functions

Test helper/utility functions by calling them directly:

```python
bathroom_floor.reset_floor_to_auto()
mt.assert_action_called(Domain.CLIMATE, "set_preset_mode")
```

### Time Mocking

```python
with mt.mock_datetime_as(local_now().replace(hour=3, minute=0)):
    mt.trigger_state_change(...)
    mt.assert_action_called(...)
```

## Config (`config/`)

- `secrets.py` -- User ID mappings (`USER_ID_TO_PERSON`, `PERSON_TO_USER_ID`), API tokens, financial constants. **Gitignored.**
- `zones.py` -- `ZoneMetadata` dataclass and `zone_metadata_registry` dict mapping zone names to rich metadata (short names, debounce durations, region flags, geographic groupings). **Gitignored.**

Both are gitignored because they contain personal data. If you need to modify them, note that changes won't appear in git status.
