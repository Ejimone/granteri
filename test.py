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
        self.call_history = []
        self.start_time = asyncio.get_event_loop().time()
        
    async def handle_inbound_call(self, call_id: str, caller_number: str):
        """Handle incoming call events"""
        current_time = asyncio.get_event_loop().time()
        logger.info(f"Handling inbound call {call_id} from {caller_number}")
        
        call_info = {
            "type": "inbound",
            "caller": caller_number,
            "status": "active",
            "start_time": current_time,
            "duration": 0
        }
        
        self.active_calls[call_id] = call_info
        self.call_history.append({**call_info, "call_id": call_id, "event": "started"})
        
    async def initiate_outbound_call(self, target_number: str):
        """Initiate an outbound call"""
        current_time = asyncio.get_event_loop().time()
        logger.info(f"Initiating outbound call to {target_number}")
        
        try:
            call = await self.assistant.make_call(target_number)
            if call:
                call_id = getattr(call, 'id', str(hash(target_number)))
                call_info = {
                    "type": "outbound",
                    "target": target_number,
                    "status": "active",
                    "start_time": current_time,
                    "duration": 0
                }
                
                self.active_calls[call_id] = call_info
                self.call_history.append({**call_info, "call_id": call_id, "event": "started"})
                return call
            else:
                # Record failed call attempt
                self.call_history.append({
                    "type": "outbound",
                    "target": target_number,
                    "status": "failed",
                    "start_time": current_time,
                    "duration": 0,
                    "call_id": f"failed_{hash(target_number)}",
                    "event": "failed"
                })
        except Exception as e:
            logger.error(f"Outbound call failed: {e}")
            self.call_history.append({
                "type": "outbound",
                "target": target_number,
                "status": "failed",
                "start_time": current_time,
                "duration": 0,
                "call_id": f"error_{hash(target_number)}",
                "event": "error",
                "error": str(e)
            })
        return None
    
    def get_active_calls(self):
        """Get list of currently active calls with updated durations"""
        current_time = asyncio.get_event_loop().time()
        
        # Update durations for active calls
        for call_id, call_info in self.active_calls.items():
            if call_info["status"] == "active":
                call_info["duration"] = current_time - call_info["start_time"]
        
        return self.active_calls
    
    async def end_call(self, call_id: str, reason: str = "completed"):
        """End a specific call"""
        current_time = asyncio.get_event_loop().time()
        
        if call_id in self.active_calls:
            call_info = self.active_calls[call_id]
            call_info["status"] = "ended"
            call_info["end_time"] = current_time
            call_info["duration"] = current_time - call_info["start_time"]
            
            # Add to history
            self.call_history.append({
                **call_info,
                "call_id": call_id,
                "event": "ended",
                "reason": reason
            })
            
            logger.info(f"Call {call_id} ended after {call_info['duration']:.1f} seconds - {reason}")
    
    def get_call_statistics(self):
        """Get comprehensive call statistics"""
        current_time = asyncio.get_event_loop().time()
        uptime = current_time - self.start_time
        
        active_calls = [c for c in self.active_calls.values() if c["status"] == "active"]
        total_calls = len(self.call_history)
        successful_calls = len([c for c in self.call_history if c["status"] not in ["failed", "error"]])
        failed_calls = len([c for c in self.call_history if c["status"] in ["failed", "error"]])
        
        return {
            "uptime_seconds": uptime,
            "active_calls": len(active_calls),
            "total_calls_handled": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
            "average_call_duration": sum(c.get("duration", 0) for c in self.call_history) / len(self.call_history) if self.call_history else 0
        }


async def system_alert(message: str, level: str = "info"):
    """Send system alerts for important events"""
    timestamp = asyncio.get_event_loop().time()
    alert_emoji = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
        "critical": "🚨"
    }
    
    emoji = alert_emoji.get(level, "📢")
    formatted_message = f"{emoji} [{level.upper()}] {message}"
    
    if level == "critical":
        logger.critical(formatted_message)
    elif level == "error":
        logger.error(formatted_message)
    elif level == "warning":
        logger.warning(formatted_message)
    else:
        logger.info(formatted_message)
    
    # In a production environment, you could send alerts to:
    # - Slack/Discord webhooks
    # - Email notifications
    # - SMS alerts
    # - Monitoring dashboards


