from vapi import Vapi
import os
from dotenv import load_dotenv
from support_assistant import create_support_assistant
import time
load_dotenv()
client = Vapi(token=os.getenv("VAPI_TOKEN"))

def run_bulk_call_campaign(assistant_id: str, phone_number_id: str):
    prospects = [
        {"number": "+1234567890", "name": "John Smith"},
        {"number": "+1234567891", "name": "Jane Doe"},
        # ... more prospects
    ]

    calls = []
    for prospect in prospects:
        call = vapi.calls.create(
            assistant_id=assistant_id,
            phone_number_id=phone_number_id,
            customer=prospect,
            metadata={"campaign": "Q1_Sales"}
        )
        calls.append(call)

        # Rate limiting
        time.sleep(2)

    return calls
