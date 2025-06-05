from __future__ import annotations
# Agent that can handle both inbound and outbound calls
# Outbound calls are only made when explicitly requested
# Inbound calls are handled via webhooks and LiveKit dispatching

import asyncio
import logging
import json
import os
from typing import Any, Optional
from dotenv import load_dotenv

from livekit import rtc, api
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    function_tool,
    RunContext,
    get_job_context,
    cli,
    WorkerOptions,
    RoomInputOptions,
)
from livekit.plugins import (
    deepgram,
    openai,
    cartesia,
    silero,
    noise_cancellation,
)
from livekit.plugins import google
from livekit.plugins.turn_detector.english import EnglishModel

# Import our modular functions
from make_outbound_call import make_outbound_call
from inbound_calls import configure_inbound_calls

# Load environment variables
load_dotenv(dotenv_path=".env")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
console_user = "+13613144340"


class VoiceAgent(Agent):
    """
    A voice agent that can handle both inbound and outbound calls.
    The agent adapts its behavior based on call type and context.
    """
    def __init__(
        self,
        *,
        name: str = "Assistant",
        call_type: str = "inbound",  # "inbound" or "outbound"
        context_data: Optional[dict[str, Any]] = None,
    ):
        # Dynamic instructions based on call type
        if call_type == "outbound":
            instructions = f"""
            You are {name}, a scheduling assistant for a dental practice and hospital reception. Your interface with user will be voice.
            You are making an OUTBOUND call to a patient who has an upcoming appointment. Your goal is to confirm the appointment details.
            Be polite and professional. Start by introducing yourself and the reason for your call.
            
            When the user would like to be transferred to a human agent, first confirm with them, then use the transfer_call tool.
            Ask the user their name and appointment details to confirm.
            """
        else:  # inbound
            instructions = f"""
            You are {name}, a helpful assistant for a dental practice and hospital reception. Your interface with user will be voice.
            A patient is calling YOU (inbound call). Greet them warmly and ask how you can help them today.
            You can help with appointment scheduling, questions, and general support.
            
            When the user would like to be transferred to a human agent, first confirm with them, then use the transfer_call tool.
            """
        
        super().__init__(instructions=instructions)
        
        self.participant: Optional[rtc.Participant] = None
        self.call_type = call_type
        self.context_data = context_data or {}
        self.name = name

    def set_participant(self, participant: rtc.Participant):
        """Set the participant for this agent session"""
        self.participant = participant

    def get_transfer_number(self) -> Optional[str]:
        """Get transfer number from context data"""
        return self.context_data.get("transfer_to")

    async def hangup(self):
        """Helper function to hang up the call by deleting the room"""
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=job_ctx.room.name)
        )

    @function_tool()
    async def transfer_call(self, ctx: RunContext):
        """Transfer the call to a human agent, called after confirming with the user"""
        
        transfer_to = self.get_transfer_number()
        if not transfer_to:
            await ctx.session.generate_reply(
                instructions="I don't have a number to transfer you to. Please contact support."
            )
            return "cannot transfer call, no transfer number configured"

        if self.participant is None:
            logger.error("Transfer call error: participant is None.")
            await ctx.session.generate_reply(
                instructions="Sorry, I cannot transfer the call right now as participant details are missing."
            )
            return "cannot transfer call, participant not available"

        p_identity = self.participant.identity

        # Check if participant_identity is a string. In console mode, it might be a MagicMock.
        if not isinstance(p_identity, str):
            # If in console mode and identity is a mock
            if self.context_data.get("phone_number") == "console_user":
                logger.warning(
                    f"Cannot perform real SIP transfer in console mode with mock participant identity: {p_identity}. Simulating transfer."
                )
                await ctx.session.generate_reply(
                    instructions=f"I will simulate transferring you to {transfer_to} now. In a real call, you would be connected."
                )
                return "simulated transfer for console mode"
            else:
                logger.error(
                    f"Transfer call error: participant identity is not a string ('{type(p_identity)}'). Cannot transfer."
                )
                await ctx.session.generate_reply(
                    instructions="Sorry, there was an unexpected issue with the participant information, and I can't transfer the call."
                )
                return "cannot transfer call, invalid participant identity type"

        logger.info(f"transferring call to {transfer_to} for participant {p_identity}")

        # Let the message play fully before transferring
        await ctx.session.generate_reply(
            instructions="Let the user know you'll be transferring them."
        )

        job_ctx = get_job_context()
        try:
            await job_ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=job_ctx.room.name,
                    participant_identity=p_identity,
                    transfer_to=f"tel:{transfer_to}",
                )
            )
            logger.info(f"transferred call to {transfer_to}")
        except Exception as e:
            logger.error(f"error transferring call: {e}")
            await ctx.session.generate_reply(
                instructions="There was an error transferring the call."
            )
            await self.hangup()  # Hang up if transfer fails

    @function_tool()
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        if self.participant is None:
            logger.info("Ending call, but participant was not set.")
        else:
            logger.info(f"ending the call for {self.participant.identity}")

        # Let the agent finish speaking
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await self.hangup()

    @function_tool()
    async def look_up_availability(self, ctx: RunContext, date: str):
        """Called when the user asks about alternative appointment availability
        
        Args:
            date: The date of the appointment to check availability for
        """
        participant_id_for_log = "unknown_participant"
        if self.participant:
            participant_id_for_log = self.participant.identity
        logger.info(f"looking up availability for {participant_id_for_log} on {date}")
        await asyncio.sleep(3)
        return {"available_times": ["1pm", "2pm", "3pm"]}

    @function_tool()
    async def confirm_appointment(self, ctx: RunContext, date: str, time: str):
        """Called when the user confirms their appointment on a specific date.
        Use this tool only when they are certain about the date and time.
        
        Args:
            date: The date of the appointment
            time: The time of the appointment
        """
        participant_id_for_log = "unknown_participant"
        if self.participant:
            participant_id_for_log = self.participant.identity
        logger.info(f"confirming appointment for {participant_id_for_log} on {date} at {time}")
        return "reservation confirmed"

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        """Called when the call reaches voicemail. Use this tool AFTER you hear the voicemail greeting"""
        participant_id_for_log = "unknown_participant"
        if self.participant:
            participant_id_for_log = self.participant.identity
        logger.info(f"detected answering machine for {participant_id_for_log}")
        await self.hangup()