async def cleanup_old_call_data():
    """Clean up old call data to prevent memory issues"""
    try:
        if call_manager and hasattr(call_manager, 'call_history'):
            current_time = asyncio.get_event_loop().time()
            
            # Keep only last 24 hours of call history
            cutoff_time = current_time - (24 * 60 * 60)  # 24 hours ago
            
            old_count = len(call_manager.call_history)
            call_manager.call_history = [
                call for call in call_manager.call_history 
                if call.get("start_time", current_time) > cutoff_time
            ]
            new_count = len(call_manager.call_history)
            
            if old_count > new_count:
                logger.info(f"🧹 Cleaned up {old_count - new_count} old call records")
                
            # Clean up ended calls from active_calls
            ended_calls = [
                call_id for call_id, call_info in call_manager.active_calls.items()
                if call_info["status"] == "ended" and 
                call_info.get("end_time", current_time) < cutoff_time
            ]
            
            for call_id in ended_calls:
                del call_manager.active_calls[call_id]
                
            if ended_calls:
                logger.info(f"🧹 Removed {len(ended_calls)} old ended calls from active tracking")
                
    except Exception as e:
        logger.error(f"Error during call data cleanup: {e}")


async def monitor_system_resources():
    """Monitor system resource usage"""
    try:
        import psutil
        
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Log resource usage if high
        if cpu_percent > 80:
            await system_alert(f"High CPU usage detected: {cpu_percent}%", "warning")
        
        if memory.percent > 85:
            await system_alert(f"High memory usage detected: {memory.percent}%", "warning")
        
        # Log normal status every hour
        current_time = asyncio.get_event_loop().time()
        if not hasattr(monitor_system_resources, 'last_resource_log'):
            monitor_system_resources.last_resource_log = 0
            
        if current_time - monitor_system_resources.last_resource_log > 3600:  # 1 hour
            logger.info(f"📊 System Resources - CPU: {cpu_percent}%, Memory: {memory.percent}%")
            monitor_system_resources.last_resource_log = current_time
            
    except ImportError:
        # psutil not available, skip resource monitoring
        pass
    except Exception as e:
        logger.error(f"Resource monitoring error: {e}")


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
    
    last_health_check = 0
    last_status_update = 0
    last_call_queue_check = 0
    last_cleanup = 0
    last_resource_check = 0
    
    while True:
        try:
            current_time = asyncio.get_event_loop().time()
            
            # Monitor call queue every 10 seconds
            if current_time - last_call_queue_check >= 10:
                await monitor_call_queue()
                last_call_queue_check = current_time
            
            # Perform health checks every 30 seconds
            if current_time - last_health_check >= 30:
                await perform_health_checks()
                last_health_check = current_time
            
            # Monitor system resources every 2 minutes
            if current_time - last_resource_check >= 120:
                await monitor_system_resources()
                last_resource_check = current_time
            
            # Periodic status updates every 60 seconds
            if current_time - last_status_update >= 60:
                await periodic_status_update()
                last_status_update = current_time
            
            # Cleanup old data every hour
            if current_time - last_cleanup >= 3600:
                await cleanup_old_call_data()
                last_cleanup = current_time
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            logger.error(f"Background service error: {e}")
            await system_alert(f"Background service error: {e}", "error")
            await asyncio.sleep(5)  # Brief pause before retrying


async def monitor_call_queue():
    """Monitor call queue for incoming and outgoing calls"""
    try:
        if call_manager:
            active_calls = call_manager.get_active_calls()
            
            # Check for stale calls (longer than 30 minutes)
            current_time = asyncio.get_event_loop().time()
            stale_calls = []
            
            for call_id, call_info in active_calls.items():
                if call_info.get("status") == "active":
                    call_start_time = call_info.get("start_time", current_time)
                    if current_time - call_start_time > 1800:  # 30 minutes
                        stale_calls.append(call_id)
            
            # Log stale calls
            if stale_calls:
                logger.warning(f"Found {len(stale_calls)} stale calls: {stale_calls}")
            
            # Monitor queue size
            active_count = len([c for c in active_calls.values() if c["status"] == "active"])
            if active_count > 10:  # Alert if more than 10 active calls
                logger.warning(f"High call volume detected: {active_count} active calls")
            
            # Check for failed calls
            failed_calls = [c for c in active_calls.values() if c["status"] == "failed"]
            if failed_calls:
                logger.warning(f"Found {len(failed_calls)} failed calls in the last period")
                
    except Exception as e:
        logger.error(f"Call queue monitoring error: {e}")


