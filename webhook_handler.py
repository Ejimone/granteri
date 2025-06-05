"""
Webhook handler for Vapi inbound calls.
This module provides webhook handling functionality for inbound calls.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VapiWebhookHandler:
    """Handler for Vapi webhook events"""
    
    def __init__(self):
        self.call_log: Dict[str, Dict[str, Any]] = {}
    
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook from Vapi
        
        Args:
            payload: The webhook payload from Vapi
            
        Returns:
            Response dictionary to send back to Vapi
        """
        try:
            event_type = payload.get("type", "unknown")
            call_data = payload.get("call", {})
            call_id = call_data.get("id", "unknown")
            
            logger.info(f"Processing webhook event: {event_type} for call: {call_id}")
            
            # Store call information
            if call_id not in self.call_log:
                self.call_log[call_id] = {
                    "call_id": call_id,
                    "events": [],
                    "created_at": datetime.now().isoformat()
                }
            
            # Add event to call log
            self.call_log[call_id]["events"].append({
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": payload
            })
            
            # Handle specific event types
            if event_type == "call.started":
                return self._handle_call_started(call_data, payload)
            elif event_type == "call.ended":
                return self._handle_call_ended(call_data, payload)
            elif event_type == "call.failed":
                return self._handle_call_failed(call_data, payload)
            elif event_type == "transcript":
                return self._handle_transcript(call_data, payload)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return {"success": True, "message": "Event received"}
                
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _handle_call_started(self, call_data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call started event"""
        customer_number = call_data.get("customer", {}).get("number", "unknown")
        logger.info(f"Inbound call started from {customer_number}")
        
        # Here you could trigger additional logic:
        # - Lookup customer information
        # - Set call context
        # - Trigger LiveKit agent dispatch if needed
        
        return {
            "success": True,
            "message": "Call started event processed",
            "call_id": call_data.get("id")
        }
    
    def _handle_call_ended(self, call_data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call ended event"""
        call_id = call_data.get("id", "unknown")
        duration = call_data.get("duration", 0)
        
        logger.info(f"Call {call_id} ended after {duration} seconds")
        
        # Here you could:
        # - Save call summary
        # - Update customer records
        # - Send notifications
        
        return {
            "success": True,
            "message": "Call ended event processed",
            "call_id": call_id
        }
    
    def _handle_call_failed(self, call_data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call failed event"""
        call_id = call_data.get("id", "unknown")
        error = payload.get("error", "Unknown error")
        
        logger.error(f"Call {call_id} failed: {error}")
        
        return {
            "success": True,
            "message": "Call failed event processed",
            "call_id": call_id
        }
    
    def _handle_transcript(self, call_data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transcript event"""
        transcript = payload.get("transcript", {})
        text = transcript.get("text", "")
        role = transcript.get("role", "unknown")
        
        logger.info(f"Transcript ({role}): {text}")
        
        return {
            "success": True,
            "message": "Transcript event processed"
        }
    
    def get_call_log(self, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Get call log for a specific call or all calls"""
        if call_id:
            return self.call_log.get(call_id, {})
        return self.call_log
    
    def clear_call_log(self):
        """Clear the call log"""
        self.call_log.clear()


# Global webhook handler instance
webhook_handler = VapiWebhookHandler()


def process_inbound_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple function to process inbound webhooks
    
    Args:
        payload: Webhook payload from Vapi
        
    Returns:
        Response dictionary
    """
    return webhook_handler.handle_webhook(payload)


def get_webhook_url_for_vapi() -> str:
    """
    Get the webhook URL that should be configured in Vapi dashboard
    
    Returns:
        The webhook URL path
    """
    return "/webhooks/inbound"


# Example usage in a simple Flask app (alternative to FastAPI)
def create_simple_webhook_app():
    """Create a simple Flask app for webhook handling (alternative to FastAPI)"""
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/webhooks/inbound', methods=['POST'])
        def handle_inbound():
            payload = request.json
            response = process_inbound_webhook(payload)
            return jsonify(response)
        
        @app.route('/calls/log')
        def get_calls():
            return jsonify(webhook_handler.get_call_log())
        
        @app.route('/health')
        def health():
            return jsonify({"status": "healthy"})
        
        return app
        
    except ImportError:
        logger.warning("Flask not installed. Use FastAPI app instead.")
        return None


if __name__ == "__main__":
    # Example webhook payload for testing
    test_payload = {
        "type": "call.started",
        "call": {
            "id": "test-call-123",
            "customer": {
                "number": "+1234567890"
            }
        }
    }
    
    response = process_inbound_webhook(test_payload)
    print(f"Test webhook response: {response}")
    print(f"Call log: {webhook_handler.get_call_log()}")
