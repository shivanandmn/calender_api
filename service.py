from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TIMEZONE = "Asia/Kolkata"
CALENDER_ID = "primary"


def to_timezone(dt):
    dt = dt.astimezone(ZoneInfo(TIMEZONE))
    return dt


class EventManager:
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(self) -> None:
        creds = None
        if os.path.exists("creds/token.pickle"):
            with open("creds/token.pickle", "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "creds/client_secret.json", self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open("creds/token.pickle", "wb") as token:
                pickle.dump(creds, token)
        self.service = build("calendar", "v3", credentials=creds)

    def events(self, **kwargs):
        return self.service.events().list(**kwargs).execute()

    def create_event(
        self, start_time, end_time, summary, description=None, location=None
    ):
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": TIMEZONE,
            },
            "end": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": TIMEZONE,
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }
        return (
            self.service.events().insert(calendarId=CALENDER_ID, body=event).execute()
        )


### to the nearest round 15mins
def roundoff(dt, to=15):
    minutes_to_add = (to - dt.minute % to) % 15
    rounded_dt = (dt + timedelta(minutes=minutes_to_add)).replace(
        second=0, microsecond=0
    )
    return rounded_dt


def check_overlap(events, start, end):
    for event in events:
        if event["start"] < end and start < event["end"]:
            return True
    return False


class CalenderService:

    def __init__(self) -> None:
        self.event_manager = EventManager()

    def list_events(self, start_date, end_date):
        # Convert dates to RFC3339 timestamps
        time_min = start_date.isoformat()  # + "Z"
        time_max = end_date.isoformat()  # + "Z"

        # Get events within the specified timeframe
        events_result = self.event_manager.events(
            calendarId=CALENDER_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
        collection = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])
            event["start"] = to_timezone(
                datetime.fromisoformat(event["start"]["dateTime"])
            )
            event["end"] = to_timezone(datetime.fromisoformat(event["end"]["dateTime"]))
        return collection, events

    def find_free_slots(self, business_hours, appointment_duration, number_of_slots=3):
        business_hours["start"] = max(
            roundoff(business_hours["start"]), roundoff(to_timezone(datetime.now()))
        )
        collection, events = self.list_events(
            business_hours["start"], business_hours["end"]
        )
        free_slots = []
        events.sort(
            key=lambda x: x["start"]
        )  # Assuming each event is a dict with 'start' and 'end' keys
        current_time = business_hours["start"]

        while current_time < business_hours["end"]:
            if not check_overlap(
                events, current_time, current_time + appointment_duration
            ):
                free_slots.append((current_time, current_time + appointment_duration))
            current_time = current_time + appointment_duration
            if len(free_slots) == number_of_slots:
                break

        return free_slots


if __name__ == "__main__":
    calender_service = CalenderService()
    calender_service.find_free_slots(
        business_hours={
            "start": to_timezone(datetime(2024, 3, 16, 10, 0, 0)),
            "end": to_timezone(datetime(2024, 3, 16, 22, 0, 0)),
        },
        appointment_duration=timedelta(minutes=30),
    )
