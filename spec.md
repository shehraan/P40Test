# Dad Reminder App — Build Instructions for GLM-4.7-Flash

## What you're building

A small Python server that:
1. Receives an SMS from you (via Twilio) containing a task, e.g. `"remind dad to take his medication at 6pm"`
2. Immediately triggers a Vapi outbound voice call to your dad's number
3. A voice AI reads him the reminder, waits for acknowledgment, then ends the call
4. Texts you back a confirmation that the call was placed

---

## Tech stack

- **Python 3.11+** with **FastAPI** and **uvicorn**
- **Twilio** — inbound SMS webhook + confirmation SMS back to you
- **Vapi** — outbound voice call to dad using a transient assistant
- **python-dotenv** for secrets
- **httpx** for async HTTP requests to the Vapi API

---

## Project structure

```
dad-reminder/
├── main.py           # FastAPI app — all routes live here
├── vapi_client.py    # Vapi API wrapper (place call, build assistant payload)
├── twilio_client.py  # Twilio helper (send confirmation SMS back to you)
├── config.py         # Load and validate env vars on startup
├── .env              # Secrets (never commit this)
├── requirements.txt
└── README.md
```

---

## Environment variables (.env)

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx       # your Twilio number (dad calls come FROM this)
MY_PHONE_NUMBER=+1xxxxxxxxxx           # your number (you text this to trigger reminders)
DAD_PHONE_NUMBER=+1xxxxxxxxxx          # dad's number

VAPI_API_KEY=your_vapi_private_key
VAPI_PHONE_NUMBER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # from Vapi dashboard
```

---

## Detailed spec for each file

### config.py
- Use `pydantic-settings` (`BaseSettings`) to load all env vars
- Raise a clear error on startup if any required var is missing
- Export a single `settings` singleton imported by other modules

### main.py
- One POST route: `POST /sms` — this is the Twilio webhook
- On receive:
  1. Validate the incoming request is from your own number (`From` field == `MY_PHONE_NUMBER`). If not, respond with HTTP 403 and do not process.
  2. Extract the task from `Body` field of the Twilio form data
  3. If body is empty or just whitespace, text back "No task provided. Send a message like: remind dad to call the doctor."
  4. Call `vapi_client.place_call(task)` — await this
  5. Call `twilio_client.send_confirmation(task)` — sends you an SMS like "✓ Calling dad now: remind him to call the doctor"
  6. Return a valid TwiML response (`<Response></Response>`) so Twilio doesn't retry
- Add a `GET /health` route that returns `{"status": "ok"}` — useful for testing the server is up

### vapi_client.py
- Async function `place_call(task: str) -> dict`
- Makes a POST to `https://api.vapi.ai/call` with `Bearer` auth header
- Uses a **transient assistant** (inline, not a saved assistant ID) so the task text can be injected dynamically per call
- Assistant configuration:
  - `firstMessage`: `"Hi, this is a reminder from [your name]. {task}. Did you get that?"`
  - `model`: use `openai` provider with model `gpt-4o-mini` (or make this configurable via env var so it's easy to swap)
  - System prompt: `"You are a friendly reminder assistant calling on behalf of [your name]. Your only job is to deliver the reminder message, confirm the person heard it, then politely end the call. Keep it short. If they ask questions you can't answer, say you're just a reminder bot and they can call [your name] directly."`
  - `endCallMessage`: `"Great, I'll let them know you got the message. Goodbye!"`
  - `endCallPhrases`: `["got it", "okay", "yes", "understood", "thank you"]`
  - `voice`: provider `11labs`, voice `paula` (or `azure` with `en-US-JennyNeural` as fallback)
  - `maxDurationSeconds`: 120 — cut the call after 2 minutes max
- Request body fields:
  - `phoneNumberId`: from settings
  - `customer.number`: `DAD_PHONE_NUMBER` from settings
  - `assistant`: the transient assistant dict above (NOT `assistantId`)
- Return the full Vapi response dict
- Raise a descriptive exception if the HTTP response is not 201

### twilio_client.py
- Sync function `send_confirmation(task: str)`
- Uses `twilio.rest.Client` to send an SMS
- From: `TWILIO_PHONE_NUMBER`, To: `MY_PHONE_NUMBER`
- Message: `f"✓ Calling dad now with: {task}"`

### requirements.txt
```
fastapi
uvicorn[standard]
twilio
httpx
python-dotenv
pydantic-settings
```

---

## Edge cases to handle

| Scenario | Expected behavior |
|---|---|
| SMS from unknown number | 403, no call placed |
| Empty SMS body | Text back a usage hint, no call placed |
| Vapi API returns non-201 | Log full error response, text you "❌ Call failed: {error}", still return valid TwiML |
| Dad doesn't pick up | Vapi handles this natively (voicemail detection) — no special handling needed |
| Twilio retries the webhook | Idempotency is not critical for this use case — a duplicate call is acceptable |

---

## How to run locally for testing

```bash
# Install deps
pip install -r requirements.txt

# Expose local server to the internet so Twilio can reach it
# Install ngrok: https://ngrok.com
ngrok http 8000

# Copy the https ngrok URL, e.g. https://abc123.ngrok.io
# In Twilio console → your number → Messaging → Webhook URL:
# Set to: https://abc123.ngrok.io/sms

# Run the server
uvicorn main:app --reload --port 8000
```

Then text your Twilio number from your personal phone:
> `remind dad to pick up the groceries before 5pm`

---

## Testing checklist

- [ ] `/health` returns 200
- [ ] SMS from your number triggers a Vapi call to dad's number
- [ ] You receive a confirmation SMS
- [ ] SMS from an unknown number returns 403 with no side effects
- [ ] Empty SMS body returns a helpful reply with no call placed
- [ ] Vapi call audio reads the task correctly

---

## Notes for the LLM

- Do not use `requests` — use `httpx` with async/await throughout
- Do not use `os.environ.get()` directly — all config goes through `config.py`'s `settings` object
- The Twilio webhook sends form-encoded data, not JSON — use `Request.form()` in FastAPI, not `Request.json()`
- Twilio requires a TwiML XML response even if you're not sending a reply SMS — always return `Response(content="<Response></Response>", media_type="application/xml")`
- Keep all business logic out of `main.py` route handlers — handlers should only parse input, call helpers, and return responses
