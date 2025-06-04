from vapi import Vapi
import os
from dotenv import load_dotenv
from support_assistant import create_support_assistant

load_dotenv()
client = Vapi(token=os.getenv("VAPI_TOKEN"))
assistant_id = os.getenv("ASSISTANT_ID")
phone_number_id = os.getenv("PHONE_NUMBER_ID")


def make_outbound_call(assistant_id: str, phone_number: str):
    try:
        call = client.calls.create(
            assistant_id=assistant_id,
            phone_number_id=phone_number_id,
            customer={
                "number": "+917204218098",  # Target phone number
            },
        )
        
        print(f"Outbound call initiated: {call.id}")
        return call
    except Exception as error:
        print(f"Error making outbound call: {error}")
        raise error

#  number for testing
make_outbound_call(assistant_id, "+917204218098")
