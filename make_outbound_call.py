from vapi import Vapi
import os
from dotenv import load_dotenv
from support_assistant import create_support_assistant
import logging

load_dotenv()
logger = logging.getLogger(__name__)

client = Vapi(token=os.getenv("VAPI_TOKEN"))
assistant_id = os.getenv("ASSISTANT_ID")
phone_number_id = os.getenv("PHONE_NUMBER_ID")


def make_outbound_call(assistant_id: str, target_phone_number: str, context_data: dict = None):
    """
    Make an outbound call using Vapi
    
    Args:
        assistant_id: The assistant to use for the call
        target_phone_number: The phone number to call
        context_data: Optional context data for the call
        
    Returns:
        Call object from Vapi
    """
    try:
        # Prepare call parameters
        call_params = {
            "assistant_id": assistant_id,
            "phone_number_id": phone_number_id,
            "customer": {
                "number": target_phone_number,
            },
        }
        
        # Add context data if provided
        if context_data:
            call_params["metadata"] = context_data
        
        logger.info(f"Making outbound call to {target_phone_number} with assistant {assistant_id}")
        
        call = client.calls.create(**call_params)
        
        logger.info(f"Outbound call initiated successfully: {call.id if hasattr(call, 'id') else 'unknown_id'}")
        return call
        
    except Exception as error:
        logger.error(f"Error making outbound call to {target_phone_number}: {error}")
        raise error


def make_outbound_call_with_livekit_context(target_phone_number: str, transfer_to: str = "+917204218098"):
    """
    Make an outbound call with LiveKit context metadata
    
    Args:
        target_phone_number: The phone number to call
        transfer_to: The number to transfer to if needed
        
    Returns:
        Dict with call information and LiveKit metadata
    """
    try:
        # Create the Vapi call
        vapi_call = make_outbound_call(assistant_id, target_phone_number, {
            "call_type": "outbound",
            "transfer_to": transfer_to
        })
        
        # Prepare LiveKit metadata for agent dispatch
        livekit_metadata = {
            "call_type": "outbound",
            "phone_number": target_phone_number,
            "transfer_to": transfer_to,
            "vapi_call_id": vapi_call.id if hasattr(vapi_call, 'id') else None
        }
        
        return {
            "vapi_call": vapi_call,
            "livekit_metadata": livekit_metadata,
            "success": True
        }
        
    except Exception as error:
        logger.error(f"Error in outbound call with LiveKit context: {error}")
        return {
            "vapi_call": None,
            "livekit_metadata": None,
            "success": False,
            "error": str(error)
        }


# Example usage (commented out to prevent auto-execution)
if __name__ == "__main__":
    # Only run if explicitly called as script
    import sys
    
    if len(sys.argv) > 1:
        target_number = sys.argv[1]
        print(f"Making outbound call to {target_number}")
        
        try:
            result = make_outbound_call_with_livekit_context(target_number)
            if result["success"]:
                print(f"Call initiated successfully!")
                print(f"Vapi Call ID: {result['vapi_call'].id if result['vapi_call'] and hasattr(result['vapi_call'], 'id') else 'unknown'}")
            else:
                print(f"Call failed: {result['error']}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python make_outbound_call.py <phone_number>")
        print("Example: python make_outbound_call.py +1234567890")
