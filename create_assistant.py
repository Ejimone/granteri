from vapi import Vapi
import os
from dotenv import load_dotenv
from support_assistant import create_support_assistant

load_dotenv()
client = Vapi(token=os.getenv("VAPI_TOKEN"))


assistant = client.assistants.create(
    name="Sales Assistant",
    first_message="Hi! I'm calling about your interest in our software solutions.",
    model={
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.7,
        "messages": [{
            "role": "system",
            "content": "You are a friendly sales representative. Keep responses under 30 words."
        }]
    },
    voice={
        "provider": "11labs",
        "voice_id": "21m00Tcm4TlvDq8ikWAM"
    }
)
