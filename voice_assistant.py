#!/usr/bin/env python3
"""
WavesAI Voice Assistant - Optimized Launcher
Combines the best features from both voice implementations
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Set environment variables for cleaner operation
os.environ['ALSA_QUIET'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:webrtcvad'
os.environ['PYTORCH_DISABLE_WARNINGS'] = '1'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import sounddevice as sd
        import numpy as np
        from faster_whisper import WhisperModel
        import torch
        return True
    except ImportError as e:
        print(f"\033[1;31m[Error]\033[0m Missing dependency: {e}")
        print("\033[1;33m[Fix]\033[0m Activate venv: source ~/.wavesai/venv/bin/activate")
        return False

def check_audio_devices():
    """Check available audio devices"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        if not input_devices:
            print("\033[1;31m[Error]\033[0m No input devices found!")
            return False
        return True
    except Exception as e:
        print(f"\033[1;31m[Error]\033[0m Audio check failed: {e}")
        return False

def main():
    """Main launcher function"""
    print("\n" + "="*70)
    print("\033[1;36m          WavesAI Voice Assistant - Enhanced Edition\033[0m")
    print("="*70)
    print()
    
    # Check if we're in the right directory
    wavesai_dir = Path.home() / ".wavesai"
    if not wavesai_dir.exists():
        print("\033[1;31m[Error]\033[0m WavesAI directory not found!")
        sys.exit(1)
    
    os.chdir(wavesai_dir)
    
    # Check dependencies
    print("\033[1;33m[Checking]\033[0m Dependencies...", end='')
    if not check_dependencies():
        sys.exit(1)
    print(" \033[1;32m✓\033[0m")
    
    # Check audio
    print("\033[1;33m[Checking]\033[0m Audio devices...", end='')
    if not check_audio_devices():
        sys.exit(1)
    print(" \033[1;32m✓\033[0m")
    
    print()
    print("\033[1;36m[Options]\033[0m Choose voice mode:")
    print("  1. \033[1;32mImproved Voice Mode\033[0m (Recommended - Smart device detection)")
    print("  2. \033[1;33mOriginal Voice Mode\033[0m (Legacy PyAudio implementation)")
    print("  3. \033[1;35mTest Audio Only\033[0m (Check microphone levels)")
    print("  4. \033[1;34mText Mode\033[0m (No voice, text only)")
    print()
    
    try:
        choice = input("\033[1;36m[Select]\033[0m Enter choice (1-4) [1]: ").strip() or "1"
        
        if choice == "1":
            print("\n\033[1;32m[Starting]\033[0m Improved Voice Mode...")
            sys.path.insert(0, str(wavesai_dir))
            from wavesai_voice_improved import integrate_improved_voice_mode
            integrate_improved_voice_mode()
            
        elif choice == "2":
            print("\n\033[1;33m[Starting]\033[0m Original Voice Mode...")
            sys.path.insert(0, str(wavesai_dir))
            from wavesai import WavesAI
            ai = WavesAI()
            ai.voice_mode()
            
        elif choice == "3":
            print("\n\033[1;35m[Starting]\033[0m Audio Test...")
            from test_audio import test_microphone
            test_microphone()
            
        elif choice == "4":
            print("\n\033[1;34m[Starting]\033[0m Text Mode...")
            sys.path.insert(0, str(wavesai_dir))
            from wavesai import WavesAI
            ai = WavesAI()
            if ai.load_llm():
                ai.interactive_mode()
            
        else:
            print("\033[1;31m[Error]\033[0m Invalid choice!")
            
    except KeyboardInterrupt:
        print("\n\033[1;33m[Cancelled]\033[0m Goodbye!")
    except Exception as e:
        print(f"\n\033[1;31m[Error]\033[0m {e}")

if __name__ == "__main__":
    main()
