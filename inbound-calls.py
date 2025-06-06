#!/usr/bin/env python3
"""
LiveKit Inbound Call Handler
This script sets up inbound call handling for a LiveKit voice agent.
It ensures SIP trunks and dispatch rules are properly configured.
"""

import asyncio
import os
import json
import subprocess
from dotenv import load_dotenv
from livekit import api

# Load environment variables from .env file
load_dotenv(override=True)

class InboundCallSetup:
    def __init__(self):
        self.livekit_api = api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
        self.agent_name = "voice-agent"  # Must match the agent name in agent.py
        
    async def list_existing_trunks(self):
        """List all existing SIP inbound trunks"""
        print("📋 Listing existing SIP inbound trunks...")
        list_request = api.ListSIPInboundTrunkRequest()
        existing_trunks = await self.livekit_api.sip.list_sip_inbound_trunk(list_request)
        
        print(f"Found {len(existing_trunks.items)} existing trunk(s):")
        for trunk in existing_trunks.items:
            print(f"  - Trunk ID: {trunk.sip_trunk_id}")
            print(f"    Name: {trunk.name}")
            print(f"    Numbers: {trunk.numbers}")
            print(f"    Krisp enabled: {trunk.krisp_enabled}")
        print()
        
        return existing_trunks.items

    async def ensure_trunk_exists(self, phone_number: str = "+15105550100"):
        """Ensure a trunk exists for the given phone number"""
        existing_trunks = await self.list_existing_trunks()
        
        # Check if the desired phone number is already in use
        existing_trunk_with_number = None
        for trunk in existing_trunks:
            if phone_number in trunk.numbers:
                existing_trunk_with_number = trunk
                break
        
        if existing_trunk_with_number:
            print(f"✅ Phone number {phone_number} is already configured in trunk:")
            print(f"   ID: {existing_trunk_with_number.sip_trunk_id}")
            print(f"   Name: {existing_trunk_with_number.name}")
            return existing_trunk_with_number.sip_trunk_id
        else:
            print(f"📞 Creating new trunk with number {phone_number}...")
            trunk_info = api.SIPInboundTrunkInfo(
                name="Voice Agent Inbound Trunk",
                numbers=[phone_number],
                krisp_enabled=True,
            )

            request = api.CreateSIPInboundTrunkRequest(trunk=trunk_info)
            new_trunk = await self.livekit_api.sip.create_sip_inbound_trunk(request)
            print(f"✅ Created new trunk: {new_trunk.sip_trunk_id}")
            return new_trunk.sip_trunk_id

    async def list_dispatch_rules(self):
        """List existing dispatch rules"""
        print("📋 Listing existing dispatch rules...")
        try:
            list_request = api.ListSIPDispatchRuleRequest()
            dispatch_rules = await self.livekit_api.sip.list_sip_dispatch_rule(list_request)
            
            print(f"Found {len(dispatch_rules.items)} dispatch rule(s):")
            for rule in dispatch_rules.items:
                print(f"  - Rule ID: {rule.sip_dispatch_rule_id}")
                print(f"    Name: {rule.name}")
                print(f"    Trunk IDs: {rule.trunk_ids}")
                print(f"    Hide phone number: {rule.hide_phone_number}")
            print()
            
            return dispatch_rules.items
        except Exception as e:
            print(f"⚠️  Could not list dispatch rules: {e}")
            return []

    async def create_dispatch_rule(self, trunk_id: str):
        """Create a dispatch rule for inbound calls"""
        print(f"🔄 Creating dispatch rule for trunk {trunk_id}...")
        
        # Create dispatch rule using the correct structure
        dispatch_rule = api.SIPDispatchRule(
            dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                room_prefix="call-",
                pin=""
            )
        )
        
        # Room configuration that includes our agent (using explicit dispatch)
        room_config = api.RoomConfiguration(
            max_participants=10,
            agents=[
                api.RoomAgentDispatch(
                    agent_name=self.agent_name,  # This enables explicit dispatch
                    metadata=json.dumps({
                        "call_type": "inbound",
                        "transfer_to": os.getenv("TECH_SUPPORT_PHONE_NUMBER", "+917204218098")
                    })
                )
            ]
        )

        request = api.CreateSIPDispatchRuleRequest(
            name="Voice Agent Dispatch Rule",
            trunk_ids=[trunk_id],
            hide_phone_number=False,
            rule=dispatch_rule,
            room_config=room_config
        )
        
        try:
            new_rule = await self.livekit_api.sip.create_sip_dispatch_rule(request)
            print(f"✅ Created dispatch rule: {new_rule.sip_dispatch_rule_id}")
            return new_rule.sip_dispatch_rule_id
        except Exception as e:
            print(f"❌ Failed to create dispatch rule: {e}")
            return None

    async def ensure_dispatch_rule_exists(self, trunk_id: str):
        """Ensure a dispatch rule exists for the trunk"""
        existing_rules = await self.list_dispatch_rules()
        
        # Check if we already have a rule for this trunk
        existing_rule = None
        for rule in existing_rules:
            if trunk_id in rule.trunk_ids:
                existing_rule = rule
                break
        
        if existing_rule:
            print(f"✅ Dispatch rule already exists for trunk {trunk_id}:")
            print(f"   Rule ID: {existing_rule.sip_dispatch_rule_id}")
            print(f"   Name: {existing_rule.name}")
            return existing_rule.sip_dispatch_rule_id
        else:
            return await self.create_dispatch_rule(trunk_id)

    def check_agent_running(self):
        """Check if the voice agent is running"""
        print("🔍 Checking if voice agent is running...")
        
        # Check if agent.py process is running
        try:
            result = subprocess.run(
                ["pgrep", "-f", "agent.py"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Voice agent appears to be running!")
                return True
            else:
                print("⚠️  Voice agent is not running.")
                print("💡 To start the agent, run: python agent.py dev")
                return False
        except Exception as e:
            print(f"⚠️  Could not check agent status: {e}")
            return False

    def verify_agent_setup(self):
        """Verify that the agent is properly configured for inbound calls"""
        print("🔍 Verifying agent configuration...")
        
        # Check if agent.py file exists
        if not os.path.exists("agent.py"):
            print("❌ agent.py file not found!")
            return False
        
        # Check if agent.py contains the required agent name
        try:
            with open("agent.py", "r") as f:
                content = f.read()
                if f'agent_name="{self.agent_name}"' in content:
                    print(f"✅ Agent file contains correct agent_name: {self.agent_name}")
                    
                    # Check for required imports and patterns
                    required_patterns = [
                        "from livekit.agents import",
                        "def entrypoint",
                        "cli.run_app"
                    ]
                    
                    missing_patterns = []
                    for pattern in required_patterns:
                        if pattern not in content:
                            missing_patterns.append(pattern)
                    
                    if missing_patterns:
                        print("⚠️  Agent file may be missing some required patterns:")
                        for pattern in missing_patterns:
                            print(f"   - {pattern}")
                        return False
                    else:
                        print("✅ Agent file appears to be properly structured")
                        return True
                else:
                    print(f"⚠️  Agent file does not contain agent_name='{self.agent_name}'")
                    print("💡 Make sure your agent.py uses explicit dispatch with the correct name")
                    return False
        except Exception as e:
            print(f"❌ Error reading agent.py: {e}")
            return False

    async def setup_inbound_calls(self, phone_number: str = "+15105550100"):
        """Complete setup for inbound call handling"""
        print("🚀 Setting up inbound call handling...")
        
        # Validate phone number
        if not phone_number or phone_number.strip() == "":
            print("❌ Error: Phone number is empty or not set!")
            print("💡 Please set PHONE_NUMBER in your .env file")
            print("   Example: PHONE_NUMBER='+15105550100'")
            return False
        
        print(f"📞 Phone number: {phone_number}")
        print(f"🤖 Agent name: {self.agent_name}")
        print()
        
        try:
            # Step 1: Ensure trunk exists
            trunk_id = await self.ensure_trunk_exists(phone_number)
            
            # Step 2: Ensure dispatch rule exists
            rule_id = await self.ensure_dispatch_rule_exists(trunk_id)
            
            if rule_id:
                print()
                print("🎉 Inbound call setup completed successfully!")
                print()
                print("📋 Summary:")
                print(f"   📞 Phone Number: {phone_number}")
                print(f"   🏗️  Trunk ID: {trunk_id}")
                print(f"   📨 Dispatch Rule ID: {rule_id}")
                print(f"   🤖 Agent Name: {self.agent_name}")
                print()
                
                # Step 3: Verify agent configuration
                agent_config_ok = self.verify_agent_setup()
                
                # Step 4: Check if agent is running
                agent_running = self.check_agent_running()
                
                if agent_config_ok and agent_running:
                    print("✅ System is ready to receive calls!")
                    print(f"📞 Call {phone_number} to test your voice agent.")
                elif agent_config_ok and not agent_running:
                    print("⚠️  Agent is configured correctly but not running.")
                    print("⚠️  To complete setup, start your voice agent:")
                    print("   python agent.py dev")
                    print()
                    print(f"Then you can call your agent at: {phone_number}")
                else:
                    print("❌ Agent configuration issues detected.")
                    print("💡 Please fix the agent configuration before starting it.")
                
                return True
            else:
                print("❌ Failed to create dispatch rule. Setup incomplete.")
                return False
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        await self.livekit_api.aclose()

async def main():
    """Main function to set up inbound call handling"""
    import sys
    
    # Check if user wants to see status only
    if len(sys.argv) > 1 and sys.argv[1] in ['--status', '-s', 'status']:
        await show_status()
        return
    
    setup = InboundCallSetup()
    
    try:
        # Use the phone number from your .env or default
        phone_number = os.getenv("PHONE_NUMBER", "+15105550100")
        success = await setup.setup_inbound_calls(phone_number)
        
        if success:
            print("\n🎯 Next steps:")
            print("1. Make sure your agent is running: python agent.py dev")
            print(f"2. Call {phone_number} to test your voice agent")
            print("3. Check LiveKit dashboard for call logs and metrics")
            print("\n💡 Tip: Run 'python inbound-calls.py status' to check system status anytime")
        
    except KeyboardInterrupt:
        print("\n⏹️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        await setup.cleanup()
        print("\n✅ Cleanup completed")

async def show_status():
    """Show current system status"""
    setup = InboundCallSetup()
    try:
        print("📊 LiveKit Inbound Call System Status")
        print("=" * 50)
        
        # Check phone number
        phone_number = os.getenv("PHONE_NUMBER", "+15105550100")
        print(f"📞 Configured Phone Number: {phone_number}")
        
        # Check trunks
        existing_trunks = await setup.list_existing_trunks()
        trunk_found = False
        for trunk in existing_trunks:
            if phone_number in trunk.numbers:
                print(f"✅ SIP Trunk: {trunk.sip_trunk_id} ({trunk.name})")
                trunk_found = True
                break
        
        if not trunk_found:
            print("❌ No SIP trunk found for this phone number")
            return
        
        # Check dispatch rules
        existing_rules = await setup.list_dispatch_rules()
        rule_found = False
        for rule in existing_rules:
            if any(trunk.sip_trunk_id in rule.trunk_ids for trunk in existing_trunks if phone_number in trunk.numbers):
                print(f"✅ Dispatch Rule: {rule.sip_dispatch_rule_id} ({rule.name or 'Unnamed'})")
                rule_found = True
                break
        
        if not rule_found:
            print("❌ No dispatch rule found for this phone number")
            return
        
        # Check agent configuration
        agent_config_ok = setup.verify_agent_setup()
        if agent_config_ok:
            print("✅ Agent Configuration: Properly configured")
        else:
            print("❌ Agent Configuration: Issues detected")
        
        # Check if agent is running
        agent_running = setup.check_agent_running()
        if agent_running:
            print("✅ Agent Status: Running and ready")
            print()
            print(f"🎉 System is fully operational! Call {phone_number} to test.")
        else:
            print("⚠️  Agent Status: Not running")
            print()
            print("🚀 To start the agent: python agent.py dev")
        
    finally:
        await setup.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
