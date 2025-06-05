#!/usr/bin/env python3
"""
Comprehensive Voice AI Agent Starter
This script starts the voice AI agent with all required services
"""

import asyncio
import logging
import signal
import sys
from test import setup_and_run_agent, background_services

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self):
        self.background_task = None
        self.running = False
        
    async def start(self):
        """Start all agent services"""
        logger.info("🚀 Starting Comprehensive Voice AI Agent...")
        
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialize the agent
            assistant = await setup_and_run_agent()
            logger.info("✅ Assistant initialized successfully")
            
            # Start background services
            self.background_task = asyncio.create_task(background_services())
            logger.info("✅ Background services started")
            
            # Keep the services running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Failed to start agent: {e}")
            raise
        finally:
            await self.cleanup()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, initiating shutdown...")
        self.running = False
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up resources...")
        
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Cleanup completed")

async def main():
    """Main entry point"""
    agent_manager = AgentManager()
    
    try:
        await agent_manager.start()
    except KeyboardInterrupt:
        logger.info("👋 Agent stopped by user")
    except Exception as e:
        logger.error(f"❌ Agent failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
