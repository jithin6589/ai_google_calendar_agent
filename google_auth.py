from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():

    creds = None

    # To Check the token exists or not
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    # If credentials are not valid, login again
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials/client_secret.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        # Save login information
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Create Google Calendar API service
    service = build(
        "calendar",
        "v3",
        credentials=creds
    )

    return service