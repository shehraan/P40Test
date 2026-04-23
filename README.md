# Dad Reminder App

A simple Python server that receives SMS reminders and triggers voice calls to your dad using Vapi.

## How it works

1. You text your Twilio number with a reminder (e.g., "remind dad to take his medication")
2. The server validates the sender and extracts the task
3. A Vapi voice call is placed to dad's number
4. A friendly AI assistant reads the reminder, waits for acknowledgment, and ends the call
5. You receive a confirmation SMS

## Requirements

- Python 3.11+
- Twilio account
- Vapi.ai account with a phone number

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your values:
   - Twilio Account SID and Auth Token
   - Your phone number and Twilio number
   - Dad's phone number
   - Vapi API key and phone number ID

4. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. Expose to the internet (using ngrok for local development):
   ```bash
   ngrok http 8000
   ```

6. In Twilio Console → Voice → A Call Comes In:
   - Set webhook to: `https://your-ngrok-url/sms`
   - Set method to: `POST`

## Usage

Text your Twilio number:
```
remind dad to call the doctor
```

You'll receive a confirmation SMS and dad will get a voice call.