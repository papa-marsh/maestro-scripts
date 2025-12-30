from dataclasses import dataclass
from datetime import datetime

from maestro.config import TIMEZONE
from maestro.domains import Calendar
from maestro.integrations import EntityId


class GoogleCalendar(Calendar):
    message: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    all_day: bool

    @dataclass
    class Event:
        title: str
        description: str | None
        start: datetime
        end: datetime
        calendar: EntityId
        location: str | None
        all_day: bool = False

    @property
    def next_event(self) -> Event:
        return self.Event(
            title=self.message,
            description=self.description,
            start=self.start_time,
            end=self.end_time,
            calendar=self.id,
            location=self.location,
            all_day=self.all_day,
        )

    def get_gcal_events(
        self,
        days: int = 7,
        calendar_ids: list[EntityId] | None = None,
    ) -> list[Event]:
        events = []
        raw_response = self.get_events(duration={"days": days}, calendar_ids=calendar_ids)

        for calendar, content in raw_response.items():
            for event_data in content["events"]:
                if not isinstance(event_data, dict):
                    raise TypeError(f"Expected dict but got {type(event_data).__name__}")

                start_string = event_data.get("start", "")
                end_string = event_data.get("end", "")
                all_day = "T" not in start_string and "T" not in end_string

                start = datetime.fromisoformat(start_string)
                end = datetime.fromisoformat(end_string)

                if start.tzinfo is None:
                    start = start.replace(tzinfo=TIMEZONE)
                if end.tzinfo is None:
                    end = end.replace(tzinfo=TIMEZONE)

                events.append(
                    self.Event(
                        title=event_data.get("summary", ""),
                        description=event_data.get("description"),  # TODO: verify key
                        start=start,
                        end=end,
                        calendar=EntityId(calendar),
                        location=event_data.get("location"),
                        all_day=all_day,
                    )
                )
        events.sort(key=lambda e: e.start)

        return events
