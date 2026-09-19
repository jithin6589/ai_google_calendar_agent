from google_auth import get_calendar_service


def list_calendars():
    """Google Calendar-കൾ കാണിക്കുന്നു."""

    service = get_calendar_service()

    results = service.calendarList().list().execute()

    calendars = results.get("items", [])

    if not calendars:
        return "No calendars found."

    output = []

    for calendar in calendars:
        name = calendar.get("summary", "No name")
        calendar_id = calendar.get("id")

        output.append(
            f"Calendar: {name}\nID: {calendar_id}"
        )

    return "\n\n".join(output)


def list_events():
    """Google Calendar-ലെ അടുത്തുള്ള events കാണിക്കുന്നു."""

    service = get_calendar_service()

    results = service.events().list(
        calendarId="primary",
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = results.get("items", [])

    if not events:
        return "No upcoming events found."

    output = []

    for event in events:
        summary = event.get("summary", "No title")

        start = event.get("start", {}).get(
            "dateTime",
            event.get("start", {}).get("date", "")
        )

        output.append(
            f"Event: {summary}\nStart: {start}"
        )

    return "\n\n".join(output)


def create_event(
    summary,
    start_time,
    end_time,
    description="",
    location=""
):
    """Google Calendar-ൽ പുതിയ event ഉണ്ടാക്കുന്നു."""

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
        f"Event created successfully!\n"
        f"Title: {created_event.get('summary')}\n"
        f"Start: {created_event.get('start', {}).get('dateTime')}\n"
        f"Link: {created_event.get('htmlLink')}"
    )