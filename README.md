# Granteri Voice AI Agent System

A robust voice AI agent system that handles both inbound and outbound calls using Vapi for telephony and LiveKit for real-time agent sessions. The system provides a modular architecture with FastAPI for easy deployment and comprehensive webhook handling.

## Features

✅ **Dual Call Handling**: Supports both inbound and outbound voice calls  
✅ **Real-time AI Conversations**: Natural voice interactions with AI personas  
✅ **Webhook Integration**: Robust webhook handling for call events  
✅ **REST API**: FastAPI endpoints for programmatic control  
✅ **Modular Architecture**: Clean separation of concerns and easy extensibility  
✅ **Comprehensive Logging**: Detailed logging for debugging and monitoring  
✅ **Error Handling**: Graceful error handling and recovery  
✅ **Multiple Deployment Options**: CLI, web service, or development modes

## Quick Start

### Prerequisites

- Python 3.8+
- Vapi API account and credentials
- LiveKit account and credentials
- Phone number provisioned through Vapi

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd granteri
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export VAPI_API_KEY="your_vapi_api_key"
export LIVEKIT_URL="your_livekit_url"
export LIVEKIT_API_KEY="your_livekit_api_key"
export LIVEKIT_API_SECRET="your_livekit_api_secret"
```

### Quick Demo

Run the demo to test both inbound and outbound functionality:

```bash
python demo.py
```

## Environment Setup

### Required Environment Variables

```bash
# Vapi Configuration
export VAPI_API_KEY="your_vapi_api_key"
export VAPI_PHONE_NUMBER_ID="your_phone_number_id"  # Optional

# LiveKit Configuration
export LIVEKIT_URL="wss://your-livekit-url"
export LIVEKIT_API_KEY="your_livekit_api_key"
export LIVEKIT_API_SECRET="your_livekit_api_secret"

# Optional: Server Configuration
export PORT="8000"  # Default FastAPI port
export HOST="0.0.0.0"  # Default FastAPI host
```

### Setting Up Vapi

1. Sign up at [Vapi.ai](https://vapi.ai)
2. Get your API key from the dashboard
3. Purchase or configure a phone number
4. Set up webhooks to point to your server endpoint

### Setting Up LiveKit

1. Sign up at [LiveKit Cloud](https://cloud.livekit.io) or self-host
2. Create a project and get your credentials
3. Note your WebSocket URL, API key, and secret

## Usage

### Method 1: FastAPI Web Service (Production)

Start the FastAPI server for production use:

```bash
python app.py
```

This provides a REST API with the following endpoints:

- `POST /make-call` - Initiate outbound calls
- `POST /webhook` - Handle Vapi webhooks
- `GET /config` - View agent configuration
- `GET /health` - Health check endpoint

#### Making Outbound Calls via API

```bash
curl -X POST "http://localhost:8000/make-call" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Hello, this is a test call from our AI agent."
  }'
```

### Method 2: LiveKit Development Mode (Development)

For development and testing with LiveKit's development tools:

```bash
python -m livekit.agents.cli dev test.py
```

This mode provides:

- Hot reloading during development
- Built-in debugging tools
- LiveKit dashboard integration

### Method 3: Direct CLI Execution

For simple testing and debugging:

```bash
# Run the main agent
python agent.py

# Make an outbound call directly
python make_outbound_call.py

# Configure inbound calls
python inbound_calls.py

# Test webhook handling
python webhook_handler.py
```

### Method 4: Background Service Manager

For running as a background service with process management:

```bash
python start_agent.py
```

## API Documentation

### FastAPI Endpoints

#### `POST /make-call`

Initiate an outbound call.

**Request Body:**

```json
{
  "phone_number": "+1234567890",
  "message": "Optional custom message",
  "assistant_id": "optional_assistant_id"
}
```

**Response:**

```json
{
  "success": true,
  "call_id": "call_123456",
  "message": "Call initiated successfully"
}
```

#### `POST /webhook`

Handle incoming webhook events from Vapi.

**Request Body:** Vapi webhook payload
**Response:** `{"status": "received"}`

#### `GET /config`

Get current agent configuration.

**Response:**

```json
{
  "agent_name": "Alex",
  "voice_settings": {...},
  "model_config": {...}
}
```

#### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Architecture

### Core Components

- **`agent.py`** - Main VoiceAgent class handling LiveKit sessions
- **`app.py`** - FastAPI web application with REST endpoints
- **`inbound_calls.py`** - Inbound call configuration and setup
- **`make_outbound_call.py`** - Outbound call initiation logic
- **`webhook_handler.py`** - Webhook event processing
- **`demo.py`** - Demonstration script for testing

### Agent Personas

The system includes pre-configured AI personas:

- **Alex** - Customer service representative
- **Support Assistant** - Technical support specialist

### Call Flow

1. **Inbound Calls:**

   - Vapi receives call on provisioned number
   - Webhook triggers agent session creation
   - LiveKit handles real-time voice processing
   - Agent responds with configured persona

2. **Outbound Calls:**
   - API request or CLI command initiates call
   - Vapi dials specified number
   - Agent session starts on connection
   - Conversation handled by AI persona

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
source .env  # or export variables manually

# Run in development mode
python -m livekit.agents.cli dev test.py
```

