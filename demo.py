#!/usr/bin/env python3
"""
Example script showing how to use the refactored voice agent system.
This demonstrates both outbound and inbound call handling.
"""

import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# Import our modules
from make_outbound_call import make_outbound_call_with_livekit_context
from inbound_calls import configure_inbound_calls
from webhook_handler import process_inbound_webhook
from agent import make_explicit_outbound_call

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def demo_outbound_call(phone_number: str):
    """
    Demonstrate making an outbound call
    """
    print(f"\n=== Making Outbound Call to {phone_number} ===")
    
    try:
        # Method 1: Using Vapi directly
        print("1. Making call with Vapi...")
        result = make_outbound_call_with_livekit_context(phone_number)
        
        if result["success"]:
            print(f"✅ Vapi call initiated successfully!")
            print(f"   Call ID: {result['vapi_call'].id if result['vapi_call'] and hasattr(result['vapi_call'], 'id') else 'unknown'}")
            
            # Method 2: Prepare LiveKit metadata for agent dispatch
            print("2. Preparing LiveKit agent metadata...")
            metadata = await make_explicit_outbound_call(phone_number)
            print(f"   LiveKit metadata: {metadata}")
            
        else:
            print(f"❌ Call failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def demo_inbound_setup():
    """
    Demonstrate setting up inbound calls
    """
    print("\n=== Setting Up Inbound Calls ===")
    
    try:
        phone_number_id = os.getenv("PHONE_NUMBER_ID")
        assistant_id = os.getenv("ASSISTANT_ID")
        
        if not phone_number_id or not assistant_id:
            print("❌ Missing PHONE_NUMBER_ID or ASSISTANT_ID in environment variables")
            return
        
        print(f"Configuring phone number {phone_number_id} with assistant {assistant_id}")
        result = configure_inbound_calls(phone_number_id, assistant_id)
        print(f"✅ Inbound calls configured successfully!")
        print(f"   Result: {result}")
        
    except Exception as e:
        print(f"❌ Error configuring inbound calls: {e}")

def demo_webhook_handling():
    """
    Demonstrate webhook handling for inbound calls
    """
    print("\n=== Testing Webhook Handling ===")
    
    # Simulate webhook payloads
    test_payloads = [
        {
            "type": "call.started",
            "call": {
                "id": "test-call-123",
                "customer": {"number": "+1234567890"},
                "assistant_id": os.getenv("ASSISTANT_ID")
            }
        },
        {
            "type": "transcript",
            "call": {"id": "test-call-123"},
            "transcript": {
                "text": "Hello, I need help with my appointment",
                "role": "user"
            }
        },
        {
            "type": "call.ended",
            "call": {
                "id": "test-call-123",
                "duration": 120
            }
        }
    ]
    
    for payload in test_payloads:
        print(f"\nProcessing webhook: {payload['type']}")
        response = process_inbound_webhook(payload)
        print(f"Response: {response}")

def show_configuration():
    """
    Show current configuration status
    """
    print("\n=== Configuration Status ===")
    
    config_items = [
        ("VAPI_TOKEN", os.getenv("VAPI_TOKEN")),
        ("ASSISTANT_ID", os.getenv("ASSISTANT_ID")),
        ("PHONE_NUMBER_ID", os.getenv("PHONE_NUMBER_ID")),
        ("LIVEKIT_API_KEY", os.getenv("LIVEKIT_API_KEY")),
        ("LIVEKIT_API_SECRET", os.getenv("LIVEKIT_API_SECRET")),
        ("LIVEKIT_URL", os.getenv("LIVEKIT_URL")),
        ("SIP_OUTBOUND_TRUNK_ID", os.getenv("SIP_OUTBOUND_TRUNK_ID"))
    ]
    
    for name, value in config_items:
        status = "✅ Configured" if value else "❌ Missing"
        # Hide sensitive values
        display_value = f"{value[:8]}..." if value and len(value) > 8 else value
        print(f"{name}: {status} ({display_value})")

def show_usage_instructions():
    """
    Show instructions for using the system
    """
    print("\n=== Usage Instructions ===")
    print("""
1. OUTBOUND CALLS:
   - Use make_outbound_call.py directly: python make_outbound_call.py +1234567890
   - Use FastAPI endpoint: POST /calls/outbound with phone number
   - Use this demo: python demo.py --outbound +1234567890

2. INBOUND CALLS:
   - Configure phone number: python demo.py --configure-inbound
   - Set webhook URL in Vapi dashboard to: https://your-domain.com/webhooks/inbound
   - Calls will be automatically handled by the configured assistant

3. FASTAPI SERVER:
   - Run: python app.py
   - Access API docs: http://localhost:8000/docs
   - Make outbound calls via REST API
   - Handle inbound webhooks automatically

4. LIVEKIT AGENT:
   - Run agent: python agent.py
   - The agent will handle both inbound and outbound calls
   - No auto-dialing - only responds to explicit requests

5. WEBHOOK TESTING:
   - Test webhook handling: python demo.py --test-webhooks
   - View webhook logs and call data
    """)

async def main():
    """
    Main demo function
    """
    import sys
    
    print("🎤 Voice Agent System Demo")
    print("=" * 50)
    
    # Show configuration first
    show_configuration()
    
    if len(sys.argv) < 2:
        show_usage_instructions()
        return
    
    command = sys.argv[1]
    
    if command == "--outbound" and len(sys.argv) > 2:
        phone_number = sys.argv[2]
        await demo_outbound_call(phone_number)
        
    elif command == "--configure-inbound":
        demo_inbound_setup()
        
    elif command == "--test-webhooks":
        demo_webhook_handling()
        
    elif command == "--help":
        show_usage_instructions()
        
    else:
        print(f"Unknown command: {command}")
        show_usage_instructions()

if __name__ == "__main__":
    asyncio.run(main())
