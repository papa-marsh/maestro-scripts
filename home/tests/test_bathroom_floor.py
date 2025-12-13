from datetime import timedelta

from maestro.domains import OFF
from maestro.integrations.home_assistant.domain import Domain
from maestro.registry import climate, person
from maestro.testing import MaestroTest
from maestro.utils.dates import local_now
from scripts.config.secrets import PERSON_TO_USER_ID
from scripts.custom_domains import BathroomFloor
from scripts.home.bathroom_floor import (
    AUTO_SHUTOFF_JOB_ID,
    HEAT_TEMPERATURE,
    TEMPERATURE_CHECK_JOB_ID,
    TURN_OFF_HEAT_JOB_ID,
)

from .. import bathroom_floor


def test_heat_bathroom_floor_schedules_jobs(maestro_test: MaestroTest) -> None:
    """Test that triggering bathroom_floor event schedules the correct jobs"""
    # Setup: Set initial state
    maestro_test.set_state(climate.bathroom_floor_thermostat, OFF)
    maestro_test.set_state(person.marshall, "home")

    # Trigger the event (simulating someone pressing the button)
    maestro_test.trigger_event("bathroom_floor", user_id=PERSON_TO_USER_ID[person.marshall])

    # Assert: Temperature was set to heat mode
    maestro_test.assert_action_called(
        Domain.CLIMATE,
        "set_temperature",
        entity_id="climate.bathroom_floor_thermostat",
        target_temp=HEAT_TEMPERATURE,
    )

    # Assert: Two jobs were scheduled
    jobs = maestro_test.get_scheduled_jobs()
    assert len(jobs) == 2

    # Assert: Temperature check job was scheduled for 1 minute from now
    maestro_test.assert_job_scheduled(TEMPERATURE_CHECK_JOB_ID)
    temp_check_job = maestro_test.get_scheduled_job(TEMPERATURE_CHECK_JOB_ID)
    assert temp_check_job.func.__name__ == "check_floor_temp"
    assert temp_check_job.kwargs["caller"] == person.marshall

    # Assert: Turn off heat job was scheduled for HEAT_DURATION
    maestro_test.assert_job_scheduled(TURN_OFF_HEAT_JOB_ID)
    turn_off_job = maestro_test.get_scheduled_job(TURN_OFF_HEAT_JOB_ID)
    assert turn_off_job.func.__name__ == "reset_floor_to_auto"


def test_reset_floor_to_auto(maestro_test: MaestroTest) -> None:
    """Test that reset_floor_to_auto sets the correct preset mode"""
    from scripts.home.bathroom_floor import reset_floor_to_auto

    maestro_test.set_state(climate.bathroom_floor_thermostat, "heat")

    # Call the function
    reset_floor_to_auto()

    # Assert: Preset mode was set to RUN_SCHEDULE
    maestro_test.assert_action_called(
        Domain.CLIMATE,
        "set_preset_mode",
        entity_id="climate.bathroom_floor_thermostat",
        preset_mode=BathroomFloor.PresetMode.RUN_SCHEDULE,
    )


def test_check_floor_temp_reschedules_if_not_ready(maestro_test: MaestroTest) -> None:
    """Test that check_floor_temp reschedules if temperature is below threshold"""
    from scripts.home.bathroom_floor import check_floor_temp

    # Setup: Floor is not warm enough yet (threshold is HEAT_TEMPERATURE - 5)
    maestro_test.set_state(
        climate.bathroom_floor_thermostat,
        "heat",
        {"current_temperature": 70},  # Below 80° threshold
    )

    # Call the function
    check_floor_temp(caller=person.marshall)

    # Assert: No notification was sent
    maestro_test.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)

    # Assert: Temperature check was rescheduled
    maestro_test.assert_job_scheduled(TEMPERATURE_CHECK_JOB_ID)
    job = maestro_test.get_scheduled_job(TEMPERATURE_CHECK_JOB_ID)
    assert job.kwargs["caller"] == person.marshall


def test_check_floor_temp_notifies_when_ready(maestro_test: MaestroTest) -> None:
    """Test that check_floor_temp sends notification when temperature is ready"""
    from scripts.home.bathroom_floor import check_floor_temp

    # Setup: Floor is warm enough (threshold is HEAT_TEMPERATURE - 5 = 80)
    ready_temp = 82
    maestro_test.set_state(
        climate.bathroom_floor_thermostat,
        "heat",
        {"current_temperature": ready_temp},
    )

    # Call the function
    check_floor_temp(caller=person.emily)

    # Assert: Notification was sent to the caller
    maestro_test.assert_action_called(
        Domain.NOTIFY,
        person.emily.notify_action_name,
        title="Bathroom Floor Ready",
        message=f"The bathroom floor is a nice warm {ready_temp}°",
    )