### Production Deployment

#### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "app.py"]
```

Build and run:

```bash
docker build -t granteri-agent .
docker run -p 8000:8000 --env-file .env granteri-agent
```

#### Using Process Manager (PM2)

```bash
# Install PM2
npm install -g pm2

# Start the application
pm2 start app.py --name granteri-agent --interpreter python

# Monitor logs
pm2 logs granteri-agent
```

#### Cloud Deployment

For cloud deployment (AWS, GCP, Azure):

1. Set up environment variables in your cloud provider
2. Deploy the FastAPI application
3. Configure webhooks to point to your deployed endpoint
4. Ensure proper security groups/firewall rules for HTTP traffic

## Configuration

### Agent Configuration

Modify agent behavior in `agent.py`:

```python
# Customize voice settings
VOICE_CONFIG = {
    "voice_id": "alex",
    "stability": 0.8,
    "similarity_boost": 0.8
}

# Modify AI persona
SYSTEM_PROMPT = "You are Alex, a helpful customer service representative..."
```

### Webhook Configuration

Set up webhooks in your Vapi dashboard:

- **Webhook URL**: `https://your-domain.com/webhook`
- **Events**: `call.started`, `call.ended`, `call.failed`
- **Authentication**: Optional bearer token

## Troubleshooting

### Common Issues

#### "Invalid API Key" Error

- Verify your Vapi API key is correct
- Check environment variable is properly set
- Ensure API key has necessary permissions

#### "Connection Failed" to LiveKit

- Verify LiveKit URL, API key, and secret
- Check network connectivity
- Ensure LiveKit server is running

#### Webhook Not Receiving Events

- Verify webhook URL is publicly accessible
- Check Vapi dashboard webhook configuration
- Review webhook handler logs for errors

#### Calls Not Connecting

- Verify phone number format (+1234567890)
- Check Vapi account balance and limits
- Review call logs in Vapi dashboard

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Logs Location

- Application logs: Console output
- Call logs: Vapi dashboard
- Agent logs: LiveKit dashboard

## Development

### Project Structure

```
granteri/
├── agent.py              # Main agent logic
├── app.py                # FastAPI web application
├── inbound_calls.py      # Inbound call setup
├── make_outbound_call.py # Outbound call logic
├── webhook_handler.py    # Webhook processing
├── demo.py              # Demo script
├── requirements.txt     # Dependencies
├── README.md           # Documentation
└── front/              # Frontend assets
    ├── index.html
    ├── script.js
    └── conversation.js
```

### Adding New Features

1. **New Agent Persona:**

   - Create new assistant in `support_assistant.py`
   - Update agent configuration in `agent.py`

2. **New API Endpoint:**

   - Add route to `app.py`
   - Implement handler logic
   - Update documentation

3. **New Webhook Event:**
   - Add handler in `webhook_handler.py`
   - Update event processing logic

### Testing

Run the demo script for comprehensive testing:

```bash
python demo.py
```

Test individual components:

```bash
# Test outbound calls
python make_outbound_call.py

# Test inbound configuration
python inbound_calls.py

# Test webhook handling
python webhook_handler.py
```

## Support

### Resources

- [Vapi Documentation](https://docs.vapi.ai)
- [LiveKit Documentation](https://docs.livekit.io)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

### Getting Help

1. Check the troubleshooting section above
2. Review application logs for error details
3. Verify configuration and environment variables
4. Test with the demo script to isolate issues

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]
