# Comprehensive Voice AI Agent - Handles inbound/outbound calls and live conversations

from dotenv import load_dotenv
import os
import asyncio
import logging
from inbound_calls import configure_inbound_calls
from vapi import Vapi
from support_assistant import create_support_assistant
from make_outbound_call import make_outbound_call

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
    google,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

# Initialize Vapi client
vapi_client = Vapi(token=os.getenv("VAPI_TOKEN"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VapiLiveKitAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""You are Alex, a comprehensive voice AI assistant. 
        You can help with various tasks, answer questions, and maintain natural conversations.
        You are capable of both receiving calls and making outbound calls when requested.
        Always be helpful, friendly, and professional.""")
        
        self.vapi_client = vapi_client
        self.assistant_id = None
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")
        
    async def initialize_vapi_assistant(self):
        """Initialize or get the Vapi assistant for call handling"""
        try:
            # Create support assistant if not exists
            assistant = create_support_assistant()
            self.assistant_id = assistant.id
            logger.info(f"Vapi assistant initialized with ID: {self.assistant_id}")
            
            # Configure inbound calls if phone number is available
            if self.phone_number_id and self.assistant_id:
                configure_inbound_calls(self.phone_number_id, self.assistant_id)
                logger.info("Inbound calls configured successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize Vapi assistant: {e}")
    
    async def make_call(self, phone_number: str):
        """Make an outbound call to a specific number"""
        if not self.assistant_id:
            await self.initialize_vapi_assistant()
            
        try:
            call = make_outbound_call(self.assistant_id, phone_number)
            logger.info(f"Outbound call initiated to {phone_number}")
            return call
        except Exception as e:
            logger.error(f"Failed to make outbound call: {e}")
            return None
        
    async def say(self, message: str, allow_interruptions: bool = True):
        """Make the agent speak a message"""
        logger.info(f"Agent saying: {message}")
        # This would be handled by the LiveKit session in practice
        return message
    
    async def handle_call_request(self, phone_number: str):
        """Handle user request to make a call"""
        if not phone_number:
            return "Please provide a valid phone number to call."
        
        try:
            call = await self.make_call(phone_number)
            if call:
                return f"Successfully initiated call to {phone_number}"
            else:
                return f"Failed to initiate call to {phone_number}"
        except Exception as e:
            logger.error(f"Call request failed: {e}")
            return f"Sorry, I couldn't make the call. Error: {str(e)}"
    
    async def get_call_status(self):
        """Get current call status"""
        if call_manager:
            active_calls = call_manager.get_active_calls()
            if active_calls:
                count = len([c for c in active_calls.values() if c["status"] == "active"])
                return f"I currently have {count} active calls."
            else:
                return "I don't have any active calls right now."
        return "Call management system is not available."


class CallManager:
    """Manages both inbound and outbound call operations"""
    
    def __init__(self, assistant: VapiLiveKitAssistant):
        self.assistant = assistant
        self.active_calls = {}
        
    async def handle_inbound_call(self, call_id: str, caller_number: str):
        """Handle incoming call events"""
        logger.info(f"Handling inbound call {call_id} from {caller_number}")
        self.active_calls[call_id] = {
            "type": "inbound",
            "caller": caller_number,
            "status": "active"
        }
        
    async def initiate_outbound_call(self, target_number: str):
        """Initiate an outbound call"""
        logger.info(f"Initiating outbound call to {target_number}")
        call = await self.assistant.make_call(target_number)
        if call:
            call_id = getattr(call, 'id', str(hash(target_number)))
            self.active_calls[call_id] = {
                "type": "outbound",
                "target": target_number,
                "status": "active"
            }
            return call
        return None
    
    def get_active_calls(self):
        """Get list of currently active calls"""
        return self.active_calls
    
    async def end_call(self, call_id: str):
        """End a specific call"""
        if call_id in self.active_calls:
            self.active_calls[call_id]["status"] = "ended"
            logger.info(f"Call {call_id} ended")


# Global call manager instance
call_manager = None


async def setup_and_run_agent():
    """Initialize and run the comprehensive voice agent"""
    global call_manager
    
    # Create the assistant instance
    assistant = VapiLiveKitAssistant()
    
    # Initialize Vapi components
    await assistant.initialize_vapi_assistant()
    
    # Initialize call manager
    call_manager = CallManager(assistant)
    
    return assistant


async def entrypoint(ctx: agents.JobContext):
    # Setup the assistant
    assistant = await setup_and_run_agent()
    
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.0-flash-lite"),
        tts=deepgram.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Hello! I'm Alex, your voice AI assistant. I'm ready to help you with any questions or tasks. I can also make and receive phone calls when needed. How can I assist you today?"
    )


async def background_services():
    """Background services for monitoring and managing calls"""
    logger.info("Background services started - monitoring for calls and system status")
    
    while True:
        try:
            # Monitor system health
            await asyncio.sleep(30)  # Check every 30 seconds
            
            # You can add more background tasks here such as:
            # - Monitoring call queue
            # - Health checks
            # - Periodic status updates
            
        except Exception as e:
            logger.error(f"Background service error: {e}")
            await asyncio.sleep(5)  # Brief pause before retrying


async def run_comprehensive_agent():
    """Main function to run the comprehensive agent with all services"""
    logger.info("Starting comprehensive voice AI agent...")
    
    # Start background services
    background_task = asyncio.create_task(background_services())
    
    try:
        # Run the main agent using LiveKit's CLI
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        logger.info("Shutting down agent...")
        background_task.cancel()
    except Exception as e:
        logger.error(f"Agent error: {e}")
        background_task.cancel()
        raise


if __name__ == "__main__":
    # For development, you can run the agent directly
    # In production, use: python -m livekit.agents.cli dev test.py
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed to start: {e}")