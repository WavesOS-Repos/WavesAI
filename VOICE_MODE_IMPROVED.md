# WavesAI Improved Voice Mode 🎤

## Features from Your Prototype

Based on your `voice_assistant.py` prototype, the improved voice mode includes:

### 🔍 Smart Device Detection
- **Automatically scans all audio devices** and scores them
- **Prioritizes:**
  - Webcam microphones (+25 points)
  - USB devices (+15 points)
  - Devices with "mic/microphone" in name (+20 points)
  - Professional mics like Blue Yeti, Rode (+30 points)
- **Excludes:**
  - Monitors (-50 points)
  - HDMI/DisplayPort devices
  - Outputs/speakers
- **Tests each device** to verify it actually works!

### 🎯 Intelligent Voice Detection
- **Automatic noise calibration** - adapts to your environment
- **Dynamic threshold adjustment** - no manual tuning needed
- **Pre-buffering** - never misses the beginning of speech
- **Smart silence detection** - knows when you're done talking

### 🚀 Better Performance
- Uses **sounddevice** instead of PyAudio (more reliable)
- **Faster Whisper** for improved transcription speed
- Automatic sample rate detection
- Works with any microphone configuration

## Installation

```bash
cd ~/.wavesai

# Install dependencies
pip install sounddevice faster-whisper scipy

# Or use the setup script
./test_improved_voice.sh
```

## Usage

### Method 1: Direct Run
```bash
python wavesai_voice_improved.py
```

### Method 2: Through Main WavesAI
```bash
# Use the improved voice mode
python wavesai.py --voice-improved

# Or shorter version
python wavesai.py voice2
```

### Method 3: Test Script
```bash
./test_improved_voice.sh
```

## What You'll See

```
============================================
   WAVESAI VOICE MODE - IMPROVED
============================================

[Device Detection] Scanning for microphones...
[Found Devices]
  0: USB Webcam Microphone (Score: 60)
  3: HDA Intel PCH: ALC897 Analog (Score: 20)
  7: USB Audio Device (Score: 35)

[Testing Devices] In order of preference...
  Testing: USB Webcam Microphone... ✓
[Selected] USB Webcam Microphone
[Settings] 44100 Hz, Device #0

[Loading] Whisper model (base)...
[Ready] Whisper loaded on CUDA

[Calibrating] Adjusting to ambient noise...
[Calibrated] Noise floor: 0.0023, Threshold: 0.0046

[Ready] Voice assistant is active!

[Commands]
  • Speak naturally after the beep
  • Say 'exit' or 'goodbye' to quit
  • Press Ctrl+C to stop

[Listening] Speak naturally...
[Recording] Energy: 0.0234..........
[Complete] 2.3s recorded
[Transcribing] Processing speech... ✓

[You] What's the weather like today?
[WavesAI] I can help you check the weather...
```

## Key Improvements Over Original

| Feature | Original Voice Mode | Improved Voice Mode |
|---------|-------------------|-------------------|
| **Device Selection** | Manual/First available | Smart scoring & testing |
| **Audio Library** | PyAudio | SoundDevice (more stable) |
| **Transcription** | OpenAI Whisper | Faster Whisper |
| **Noise Handling** | Fixed threshold | Auto-calibration |
| **Sample Rate** | Fixed 44100 Hz | Auto-detection |
| **Device Testing** | None | Tests before selection |
| **Visual Feedback** | Basic | Detailed with energy levels |

## Troubleshooting

### No Microphone Found
```bash
# Check available devices
python -c "import sounddevice; print(sounddevice.query_devices())"
```

### Permission Issues
```bash
# On Linux, add user to audio group
sudo usermod -a -G audio $USER
# Then logout and login again
```

### Dependencies Missing
```bash
# Install all at once
pip install sounddevice faster-whisper scipy numpy
```

## Configuration

The improved mode uses these settings (auto-configured):

```python
config = {
    'sample_rate': 44100,        # Auto-detected
    'channels': 1,               # Mono
    'vad_threshold': 0.01,       # Auto-calibrated
    'silence_duration': 1.2,     # Seconds of silence to stop
    'min_recording_duration': 0.5,  # Minimum speech length
    'max_recording_duration': 30,   # Maximum recording
    'whisper_model': 'base',     # Whisper model size
}
```

## Advanced Features

### Device Scoring Algorithm
The system scores each device based on:
- Name patterns (mic, webcam, usb, etc.)
- Device type (input vs output)
- Channel count (prefers 1-2 channels)
- Professional device detection

### Noise Calibration
- Takes 20 samples of ambient noise
- Sets threshold to 2x average noise level
- Continuously adapts during use

### Pre-buffering
- Keeps 0.5 seconds of audio before speech detected
- Never misses the beginning of sentences

## Credits

This improved voice mode is based on your `voice_assistant.py` prototype, integrating its smart device detection and noise handling into WavesAI.
