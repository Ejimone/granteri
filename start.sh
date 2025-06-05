#!/bin/bash

# Granteri Voice AI Agent - Development Startup Script

set -e

echo "🎯 Granteri Voice AI Agent Setup"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for environment file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  No .env file found. Copying from .env.example..."
        cp .env.example .env
        echo "📝 Please edit .env file with your actual API keys and configuration."
        echo "   Required variables:"
        echo "   - VAPI_API_KEY"
        echo "   - LIVEKIT_URL"
        echo "   - LIVEKIT_API_KEY"
        echo "   - LIVEKIT_API_SECRET"
        echo ""
        read -p "Press Enter to continue after configuring .env file..."
    else
        echo "❌ No .env or .env.example file found. Please create one with required variables."
        exit 1
    fi
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "🔑 Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required environment variables
echo "🔍 Checking configuration..."
if [ -z "$VAPI_API_KEY" ]; then
    echo "❌ VAPI_API_KEY is not set"
    exit 1
fi

if [ -z "$LIVEKIT_URL" ]; then
    echo "❌ LIVEKIT_URL is not set"
    exit 1
fi

if [ -z "$LIVEKIT_API_KEY" ]; then
    echo "❌ LIVEKIT_API_KEY is not set"
    exit 1
fi

if [ -z "$LIVEKIT_API_SECRET" ]; then
    echo "❌ LIVEKIT_API_SECRET is not set"
    exit 1
fi

echo "✅ Configuration looks good!"
echo ""

# Show menu
echo "🚀 Choose how to run the agent:"
echo "1) Development mode (LiveKit CLI - recommended for dev)"
echo "2) FastAPI server (recommended for production)"
echo "3) Demo script (test functionality)"
echo "4) Direct agent execution"
echo "5) Make outbound call"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "🔧 Starting in development mode..."
        python -m livekit.agents.cli dev test.py
        ;;
    2)
        echo "🌐 Starting FastAPI server..."
        python app.py
        ;;
    3)
        echo "🎭 Running demo script..."
        python demo.py
        ;;
    4)
        echo "🤖 Starting agent directly..."
        python agent.py
        ;;
    5)
        echo "📞 Making outbound call..."
        python make_outbound_call.py
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac
