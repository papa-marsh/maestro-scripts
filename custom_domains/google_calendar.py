from dataclasses import dataclass
from datetime import datetime

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

                start = event_data.get("start", "")
                end = event_data.get("end", "")
                all_day = "T" not in start and "T" not in end

                events.append(
                    self.Event(
                        title=event_data.get("summary", ""),
                        description=event_data.get("description"),  # TODO: verify key
                        start=datetime.fromisoformat(start),
                        end=datetime.fromisoformat(end),
                        calendar=EntityId(calendar),
                        location=event_data.get("location"),
                        all_day=all_day,
                    )
                )
        events.sort(key=lambda e: e.start)

        return events
