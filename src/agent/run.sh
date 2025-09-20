#!/bin/bash

# Clarity Voice Agent Runner

echo "Starting Clarity Voice Agent..."
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    python3 setup.py
    if [ $? -ne 0 ]; then
        echo "Setup failed. Exiting."
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Please create .env with your API keys"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Verify required environment variables
if [ -z "$LIVEKIT_URL" ] || [ -z "$LIVEKIT_API_KEY" ] || [ -z "$LIVEKIT_API_SECRET" ]; then
    echo "Error: LiveKit credentials not set in .env"
    echo "Required: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set in .env"
    exit 1
fi

echo "✓ Environment configured"
echo "✓ Connecting to LiveKit: $LIVEKIT_URL"
echo ""
echo "Starting agent..."
echo "Press Ctrl+C to stop"
echo "================================"

# Run the agent
python voice_agent.py