from google_auth import get_calendar_service

# 1. LIST CALENDARS

def list_calendars():
    """List all calendars in the user's Google Calendar."""
    service = get_calendar_service()
    results = service.calendarList().list().execute()
    calendars = results.get("items", [])
    if not calendars:
        return "No calendars found."
    output = []
    for calendar in calendars:
        name = calendar.get(
            "summary",
            "No name"
        )
        calendar_id = calendar.get("id")
        output.append(
            f"Calendar: {name}\n"
            f"ID: {calendar_id}"
        )
    return "\n\n".join(output)

# 2. LIST EVENTS

from datetime import datetime
from zoneinfo import ZoneInfo
def list_events():
    """LIST ALL EVENTS FROM GOOGLE CALENDAR"""
    service = get_calendar_service()
    all_events = []
    page_token = None
    while True:
        results = service.events().list(
            calendarId="primary",
            maxResults=2500,
            singleEvents=True,
            orderBy="startTime",
            pageToken=page_token
        ).execute()
        events = results.get("items", [])
        all_events.extend(events)
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    if not all_events:
        return "No events found."
    output = []
    for event in all_events:
        summary = event.get("summary","No title")
        start_data = event.get(
            "start",
            {}
        )
        start = start_data.get(
            "dateTime",
            start_data.get("date", "")
        )
        output.append(
            f"Event: {summary}\n"
            f"Start: {start}"
        )
    return "\n\n".join(output)

# 3. CREATE EVENT

def create_event(
    summary,
    start_time,
    end_time,
    description="",
    location=""
):
    """Create a new event in to your primary calendar."""
    service = get_calendar_service()
    event = {
        "summary": summary,
        "description": description,
        "location": location,

        "start": {
            "dateTime": start_time,
            "timeZone": "Asia/Kolkata"
        },

        "end": {
            "dateTime": end_time,
            "timeZone": "Asia/Kolkata"
        }
    }
    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()
    return (
        "Event created successfully!\n"
        f"Title: {created_event.get('summary')}\n"
        f"Start: "
        f"{created_event.get('start', {}).get('dateTime')}\n"
        f"Link: {created_event.get('htmlLink')}"
    )

# 4. UPDATE EVENT FUNCTION

def update_event(
    event_id,
    summary=None,
    start_time=None,
    end_time=None,
    description=None,
    location=None
):
    """UPDATE AN EXISTING GOOGLE CALENDAR EVENT"""

    service = get_calendar_service()

    # Get the existing event
    event = service.events().get(
        calendarId="primary",
        eventId=event_id
    ).execute()

    # Update only the values provided
    if summary is not None:
        event["summary"] = summary

    if start_time is not None:
        event["start"] = {
            "dateTime": start_time,
            "timeZone": "Asia/Kolkata"
        }

    if end_time is not None:
        event["end"] = {
            "dateTime": end_time,
            "timeZone": "Asia/Kolkata"
        }

    if description is not None:
        event["description"] = description

    if location is not None:
        event["location"] = location

    # Update the event in Google Calendar
    updated_event = service.events().update(
        calendarId="primary",
        eventId=event_id,
        body=event
    ).execute()

    return (
        f"Event updated successfully!\n"
        f"Title: {updated_event.get('summary')}\n"
        f"Start: {updated_event.get('start', {}).get('dateTime', updated_event.get('start', {}).get('date', ''))}\n"
        f"Link: {updated_event.get('htmlLink')}"
    )
def find_event(search_text):
    """FIND AN EVENT BY TITLE"""

    service = get_calendar_service()

    all_events = []
    page_token = None

    while True:

        results = service.events().list(
            calendarId="primary",
            maxResults=2500,
            singleEvents=True,
            orderBy="startTime",
            pageToken=page_token
        ).execute()

        events = results.get("items", [])

        all_events.extend(events)

        page_token = results.get("nextPageToken")

        if not page_token:
            break

    matches = []

    search_text = search_text.lower()

    for event in all_events:

        summary = event.get(
            "summary",
            ""
        )

        if search_text in summary.lower():

            matches.append({
                "id": event.get("id"),
                "summary": summary,
                "start": event.get(
                    "start",
                    {}
                ).get(
                    "dateTime",
                    event.get(
                        "start",
                        {}
                    ).get("date", "")
                )
            })

    if not matches:
        return "No matching event found."

    output = []

    for event in matches:

        output.append(
            f"Event: {event['summary']}\n"
            f"ID: {event['id']}\n"
            f"Start: {event['start']}"
        )

    return "\n\n".join(output)

# 5. DELETE EVENT FUNCTION

def delete_event(event_id):
    """DELETE AN EXISTING GOOGLE CALENDAR EVENT"""

    service = get_calendar_service()

    event = service.events().get(
        calendarId="primary",
        eventId=event_id
    ).execute()

    event_title = event.get(
        "summary",
        "No title"
    )

    service.events().delete(
        calendarId="primary",
        eventId=event_id
    ).execute()

    return (
        f"Event deleted successfully!\n"
        f"Title: {event_title}"
    )