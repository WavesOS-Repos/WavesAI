#!/bin/bash

# Test the improved voice mode with smart device detection

echo "============================================"
echo "   WavesAI Improved Voice Mode Test"
echo "============================================"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q sounddevice faster-whisper scipy 2>/dev/null

# Run the improved voice mode
echo ""
echo "Starting improved voice mode with smart device detection..."
echo ""

python wavesai_voice_improved.py
