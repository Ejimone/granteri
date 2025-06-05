# Comprehensive Voice AI Agent

This is a comprehensive voice AI agent that combines LiveKit real-time conversation capabilities with Vapi's phone call management system.

## Features

- 🎙️ **Real-time Voice Conversations**: Powered by LiveKit with Google Gemini, Deepgram STT/TTS
- 📞 **Inbound Call Handling**: Automatically receives and handles incoming phone calls via Vapi
- 📱 **Outbound Call Management**: Can initiate calls to specific phone numbers
- 🤖 **Intelligent Assistant**: Alex, a customer service voice assistant with natural conversation abilities
- 🔄 **Background Services**: Continuous monitoring and health checks
- 🛡️ **Error Handling**: Robust error handling and logging

## Setup

1. **Environment Variables**: Create a `.env` file with:

   ```
   VAPI_TOKEN=your_vapi_token
   PHONE_NUMBER_ID=your_phone_number_id
   ASSISTANT_ID=your_assistant_id
   ```

2. **Install Dependencies**: Make sure you have all required packages installed:
   ```bash
   pip install vapi-python livekit-agents livekit-plugins-deepgram livekit-plugins-google python-dotenv
   ```

## Running the Agent

### Method 1: LiveKit Development Mode (Recommended)

```bash
python -m livekit.agents.cli dev test.py
```

### Method 2: Direct Execution

```bash
python test.py
```

### Method 3: Full Service Manager

```bash
python start_agent.py
```

## How It Works

### Core Components

1. **VapiLiveKitAssistant**: Main agent class that combines LiveKit and Vapi functionality
2. **CallManager**: Handles both inbound and outbound call operations
3. **Background Services**: Monitors system health and manages ongoing operations

### Call Flow

**Inbound Calls:**

1. Vapi receives the call on your configured phone number
2. The call is routed to your assistant
3. LiveKit handles the real-time conversation
4. CallManager tracks the call status

**Outbound Calls:**

1. Agent receives a request to make a call
2. Uses Vapi to initiate the call
3. CallManager tracks the outbound call
4. LiveKit manages the conversation

### Voice Capabilities

- **Speech Recognition**: Deepgram Nova-3 with multilingual support
- **Text-to-Speech**: Deepgram TTS for natural voice output
- **Language Model**: Google Gemini 2.0 Flash Lite for intelligent responses
- **Voice Activity Detection**: Silero VAD for conversation flow
- **Noise Cancellation**: LiveKit BVC for clear audio

## Usage Examples

Once the agent is running, it can:

- Answer incoming phone calls automatically
- Have natural voice conversations
- Make outbound calls when requested
- Provide customer service assistance
- Handle multiple calls simultaneously

## Configuration

The agent can be customized by:

- Modifying the system prompt in `support_assistant.py`
- Adjusting voice settings in the LiveKit session configuration
- Adding new capabilities to the `VapiLiveKitAssistant` class
- Configuring call routing and phone number settings

## Troubleshooting

1. **Environment Variables**: Ensure all required environment variables are set
2. **API Keys**: Verify that your Vapi token is valid and has necessary permissions
3. **Phone Numbers**: Make sure your phone number is properly configured in Vapi
4. **Dependencies**: Install all required packages using pip
5. **Ports**: Ensure necessary ports are available for LiveKit connections

## Support

For issues with:

- Vapi integration: Check the Vapi documentation
- LiveKit setup: Refer to LiveKit documentation
- Voice quality: Adjust Deepgram or TTS settings
- Call routing: Verify Vapi phone number configuration
