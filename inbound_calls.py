from vapi import Vapi
import os
from dotenv import load_dotenv
from support_assistant import create_support_assistant

load_dotenv()
client = Vapi(token=os.getenv("VAPI_TOKEN"))


def configure_inbound_calls(phone_number_id: str, assistant_id: str):
    try:
        updated_number = client.phone_numbers.update(
            phone_number_id,  # The ID of the phone number to update
            request={"assistant_id": assistant_id}  # The payload passed as the 'request' keyword argument
        )
        print(f"Phone number {phone_number_id} configured to use assistant {assistant_id}")
        return updated_number
    except Exception as error:
        print(f"Error configuring inbound calls: {error}")
        raise error


phone_number_id = os.getenv("PHONE_NUMBER_ID")
assistant_id = os.getenv("ASSISTANT_ID")

configure_inbound_calls(phone_number_id, assistant_id)
