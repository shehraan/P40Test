from twilio.rest import Client
from config import settings


def send_confirmation(task: str) -> None:
    """Send a confirmation SMS back to the user."""
    client = Client(
        settings.twilio_account_sid,
        settings.twilio_auth_token
    )

    message = client.messages.create(
        body=f"✓ Calling dad now with: {task}",
        from_=settings.twilio_phone_number,
        to=settings.my_phone_number
    )