def test_bathroom_floor_timeout_handler_cancels_on_auto(maestro_test: MaestroTest) -> None:
    """Test that timeout handler cancels auto-shutoff job when mode is set to AUTO"""
    # Setup: Schedule a fake auto-shutoff job first
    maestro_test.set_state(climate.bathroom_floor_thermostat, "heat")

    # Manually schedule the auto-shutoff job so we can test cancellation
    from maestro.utils.scheduler import JobScheduler

    def fake_timeout() -> None:
        pass

    scheduler = JobScheduler()
    scheduler.schedule_job(
        run_time=local_now() + timedelta(hours=1),
        func=fake_timeout,
        job_id=AUTO_SHUTOFF_JOB_ID,
    )

    maestro_test.assert_job_scheduled(AUTO_SHUTOFF_JOB_ID)

    # Trigger state change to AUTO
    maestro_test.trigger_state_change(
        climate.bathroom_floor_thermostat,
        old="heat",
        new=BathroomFloor.HVACMode.AUTO,
    )

    # Assert: Auto-shutoff job was cancelled
    maestro_test.assert_job_not_scheduled(AUTO_SHUTOFF_JOB_ID)


def test_bathroom_floor_timeout_handler_schedules_shutoff(maestro_test: MaestroTest) -> None:
    """Test that timeout handler schedules auto-shutoff when mode is not AUTO"""
    maestro_test.set_state(climate.bathroom_floor_thermostat, "off")

    # Trigger state change to HEAT
    maestro_test.trigger_state_change(
        climate.bathroom_floor_thermostat,
        old="off",
        new="heat",
    )

    # Assert: Auto-shutoff job was scheduled
    maestro_test.assert_job_scheduled(AUTO_SHUTOFF_JOB_ID)
    job = maestro_test.get_scheduled_job(AUTO_SHUTOFF_JOB_ID)

    # Verify the job will run after AUTO_SHUTOFF_TIME
    # Note: We can't easily verify exact run_time without exposing it,
    # but we can verify the job exists with correct function name
    assert job.func.__name__ == "reset_after_timeout"


def test_auto_shutoff_sends_notification_and_resets(maestro_test: MaestroTest) -> None:
    """Test that auto-shutoff function sends notification and resets floor"""
    # This tests the nested function inside bathroom_floor_timeout_handler
    # We'll trigger the state change and manually call the scheduled function

    maestro_test.set_state(climate.bathroom_floor_thermostat, "off")
    maestro_test.set_state(person.marshall, "home")

    # Trigger state change to schedule the auto-shutoff
    maestro_test.trigger_state_change(
        climate.bathroom_floor_thermostat,
        old="off",
        new="heat",
    )

    # Get the scheduled job and execute it manually
    job = maestro_test.get_scheduled_job(AUTO_SHUTOFF_JOB_ID)
    job.func()  # Execute the reset_after_timeout function

    # Assert: Notification was sent to Marshall
    maestro_test.assert_action_called(
        Domain.NOTIFY,
        person.marshall.notify_action_name,
        title="Bathroom Floor Still On",
    )

    # Assert: Floor was reset to auto mode
    maestro_test.assert_action_called(
        Domain.CLIMATE,
        "set_preset_mode",
        entity_id="climate.bathroom_floor_thermostat",
        preset_mode=BathroomFloor.PresetMode.RUN_SCHEDULE,
    )


def test_full_workflow_bathroom_floor_heating(maestro_test: MaestroTest) -> None:
    """Integration test: Full workflow from button press to notification"""
    # Setup
    maestro_test.set_state(climate.bathroom_floor_thermostat, OFF, {"current_temperature": 65})
    maestro_test.set_state(person.emily, "home")

    # Step 1: User presses bathroom_floor button
    maestro_test.trigger_event("bathroom_floor", user_id=PERSON_TO_USER_ID[person.emily])

    # Verify initial jobs were scheduled
    maestro_test.assert_job_scheduled(TEMPERATURE_CHECK_JOB_ID)
    maestro_test.assert_job_scheduled(TURN_OFF_HEAT_JOB_ID)

    # Step 2: First temperature check (not ready yet)
    temp_check_job = maestro_test.get_scheduled_job(TEMPERATURE_CHECK_JOB_ID)
    temp_check_job.func(**temp_check_job.kwargs)  # Execute check_floor_temp

    # Should have rescheduled
    jobs_after_first_check = maestro_test.get_scheduled_jobs()
    temp_check_jobs = [j for j in jobs_after_first_check if j.id == TEMPERATURE_CHECK_JOB_ID]
    assert len(temp_check_jobs) == 1

    # Step 3: Floor heats up, check again
    maestro_test.set_state(
        climate.bathroom_floor_thermostat,
        "heat",
        {"current_temperature": 83},  # Above threshold
    )

    temp_check_job = maestro_test.get_scheduled_job(TEMPERATURE_CHECK_JOB_ID)
    temp_check_job.func(**temp_check_job.kwargs)

    # Should have sent notification and NOT rescheduled
    maestro_test.assert_action_called(
        Domain.NOTIFY,
        person.emily.notify_action_name,
        title="Bathroom Floor Ready",
    )
