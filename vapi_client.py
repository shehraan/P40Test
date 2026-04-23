import httpx
from config import settings
from typing import Optional


async def place_call(task: str) -> dict:
    """Place a Vapi outbound call with a transient assistant."""
    assistant = {
        "firstMessage": f"Hi, this is a reminder from Dad. {task}. Did you get that?",
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini"
        },
        "systemPrompt": (
            "You are a friendly reminder assistant calling on behalf of Dad. "
            "Your only job is to deliver the reminder message, confirm the person heard it, "
            "then politely end the call. Keep it short. If they ask questions you can't answer, "
            "say you're just a reminder bot and they can call Dad directly."
        ),
        "endCallMessage": "Great, I'll let them know you got the message. Goodbye!",
        "endCallPhrases": ["got it", "okay", "yes", "understood", "thank you"],
        "voice": {
            "provider": "11labs",
            "voice": "paula"
        },
        "maxDurationSeconds": 120
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.vapi.ai/call",
            headers={
                "Authorization": f"Bearer {settings.vapi_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "phoneNumberId": settings.vapi_phone_number_id,
                "customer": {
                    "number": settings.dad_phone_number
                },
                "assistant": assistant
            }
        )

    if response.status_code != 201:
        error_text = response.text
        raise Exception(f"Vapi API returned {response.status_code}: {error_text}")

    return response.json()