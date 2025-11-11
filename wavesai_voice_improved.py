#!/usr/bin/env python3
"""
WavesAI Voice Mode - Improved with Smart Device Detection
Based on your voice_assistant.py prototype
"""

import os
import sys
import time
import queue
import threading
import tempfile
import wave
from collections import deque
from typing import Optional, Tuple, List
import numpy as np

# Audio libraries
try:
    import sounddevice as sd
except ImportError:
    print("Installing sounddevice...")
    os.system("pip install sounddevice")
    import sounddevice as sd

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Installing faster-whisper...")
    os.system("pip install faster-whisper")
    from faster_whisper import WhisperModel

# Check for CUDA
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except:
    CUDA_AVAILABLE = False


class SmartDeviceDetector:
    """Intelligent audio device detection from your prototype"""
    
    def __init__(self):
        self.best_device = None
        self.best_sample_rate = None
    
    def is_likely_microphone(self, device_info: dict) -> int:
        """Score how likely a device is to be a useful microphone (0-100)"""
        name = device_info['name'].lower()
        score = 0
        
        # Positive indicators
        microphone_keywords = ['mic', 'microphone', 'webcam', 'camera', 'usb', 'input', 'capture', 'audio']
        for keyword in microphone_keywords:
            if keyword in name:
                score += 20
        
        # Prefer USB devices over built-in
        if 'usb' in name:
            score += 15
        
        # Prefer webcam mics (usually good quality)
        if 'webcam' in name or 'camera' in name:
            score += 25
        
        # Check for specific good devices
        if 'blue' in name or 'yeti' in name or 'rode' in name:
            score += 30
        
        # Negative indicators (monitors, outputs, etc)
        bad_keywords = ['monitor', 'hdmi', 'displayport', 'output', 'speaker', 'headphone', 'sink', 'spdif']
        for keyword in bad_keywords:
            if keyword in name:
                score -= 50
        
        # Check if device has input channels
        if device_info.get('max_input_channels', 0) == 0:
            score -= 100
        
        # Prefer devices with stereo or mono (1-2 channels)
        channels = device_info.get('max_input_channels', 0)
        if 1 <= channels <= 2:
            score += 10
        elif channels > 8:  # Probably a mixer or something complex
            score -= 10
        
        return max(0, score)
    
    def test_device(self, device_index: int, sample_rate: int) -> bool:
        """Test if a device actually works for recording"""
        try:
            # Try to record a tiny snippet
            test_duration = 0.1  # 100ms
            recording = sd.rec(
                int(test_duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                device=device_index,
                dtype='float32'
            )
            sd.wait()
            
            # Check if we got actual audio data (not all zeros)
            if recording is not None and len(recording) > 0:
                rms = np.sqrt(np.mean(recording**2))
                # Should have at least some noise floor
                return not (np.isnan(rms) or rms == 0.0)
            
            return False
        except Exception:
            return False
    
    def find_best_device(self) -> Tuple[Optional[int], Optional[int]]:
        """Find the best working microphone device"""
        print("\033[1;36m[Device Detection]\033[0m Scanning for microphones...")
        
        devices = sd.query_devices()
        candidates = []
        
        # Score all input devices
        print("\033[1;33m[Found Devices]\033[0m")
        for idx, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                score = self.is_likely_microphone(device)
                if score > 0:
                    candidates.append((idx, device, score))
                    print(f"  {idx}: {device['name'][:50]} (Score: {score})")
        
        if not candidates:
            print("\033[1;31m[Error]\033[0m No input devices found!")
            return None, None
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        print("\n\033[1;36m[Testing Devices]\033[0m In order of preference...")
        
        # Test candidates in order of score
        sample_rates = [44100, 48000, 16000, 22050, 32000, 8000]
        
        for idx, device, score in candidates:
            device_name = device['name']
            print(f"  Testing: {device_name[:50]}...", end='')
            
            # Try different sample rates
            for rate in sample_rates:
                if self.test_device(idx, rate):
                    print(f" \033[1;32m✓\033[0m")
                    print(f"\033[1;32m[Selected]\033[0m {device_name}")
                    print(f"\033[1;32m[Settings]\033[0m {rate} Hz, Device #{idx}\n")
                    return idx, rate
            print(f" \033[1;31m✗\033[0m")
        
        # If we get here, nothing worked
        print("\033[1;31m[Error]\033[0m No working microphone found!")
        print("\033[1;33m[Tip]\033[0m Check your audio settings and permissions")
        return None, None


class VoiceActivityDetector:
    """Smart voice activity detection with noise adaptation"""
    
    def __init__(self, threshold: float = 0.01):
        self.threshold = threshold
        self.noise_floor = None
        self.calibration_samples = []
        self.is_calibrated = False
        self.dynamic_threshold = threshold
    
    def calibrate(self, audio_chunk: np.ndarray):
        """Calibrate noise floor based on ambient noise"""
        if len(self.calibration_samples) < 20:
            rms = self.calculate_rms(audio_chunk)
            if not np.isnan(rms) and rms > 0:
                self.calibration_samples.append(rms)
        elif not self.is_calibrated:
            # Set noise floor to 2x average ambient noise
            self.noise_floor = np.mean(self.calibration_samples) * 2.0
            self.dynamic_threshold = max(self.threshold, self.noise_floor)
            self.is_calibrated = True
            print(f"\033[1;32m[Calibrated]\033[0m Noise floor: {self.noise_floor:.4f}, Threshold: {self.dynamic_threshold:.4f}")
    
    def calculate_rms(self, audio_chunk: np.ndarray) -> float:
        """Calculate RMS energy safely"""
        if len(audio_chunk) == 0:
            return 0.0
        
        # Flatten and ensure float32
        audio_flat = audio_chunk.flatten().astype(np.float32)
        
        # Calculate RMS
        squared = audio_flat ** 2
        mean_squared = np.mean(squared)
        
        if mean_squared < 0 or np.isnan(mean_squared):
            return 0.0
        
        return np.sqrt(mean_squared)
    
    def is_voice_detected(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """Detect if voice is present, return detection and energy level"""
        rms = self.calculate_rms(audio_chunk)
        
        # Use calibrated threshold if available
        threshold = self.dynamic_threshold if self.is_calibrated else self.threshold
        
        is_speech = rms > threshold and not np.isnan(rms)
        
        return is_speech, rms


class ImprovedVoiceMode:
    """Improved voice mode for WavesAI using smart device detection"""
    
    def __init__(self, wavesai_instance):
        self.ai = wavesai_instance
        self.config = {
            'sample_rate': 44100,  # Will be updated by device detector
            'channels': 1,
            'vad_threshold': 0.01,
            'silence_duration': 1.2,
            'min_recording_duration': 0.5,
            'max_recording_duration': 30,
            'whisper_model': 'base',
            'device': 'cuda' if CUDA_AVAILABLE else 'cpu'
        }
        
        self.audio_queue = queue.Queue()
        self.vad = VoiceActivityDetector(self.config['vad_threshold'])
        self.stream = None
        self.device_index = None
        self.sample_rate = None
        self.whisper_model = None
        self.stop_listening = False
        
    def setup_audio(self):
        """Setup audio with smart device detection"""
        detector = SmartDeviceDetector()
        self.device_index, self.sample_rate = detector.find_best_device()
        
        if self.device_index is None:
            raise RuntimeError("No working microphone found")
        
        self.config['sample_rate'] = self.sample_rate
        return True
    
    def load_whisper(self):
        """Load Whisper model"""
        print(f"\033[1;33m[Loading]\033[0m Whisper model ({self.config['whisper_model']})...")
        
        try:
            # Try with CUDA if available
            if CUDA_AVAILABLE:
                self.whisper_model = WhisperModel(
                    self.config['whisper_model'],
                    device="cuda",
                    compute_type="float16"
                )
                print(f"\033[1;32m[Ready]\033[0m Whisper loaded on CUDA")
            else:
                self.whisper_model = WhisperModel(
                    self.config['whisper_model'],
                    device="cpu",
                    compute_type="int8"
                )
                print(f"\033[1;32m[Ready]\033[0m Whisper loaded on CPU")
        except Exception as e:
            print(f"\033[1;31m[Error]\033[0m Failed to load Whisper: {e}")
            return False
        
        return True
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if status and status.input_overflow:
            pass  # Ignore overflow warnings
        
        # Calibrate noise floor during first second
        if not self.vad.is_calibrated:
            self.vad.calibrate(indata)
        
        # Add to queue for processing
        self.audio_queue.put(indata.copy())
    
    def start_stream(self):
        """Start audio stream"""
        try:
            self.stream = sd.InputStream(
                device=self.device_index,
                samplerate=self.sample_rate,
                channels=self.config['channels'],
                callback=self.audio_callback,
                blocksize=int(self.sample_rate * 0.05),  # 50ms chunks
                dtype='float32'
            )
            self.stream.start()
            
            # Calibration period
            print("\033[1;36m[Calibrating]\033[0m Adjusting to ambient noise...")
            time.sleep(1.5)
            
            return True
            
        except Exception as e:
            print(f"\033[1;31m[Error]\033[0m Failed to start audio: {e}")
            return False
    
    def wait_for_speech(self) -> Optional[np.ndarray]:
        """Wait for speech and record automatically"""
        print("\033[1;32m[Listening]\033[0m Speak naturally...", end='', flush=True)
        
        recording_buffer = []
        pre_buffer = deque(maxlen=int(self.sample_rate * 0.5))  # 0.5s pre-buffer
        is_recording = False
        silence_start = None
        recording_start = None
        
        # Visual feedback
        dot_count = 0
        
        try:
            while not self.stop_listening:
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Always add to pre-buffer
                pre_buffer.append(audio_chunk)
                
                # Check for voice
                voice_detected, energy = self.vad.is_voice_detected(audio_chunk)
                
                if voice_detected and not is_recording:
                    # Start recording
                    print(f"\n\033[1;33m[Recording]\033[0m Energy: {energy:.4f}", end='', flush=True)
                    is_recording = True
                    recording_start = time.time()
                    # Include pre-buffer
                    recording_buffer = list(pre_buffer)
                    silence_start = None
                    dot_count = 0
                
                if is_recording:
                    recording_buffer.append(audio_chunk)
                    
                    # Visual feedback
                    dot_count += 1
                    if dot_count % 10 == 0:
                        print(".", end='', flush=True)
                    
                    # Check for max duration
                    if time.time() - recording_start > self.config['max_recording_duration']:
                        print("\n\033[1;33m[Max Duration]\033[0m Processing...")
                        break
                    
                    if not voice_detected:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= self.config['silence_duration']:
                            # Check minimum duration
                            if time.time() - recording_start >= self.config['min_recording_duration']:
                                duration = time.time() - recording_start
                                print(f"\n\033[1;32m[Complete]\033[0m {duration:.1f}s recorded")
                                break
                    else:
                        silence_start = None
                        
        except KeyboardInterrupt:
            print("\n\033[1;33m[Interrupted]\033[0m")
            return None
        
        if not recording_buffer:
            return None
        
        # Concatenate all audio
        return np.concatenate(recording_buffer, axis=0)
    
    def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using Whisper"""
        if audio_data is None or len(audio_data) == 0:
            return None
        
        print("\033[1;36m[Transcribing]\033[0m Processing speech...", end='', flush=True)
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Normalize audio
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_normalized = audio_data / max_val
            else:
                audio_normalized = audio_data
            
            # Convert to int16
            audio_int16 = np.int16(audio_normalized * 32767)
            
            # Write WAV
            with wave.open(tmp_file.name, 'wb') as wf:
                wf.setnchannels(self.config['channels'])
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            tmp_path = tmp_file.name
        
        try:
            # Transcribe
            segments, _ = self.whisper_model.transcribe(
                tmp_path,
                beam_size=5,
                language="en",
                vad_filter=True,
                condition_on_previous_text=False
            )
            
            text = " ".join([s.text for s in segments]).strip()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            if text:
                print(f" \033[1;32m✓\033[0m")
                return text
            else:
                print(f" \033[1;31m(no speech detected)\033[0m")
                return None
                
        except Exception as e:
            print(f" \033[1;31m✗ {e}\033[0m")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return None
    
    def process_command(self, text: str):
        """Process the transcribed text through WavesAI"""
        if not text:
            return
        
        print(f"\n\033[1;36m[You]\033[0m {text}")
        
        # Check for exit commands
        if text.lower() in ['exit', 'quit', 'goodbye', 'bye', 'stop']:
            print("\033[1;35m[WavesAI]\033[0m Goodbye! Have a great day.")
            self.stop_listening = True
            return
        
        # Process through WavesAI
        try:
            # Try to use the AI's existing methods
            response = self.ai.generate_response(text)
            
            if response:
                print(f"\033[1;35m[WavesAI]\033[0m {response}")
                
                # Try to speak the response if TTS is available
                if hasattr(self.ai, 'tts_speak_advanced'):
                    self.ai.tts_speak_advanced(response[:500])  # Limit length for TTS
                    
        except Exception as e:
            print(f"\033[1;31m[Error]\033[0m {e}")
    
    def run(self):
        """Main voice mode loop"""
        print("\n" + "="*60)
        print("\033[1;36m   WAVESAI VOICE MODE - IMPROVED\033[0m")
        print("="*60)
        print()
        
        # Setup audio device
        if not self.setup_audio():
            return
        
        # Load Whisper
        if not self.load_whisper():
            return
        
        # Load the AI model
        if hasattr(self.ai, 'load_llm'):
            if not self.ai.load_llm():
                print("\033[1;31m[Error]\033[0m Failed to load LLM")
                return
        
        # Start audio stream
        if not self.start_stream():
            return
        
        print("\033[1;32m[Ready]\033[0m Voice assistant is active!\n")
        print("\033[1;33m[Commands]\033[0m")
        print("  • Speak naturally after the beep")
        print("  • Say 'exit' or 'goodbye' to quit")
        print("  • Press Ctrl+C to stop\n")
        
        # Main loop
        try:
            while not self.stop_listening:
                # Wait for speech
                audio_data = self.wait_for_speech()
                
                if audio_data is not None:
                    # Transcribe
                    text = self.transcribe_audio(audio_data)
                    
                    if text:
                        # Process command
                        self.process_command(text)
                
                # Small delay between recordings
                if not self.stop_listening:
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            print("\n\033[1;33m[Interrupted]\033[0m Shutting down...")
        finally:
            # Cleanup
            if self.stream:
                self.stream.stop()
                self.stream.close()
            
            print("\033[1;35m[WavesAI]\033[0m Voice mode terminated. Goodbye!")


def integrate_improved_voice_mode():
    """Integrate the improved voice mode into WavesAI"""
    
    # Import the main WavesAI class
    sys.path.insert(0, '/home/bowser/.wavesai')
    from wavesai import WavesAI
    
    # Create WavesAI instance
    ai = WavesAI()
    
    # Create and run improved voice mode
    voice_mode = ImprovedVoiceMode(ai)
    voice_mode.run()


if __name__ == "__main__":
    integrate_improved_voice_mode()
