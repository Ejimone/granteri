from vapi import Vapi
import os
from dotenv import load_dotenv
load_dotenv()
client = Vapi(token=os.getenv("VAPI_TOKEN"))


def purchase_phone_number():
    try:
        # Purchase a phone number
        phone_number = client.phone_numbers.create(
            fallback_destination={
                "type": "number",
                "number": "+1234567890",  # Your fallback number
            }
        )
        
        print(f"Phone number created: {phone_number.number}")
        return phone_number
    except Exception as error:
        print(f"Error creating phone number: {error}")
        raise error



purchase_phone_number()