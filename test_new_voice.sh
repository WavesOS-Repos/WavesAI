#!/bin/bash

echo "============================================"
echo "   Testing New Voice Mode with SoundDevice"
echo "============================================"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install required dependencies
echo "Installing dependencies..."
pip install -q sounddevice faster-whisper scipy numpy 2>/dev/null

echo ""
echo "Starting voice mode with device detection..."
echo ""

# Run the new voice mode
python wavesai.py --voice