async def entrypoint(ctx: JobContext):
    """
    Entry point for the LiveKit agent.
    Handles both inbound and outbound call contexts.
    """
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()

    # Parse metadata to determine call type and context
    context_data: dict[str, Any] = {}
    call_type = "inbound"  # Default to inbound
    
    if ctx.job.metadata:
        try:
            context_data = json.loads(ctx.job.metadata)
            call_type = context_data.get("call_type", "inbound")
        except json.JSONDecodeError:
            logger.warning("Failed to parse job metadata. Using defaults for inbound call.")
            context_data = {
                "phone_number": "unknown",
                "transfer_to": "+917204218098",
                "call_type": "inbound"
            }
    else:
        logger.info("No job metadata found. Defaulting to inbound call mode.")
        context_data = {
            "phone_number": "unknown", 
            "transfer_to": "+917204218098",
            "call_type": "inbound"
        }

    # Create agent with appropriate configuration
    agent = VoiceAgent(
        name="Jayden",
        call_type=call_type,
        context_data=context_data,
    )

    # Configure the session with AI models
    session = AgentSession(
        turn_detection=EnglishModel(),
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        tts=deepgram.TTS(),
        llm=google.LLM(model="gemini-2.0-flash-lite")
    )

    # Start the session
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVCTelephony(),
            ),
        )
    )

    # Handle outbound calls - only create SIP participant if this is an outbound call
    phone_number = context_data.get("phone_number", "unknown")
    participant_identity = phone_number
    
    try:
        if call_type == "outbound" and phone_number != "console_user" and phone_number != "unknown":
            # This is an explicit outbound call request
            logger.info(f"Making outbound call to {phone_number}")
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=outbound_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=participant_identity,
                    wait_until_answered=True,
                )
            )
        elif phone_number == "console_user":
            # Console mode for testing
            logger.info("Console mode detected")
        else:
            # Inbound call - participant will join automatically
            logger.info("Waiting for inbound call participant to join")

        # Wait for session to start
        await session_started
        
        # Set the participant once connected
        if phone_number == "console_user":
            logger.info("Console mode: Setting agent participant to local participant.")
            if ctx.room and ctx.room.local_participant:
                agent.set_participant(ctx.room.local_participant)
                logger.info(f"Agent participant set for console mode.")
            else:
                logger.warning("Console mode: local_participant not found.")
        else:
            # Wait for the participant to join (either inbound caller or outbound callee)
            participant = await ctx.wait_for_participant(identity=participant_identity)
            logger.info(f"participant joined: {participant.identity}")
            agent.set_participant(participant)

    except api.TwirpError as e:
        logger.error(
            f"error with SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        ctx.shutdown()


# Function to explicitly make an outbound call (can be called from external scripts)
async def make_explicit_outbound_call(phone_number: str, transfer_to: str = "+917204218098"):
    """
    Function to explicitly make an outbound call.
    This should be called from external scripts or APIs, not automatically.
    """
    from livekit.agents import JobRequest
    
    metadata = json.dumps({
        "call_type": "outbound",
        "phone_number": phone_number,
        "transfer_to": transfer_to
    })
    
    # This would typically be called by LiveKit's job dispatcher
    logger.info(f"Requesting outbound call to {phone_number}")
    return metadata


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-agent",
        )
    )