"""
FastAPI application for managing voice agent calls.
Provides REST endpoints for triggering outbound calls and handling inbound call webhooks.
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import logging
import os
from typing import Optional, Dict, Any
import asyncio
from dotenv import load_dotenv

# Import our call functions
from make_outbound_call import make_outbound_call
from inbound_calls import configure_inbound_calls
from support_assistant import create_support_assistant

# Import for LiveKit agent dispatch
from livekit import api, rtc

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Agent API",
    description="API for managing inbound and outbound voice calls with AI agents",
    version="1.0.0"
)

# Environment variables
VAPI_TOKEN = os.getenv("VAPI_TOKEN")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

# Pydantic models for API requests
class OutboundCallRequest(BaseModel):
    phone_number: str
    transfer_to: Optional[str] = "+917204218098"
    assistant_id: Optional[str] = None
    call_context: Optional[Dict[str, Any]] = None

class InboundCallWebhook(BaseModel):
    call_id: str
    phone_number: str
    status: str
    metadata: Optional[Dict[str, Any]] = None

class CallStatusResponse(BaseModel):
    success: bool
    message: str
    call_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Global call tracking
active_calls: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Voice Agent API is running",
        "status": "healthy",
        "active_calls": len(active_calls)
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "vapi": "configured" if VAPI_TOKEN else "missing_token",
            "livekit": "configured" if LIVEKIT_API_KEY else "missing_credentials",
            "assistant": "configured" if ASSISTANT_ID else "missing_id"
        },
        "active_calls": len(active_calls)
    }

@app.post("/calls/outbound", response_model=CallStatusResponse)
async def make_outbound_call_endpoint(
    request: OutboundCallRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger an outbound call to a specific phone number.
    This uses both Vapi for call initiation and LiveKit for agent dispatch.
    """
    try:
        # Use the assistant ID from request or default
        assistant_id = request.assistant_id or ASSISTANT_ID
        
        if not assistant_id:
            raise HTTPException(status_code=400, detail="Assistant ID is required")
        
        logger.info(f"Initiating outbound call to {request.phone_number}")
        
        # Method 1: Use Vapi for call initiation
        vapi_call = make_outbound_call(assistant_id, request.phone_number)
        
        # Method 2: Also prepare LiveKit agent dispatch metadata
        # This allows the LiveKit agent to handle the call with proper context
        call_metadata = {
            "call_type": "outbound",
            "phone_number": request.phone_number,
            "transfer_to": request.transfer_to,
            "vapi_call_id": vapi_call.id if hasattr(vapi_call, 'id') else None,
            "context": request.call_context or {}
        }
        
        # Store call information
        call_id = vapi_call.id if hasattr(vapi_call, 'id') else f"outbound_{len(active_calls)}"
        active_calls[call_id] = {
            "type": "outbound",
            "phone_number": request.phone_number,
            "status": "initiated",
            "metadata": call_metadata,
            "vapi_call": vapi_call
        }
        
        logger.info(f"Outbound call initiated successfully: {call_id}")
        
        return CallStatusResponse(
            success=True,
            message=f"Outbound call initiated to {request.phone_number}",
            call_id=call_id,
            details=call_metadata
        )
        
    except Exception as e:
        logger.error(f"Error making outbound call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

@app.post("/webhooks/inbound")
async def handle_inbound_webhook(request: Request):
    """
    Webhook endpoint for handling inbound call events from Vapi.
    This is called when someone calls your Vapi phone number.
    """
    try:
        # Parse the webhook payload
        payload = await request.json()
        logger.info(f"Received inbound webhook: {payload}")
        
        # Extract call information
        call_id = payload.get("call", {}).get("id", "unknown")
        phone_number = payload.get("call", {}).get("customer", {}).get("number", "unknown")
        status = payload.get("type", "unknown")  # e.g., "call.started", "call.ended"
        
        # Store/update call information
        if call_id not in active_calls:
            active_calls[call_id] = {
                "type": "inbound",
                "phone_number": phone_number,
                "status": status,
                "metadata": payload,
                "webhook_data": payload
            }
        else:
            active_calls[call_id]["status"] = status
            active_calls[call_id]["webhook_data"] = payload
        
        # Handle different webhook events
        if status == "call.started":
            logger.info(f"Inbound call started from {phone_number}")
            # Here you could trigger additional LiveKit agent dispatch if needed
            
        elif status == "call.ended":
            logger.info(f"Inbound call ended from {phone_number}")
            # Clean up or log final call data
            
        elif status == "call.failed":
            logger.warning(f"Inbound call failed from {phone_number}")
            
        # Return success response to Vapi
        return {"success": True, "message": "Webhook processed successfully"}
        
    except Exception as e:
        logger.error(f"Error processing inbound webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")

@app.get("/calls/active")
async def get_active_calls():
    """Get list of currently active calls"""
    return {
        "active_calls": active_calls,
        "count": len(active_calls)
    }

@app.get("/calls/{call_id}")
async def get_call_status(call_id: str):
    """Get status of a specific call"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return active_calls[call_id]

@app.delete("/calls/{call_id}")
async def end_call(call_id: str):
    """End a specific call"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    try:
        # Here you would implement call termination logic
        # This might involve calling Vapi API to end the call
        call_info = active_calls[call_id]
        logger.info(f"Ending call {call_id}")
        
        # Remove from active calls
        del active_calls[call_id]
        
        return {"success": True, "message": f"Call {call_id} ended successfully"}
        
    except Exception as e:
        logger.error(f"Error ending call {call_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to end call: {str(e)}")

@app.post("/calls/configure-inbound")
async def configure_inbound_endpoint():
    """Configure inbound calls for the phone number"""
    try:
        if not PHONE_NUMBER_ID or not ASSISTANT_ID:
            raise HTTPException(
                status_code=400, 
                detail="Phone number ID and Assistant ID are required"
            )
        
        result = configure_inbound_calls(PHONE_NUMBER_ID, ASSISTANT_ID)
        
        return {
            "success": True,
            "message": "Inbound calls configured successfully",
            "phone_number_id": PHONE_NUMBER_ID,
            "assistant_id": ASSISTANT_ID,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error configuring inbound calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to configure: {str(e)}")

# Additional utility endpoints

@app.post("/assistant/create")
async def create_assistant_endpoint():
    """Create a new assistant (wrapper for support_assistant)"""
    try:
        assistant = create_support_assistant()
        return {
            "success": True,
            "message": "Assistant created successfully",
            "assistant": assistant
        }
    except Exception as e:
        logger.error(f"Error creating assistant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create assistant: {str(e)}")

@app.get("/config")
async def get_configuration():
    """Get current configuration (without sensitive data)"""
    return {
        "phone_number_configured": bool(PHONE_NUMBER_ID),
        "assistant_configured": bool(ASSISTANT_ID),
        "vapi_configured": bool(VAPI_TOKEN),
        "livekit_configured": bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET),
        "webhook_url": "/webhooks/inbound"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI app
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
