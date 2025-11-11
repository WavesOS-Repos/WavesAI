#!/usr/bin/env python3
"""
Audio Test Script for WavesAI Voice Assistant
Tests microphone input and shows energy levels
"""

import pyaudio
import numpy as np
import sys
import time

def test_microphone():
    """Test microphone input and show energy levels"""
    
    print("=" * 60)
    print("   WavesAI Audio Test")
    print("=" * 60)
    print()
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Get default input device info
    try:
        info = p.get_default_input_device_info()
        print(f"Default Input Device: {info['name']}")
        print(f"Default Sample Rate: {info['defaultSampleRate']} Hz")
        print(f"Max Input Channels: {info['maxInputChannels']}")
        print()
    except Exception as e:
        print(f"Error getting device info: {e}")
        return
    
    # Test parameters
    RATE = 44100
    CHUNK = 2048
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    
    print(f"Testing with: {RATE} Hz, {CHUNK} samples per chunk")
    print()
    print("Speak into your microphone. The bars show audio energy level.")
    print("Higher energy = more bars. Press Ctrl+C to stop.")
    print()
    print("Energy Levels:")
    print("-" * 60)
    
    # Open stream
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print(f"Error opening audio stream: {e}")
        print("\nTrying with 48000 Hz...")
        RATE = 48000
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            print(f"Success! Using {RATE} Hz")
        except Exception as e2:
            print(f"Failed: {e2}")
            return
    
    # Monitor audio levels
    try:
        max_energy = 0
        min_energy = float('inf')
        avg_energies = []
        
        while True:
            # Read audio data
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            
            # Calculate RMS energy
            energy = np.sqrt(np.mean(audio_data ** 2))
            avg_energies.append(energy)
            
            # Keep last 100 samples for average
            if len(avg_energies) > 100:
                avg_energies.pop(0)
            
            # Update min/max
            if energy > max_energy:
                max_energy = energy
            if energy < min_energy and energy > 0:
                min_energy = energy
            
            # Create energy bar
            bar_length = min(int(energy / 100), 60)
            bar = '█' * bar_length
            
            # Color based on energy level
            if energy < 50:
                color = '\033[1;31m'  # Red - too quiet
                status = "TOO QUIET"
            elif energy < 200:
                color = '\033[1;33m'  # Yellow - quiet
                status = "QUIET    "
            elif energy < 1000:
                color = '\033[1;32m'  # Green - good
                status = "GOOD     "
            else:
                color = '\033[1;36m'  # Cyan - loud
                status = "LOUD     "
            
            # Print energy level
            avg = sum(avg_energies) / len(avg_energies) if avg_energies else 0
            print(f"\r{color}[{status}] Energy: {energy:6.0f} | Avg: {avg:6.0f} | {bar}\033[0m", 
                  end='', flush=True)
            
    except KeyboardInterrupt:
        print("\n")
        print("-" * 60)
        print(f"Test Complete!")
        print(f"Min Energy: {min_energy:.0f}")
        print(f"Max Energy: {max_energy:.0f}")
        print(f"Average: {avg:.0f}")
        print()
        print("Recommended threshold for speech detection: ", end='')
        if avg < 30:
            print(f"{max(20, avg * 2):.0f} (your mic is very quiet)")
        elif avg < 100:
            print(f"{avg * 1.5:.0f} (normal)")
        else:
            print(f"{avg * 2:.0f} (your mic is loud)")
        print()
        print("To use this threshold, set:")
        print(f"export WAVESAI_ENERGY_THRESHOLD={int(avg * 1.5)}")
        
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    test_microphone()
