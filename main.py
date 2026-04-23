from fastapi import Request, Response
from fastapi.responses import HTMLResponse, Response as HttpResponse
from twilio.rest import Client
from twilio.twiml.voice_response import Response as TwiMLResponse
import urllib.parse

from config import settings
from vapi_client import place_call
from twilio_client import send_confirmation


async def sms_handler(request: Request) -> Response:
    """Handle inbound SMS from the user."""
    form = await request.form()

    # Validate the sender is the user's number
    from_number = form.get("From")
    if from_number != settings.my_phone_number:
        # Return 403 to prevent processing
        return Response(content="", status_code=403)

    # Extract task from the message body
    task_body = form.get("Body", "").strip()

    # Validate task is not empty
    if not task_body:
        # Send usage hint back via SMS
        usage_hint = urllib.parse.quote_plus(
            "No task provided. Send a message like: remind dad to call the doctor."
        )
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body="No task provided. Send a message like: remind dad to call the doctor.",
            from_=settings.twilio_phone_number,
            to=settings.my_phone_number
        )
        # Return TwiML so Twilio doesn't retry
        twiml = TwiMLResponse()
        return HttpResponse(
            content=str(twiml),
            media_type="application/xml"
        )

    # Place Vapi call and send confirmation
    try:
        await place_call(task_body)
        send_confirmation(task_body)
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error: {e}")

        # Send error message to user
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=f"❌ Call failed: {str(e)}",
            from_=settings.twilio_phone_number,
            to=settings.my_phone_number
        )

    # Return TwiML to indicate webhook completed
    twiml = TwiMLResponse()
    return HttpResponse(
        content=str(twiml),
        media_type="application/xml"
    )


def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


def index() -> HTMLResponse:
    """Simple UI for testing."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dad Reminder App</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; }
            .status {
                padding: 15px;
                background: #d4edda;
                border-radius: 4px;
                color: #155724;
                margin: 20px 0;
            }
            form {
                margin-top: 20px;
            }
            input[type="text"] {
                width: 70%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            button {
                padding: 10px 20px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Dad Reminder App</h1>
            <div class="status" id="status">
                <strong>Server Status:</strong> Checking...
            </div>
            <p>Test the SMS reminder feature:</p>
            <form id="test-form">
                <input type="text" id="task" placeholder="remind dad to take medication">
                <button type="submit">Send Test</button>
            </form>
            <p style="margin-top: 30px; color: #666;">
                Or text your Twilio number directly:
                <strong>"remind dad to take medication"</strong>
            </p>
            <p style="color: #666;">
                Health check: <a href="/health" target="_blank">/health</a>
            </p>
        </div>
        <script>
            fetch('/health')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status').innerHTML =
                        '<strong>Server Status:</strong> ' +
                        '<span style="color: green">✓ Running</span>';
                })
                .catch(() => {
                    document.getElementById('status').innerHTML =
                        '<strong>Server Status:</strong> <span style="color: red">✗ Not responding</span>';
                });

            document.getElementById('test-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const task = document.getElementById('task').value;
                const response = await fetch('/sms', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'Body=' + encodeURIComponent(task)
                });

                if (response.ok) {
                    alert('Test SMS sent! Check your phone for confirmation.');
                } else {
                    alert('Test failed: ' + response.status);
                }
            });
        </script>
    </body>
    </html>
    """)


def create_app() -> fastapi.FastAPI:
    """Create and configure the FastAPI app."""
    import fastapi

    app = fastapi.FastAPI(
        title="Dad Reminder App",
        description="SMS-triggered voice reminder service"
    )

    # Routes
    app.add_api_route("/sms", sms_handler, methods=["POST"])
    app.add_api_route("/health", health_check, methods=["GET"])
    app.get("/", response_class=HTMLResponse)(index)

    return app


app = create_app()