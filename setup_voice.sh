#!/bin/bash

# WavesAI Voice Assistant Setup Script
# This script installs all necessary dependencies for the voice mode

echo "============================================"
echo "   WavesAI Voice Assistant Setup"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        return 1
    fi
}

echo -e "${YELLOW}[1/4]${NC} Installing system dependencies..."
echo "Installing: portaudio, espeak-ng, ffmpeg..."

# Install system dependencies
sudo pacman -S --needed --noconfirm portaudio espeak-ng ffmpeg
print_status $? "System dependencies installed"

echo ""
echo -e "${YELLOW}[2/4]${NC} Installing Python voice dependencies..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install Python packages
pip install --upgrade pip
pip install pyaudio webrtcvad openai-whisper noisereduce

# Check for CUDA and install torch accordingly
if command_exists nvidia-smi && nvidia-smi > /dev/null 2>&1; then
    echo -e "${GREEN}NVIDIA GPU detected!${NC} Installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "No NVIDIA GPU detected. Installing CPU-only PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

print_status $? "Python dependencies installed"

echo ""
echo -e "${YELLOW}[3/4]${NC} Setting up Piper TTS (optional but recommended)..."

# Check if piper is available in AUR
if command_exists yay; then
    echo "Installing Piper from AUR..."
    yay -S --needed --noconfirm piper-tts-bin
elif command_exists paru; then
    echo "Installing Piper from AUR..."
    paru -S --needed --noconfirm piper-tts-bin
else
    echo -e "${YELLOW}Warning:${NC} No AUR helper found. You can install Piper manually from:"
    echo "https://github.com/rhasspy/piper/releases"
fi

# Download a Piper voice model
PIPER_MODELS_DIR="$HOME/.local/share/piper/voices"
mkdir -p "$PIPER_MODELS_DIR"

echo ""
echo "Downloading recommended Piper voice model..."
cd "$PIPER_MODELS_DIR"

# Download a high-quality English voice
VOICE_NAME="en_US-amy-medium"
if [ ! -f "${VOICE_NAME}.onnx" ]; then
    wget -q "https://github.com/rhasspy/piper/releases/download/v1.2.0/${VOICE_NAME}.onnx"
    wget -q "https://github.com/rhasspy/piper/releases/download/v1.2.0/${VOICE_NAME}.onnx.json"
    print_status $? "Piper voice model downloaded"
else
    echo -e "${GREEN}✓${NC} Piper voice model already exists"
fi

cd - > /dev/null

echo ""
echo -e "${YELLOW}[4/4]${NC} Creating configuration file..."

# Create .env file for voice configuration
cat > "$HOME/.wavesai/.env" << EOF
# WavesAI Voice Configuration

# Whisper Model (tiny, base, small, medium, large)
WAVESAI_WHISPER_MODEL=base.en

# Piper TTS Model Path
WAVESAI_PIPER_MODEL=$PIPER_MODELS_DIR/${VOICE_NAME}.onnx

# TTS Speed (0.5 = slower, 1.0 = normal, 2.0 = faster)
WAVESAI_TTS_SPEED=1.0

# Enable noise reduction (true/false)
WAVESAI_NOISE_REDUCTION=true
EOF

print_status $? "Configuration file created"

echo ""
echo "============================================"
echo -e "${GREEN}   Setup Complete!${NC}"
echo "============================================"
echo ""
echo "To start WavesAI in voice mode, run:"
echo -e "${GREEN}python ~/.wavesai/wavesai.py --voice${NC}"
echo ""
echo "Configuration file: ~/.wavesai/.env"
echo "You can edit this file to change voice settings."
echo ""
echo "Tips:"
echo "  • Say 'exit' or 'quit' to stop voice mode"
echo "  • Speak naturally after the assistant says it's ready"
echo "  • The system will detect when you stop speaking"
echo ""

# Test audio input
echo "Testing audio input device..."
if python -c "import pyaudio; p=pyaudio.PyAudio(); p.terminate()" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Audio input device detected"
else
    echo -e "${RED}✗${NC} No audio input device found. Please check your microphone."
fi

echo ""
echo "For better voice quality, consider downloading additional Piper models from:"
echo "https://github.com/rhasspy/piper/releases"