async def perform_health_checks():
    """Perform comprehensive health checks on the system"""
    try:
        health_status = {
            "vapi_connection": False,
            "assistant_available": False,
            "phone_number_configured": False,
            "call_manager_active": False,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Check Vapi connection
        try:
            if vapi_client:
                # Try to list assistants to test connection
                assistants = vapi_client.assistants.list(limit=1)
                health_status["vapi_connection"] = True
        except Exception as e:
            logger.error(f"Vapi connection health check failed: {e}")
        
        # Check assistant availability
        if call_manager and call_manager.assistant.assistant_id:
            health_status["assistant_available"] = True
        
        # Check phone number configuration
        phone_number_id = os.getenv("PHONE_NUMBER_ID")
        if phone_number_id:
            health_status["phone_number_configured"] = True
        
        # Check call manager
        if call_manager:
            health_status["call_manager_active"] = True
        
        # Log health status
        healthy_services = sum(health_status.values() if isinstance(v, bool) else 0 for v in health_status.values())
        total_services = len([v for v in health_status.values() if isinstance(v, bool)])
        
        if healthy_services == total_services:
            logger.info(f"✅ All systems healthy ({healthy_services}/{total_services})")
        else:
            logger.warning(f"⚠️  System health: {healthy_services}/{total_services} services healthy")
            for service, status in health_status.items():
                if isinstance(status, bool) and not status:
                    logger.warning(f"❌ {service}: Not healthy")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"error": str(e)}


async def periodic_status_update():
    """Provide periodic status updates on system operations"""
    try:
        current_time = asyncio.get_event_loop().time()
        
        status_report = {
            "timestamp": current_time,
            "uptime_seconds": current_time,
            "active_calls": 0,
            "total_calls_handled": 0,
            "system_health": "unknown",
            "success_rate": 0,
            "average_call_duration": 0
        }
        
        if call_manager:
            # Get detailed call statistics
            call_stats = call_manager.get_call_statistics()
            status_report.update({
                "active_calls": call_stats["active_calls"],
                "total_calls_handled": call_stats["total_calls_handled"],
                "success_rate": call_stats["success_rate"],
                "average_call_duration": call_stats["average_call_duration"],
                "uptime_seconds": call_stats["uptime_seconds"]
            })
        
        # Get recent health status
        health_status = await perform_health_checks()
        if isinstance(health_status, dict) and "error" not in health_status:
            healthy_count = sum(1 for v in health_status.values() if isinstance(v, bool) and v)
            total_count = len([v for v in health_status.values() if isinstance(v, bool)])
            status_report["system_health"] = f"{healthy_count}/{total_count}"
        
        # Format uptime for readability
        uptime_hours = status_report["uptime_seconds"] / 3600
        uptime_str = f"{uptime_hours:.1f}h" if uptime_hours >= 1 else f"{status_report['uptime_seconds']/60:.1f}m"
        
        # Log comprehensive status report
        logger.info(f"📊 Status Report - Uptime: {uptime_str}, "
                   f"Active: {status_report['active_calls']}, "
                   f"Total: {status_report['total_calls_handled']}, "
                   f"Success: {status_report['success_rate']:.1f}%, "
                   f"Avg Duration: {status_report['average_call_duration']:.1f}s, "
                   f"Health: {status_report['system_health']}")
        
        # Generate alerts based on metrics
        if status_report["active_calls"] > 15:
            await system_alert(f"High call volume: {status_report['active_calls']} active calls", "warning")
        
        if status_report["success_rate"] < 90 and status_report["total_calls_handled"] > 10:
            await system_alert(f"Low success rate: {status_report['success_rate']:.1f}%", "warning")
        
        if status_report["average_call_duration"] > 600:  # 10 minutes
            await system_alert(f"Long average call duration: {status_report['average_call_duration']:.1f}s", "info")
        
        return status_report
        
    except Exception as e:
        logger.error(f"Status update error: {e}")
        await system_alert(f"Status update failed: {e}", "error")
        return {"error": str(e)}


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