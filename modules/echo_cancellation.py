#!/usr/bin/env python3
"""
Acoustic Echo Cancellation Module for WavesAI
Prevents AI from interrupting itself by canceling its own voice from microphone input
"""

import numpy as np
import threading
import queue
import time
from dataclasses import dataclass
from typing import Optional
import sounddevice as sd


@dataclass
class EchoCancelConfig:
    """Configuration for echo cancellation"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    buffer_duration: float = 2.0  # seconds of audio history to keep
    adaptation_rate: float = 0.01  # How fast to adapt to echo
    suppression_factor: float = 0.95  # How much to suppress detected echo


class AdaptiveEchoCanceller:
    """
    Real-time Adaptive Echo Cancellation using LMS (Least Mean Squares) algorithm
    
    How it works:
    1. Records what AI is speaking (reference signal)
    2. Subtracts AI's voice from microphone input
    3. Adapts in real-time to room acoustics
    """
    
    def __init__(self, config: EchoCancelConfig):
        self.config = config
        self.is_speaking = False
        
        # Audio buffers
        self.reference_buffer = []  # What AI is speaking
        self.mic_buffer = []  # What mic hears
        
        # Adaptive filter coefficients
        self.filter_length = int(config.sample_rate * 0.3)  # 300ms filter
        self.weights = np.zeros(self.filter_length)
        
        # Thread safety
        self.lock = threading.Lock()
        
    def start_speaking(self, audio_data: np.ndarray):
        """
        Called when AI starts speaking
        Stores reference audio for echo cancellation
        """
        with self.lock:
            self.is_speaking = True
            self.reference_buffer = audio_data.copy()
    
    def stop_speaking(self):
        """Called when AI stops speaking"""
        with self.lock:
            self.is_speaking = False
            time.sleep(0.5)  # Wait for echo to fade
            self.reference_buffer = []
    
    def cancel_echo(self, mic_input: np.ndarray) -> np.ndarray:
        """
        Remove AI's voice from microphone input
        
        Args:
            mic_input: Raw audio from microphone
            
        Returns:
            Clean audio with echo removed
        """
        if not self.is_speaking or len(self.reference_buffer) == 0:
            return mic_input
        
        with self.lock:
            # Ensure same length
            ref_len = len(self.reference_buffer)
            mic_len = len(mic_input)
            min_len = min(ref_len, mic_len)
            
            reference = self.reference_buffer[:min_len]
            mic = mic_input[:min_len]
            
            # Apply adaptive filter
            estimated_echo = self._estimate_echo(reference)
            
            # Subtract estimated echo from mic input
            clean_signal = mic - estimated_echo[:len(mic)]
            
            # Update filter weights (adapt to room)
            self._update_filter(reference, mic, clean_signal)
            
            return clean_signal
    
    def _estimate_echo(self, reference: np.ndarray) -> np.ndarray:
        """Estimate echo using adaptive filter"""
        estimated = np.convolve(reference.flatten(), self.weights, mode='same')
        return estimated * self.config.suppression_factor
    
    def _update_filter(self, reference: np.ndarray, mic: np.ndarray, error: np.ndarray):
        """Update filter weights using LMS algorithm"""
        if len(reference) < self.filter_length:
            return
        
        # Normalize
        ref_flat = reference.flatten()
        err_flat = error.flatten()
        
        # Update weights
        for i in range(min(len(err_flat), len(ref_flat) - self.filter_length)):
            ref_segment = ref_flat[i:i + self.filter_length]
            self.weights += self.config.adaptation_rate * err_flat[i] * ref_segment


class SimpleEchoCanceller:
    """
    Simpler approach: Time-based muting
    Mutes mic when AI is speaking, with smart gap detection
    """
    
    def __init__(self):
        self.is_speaking = False
        self.speaking_start = None
        self.min_gap_for_interrupt = 0.3  # seconds
        self.last_speech_end = 0
    
    def start_speaking(self):
        """Mark that AI started speaking"""
        self.is_speaking = True
        self.speaking_start = time.time()
    
    def stop_speaking(self):
        """Mark that AI stopped speaking"""
        self.is_speaking = False
        self.last_speech_end = time.time()
    
    def should_process_audio(self) -> bool:
        """
        Determine if we should process mic input
        Returns False if AI is speaking (to prevent self-interruption)
        """
        if not self.is_speaking:
            # Allow short gap after speaking ends
            if time.time() - self.last_speech_end < 0.3:
                return False
            return True
        
        return False


class SmartEchoCanceller:
    """
    Hybrid approach: Combines multiple techniques
    1. RMS-based voice detection (distinguish AI voice from user)
    2. Spectral subtraction
    3. Time-domain filtering
    """
    
    def __init__(self, config: EchoCancelConfig):
        self.config = config
        self.is_speaking = False
        self.ai_voice_profile = None  # Learned AI voice characteristics
        self.reference_audio = []
    
    def start_speaking(self, audio_data: np.ndarray):
        """Record AI's voice for reference"""
        self.is_speaking = True
        self.reference_audio = audio_data.copy()
        self._learn_ai_voice_profile(audio_data)
    
    def stop_speaking(self):
        """Stop tracking AI voice"""
        self.is_speaking = False
        time.sleep(0.4)  # Acoustic delay
        self.reference_audio = []
    
    def _learn_ai_voice_profile(self, audio: np.ndarray):
        """Learn frequency characteristics of AI's voice"""
        # FFT to get frequency profile
        fft = np.fft.rfft(audio.flatten())
        self.ai_voice_profile = np.abs(fft)
    
    def cancel_echo(self, mic_input: np.ndarray) -> np.ndarray:
        """Remove echo using spectral subtraction"""
        if not self.is_speaking or self.ai_voice_profile is None:
            return mic_input
        
        # Convert to frequency domain
        mic_fft = np.fft.rfft(mic_input.flatten())
        mic_magnitude = np.abs(mic_fft)
        mic_phase = np.angle(mic_fft)
        
        # Subtract AI voice spectrum
        profile_len = len(self.ai_voice_profile)
        mag_len = len(mic_magnitude)
        
        if profile_len <= mag_len:
            # Spectral subtraction
            clean_magnitude = mic_magnitude.copy()
            clean_magnitude[:profile_len] = np.maximum(
                mic_magnitude[:profile_len] - self.ai_voice_profile * 0.8,
                mic_magnitude[:profile_len] * 0.1  # Noise floor
            )
        else:
            clean_magnitude = mic_magnitude
        
        # Reconstruct signal
        clean_fft = clean_magnitude * np.exp(1j * mic_phase)
        clean_signal = np.fft.irfft(clean_fft, n=len(mic_input.flatten()))
        
        return clean_signal.reshape(mic_input.shape)
    
    def is_user_speaking(self, mic_input: np.ndarray) -> bool:
        """
        Distinguish between AI's voice (from speakers) and user's voice
        
        Returns:
            True if it's likely user speaking (not echo)
        """
        if not self.is_speaking:
            return True  # AI not speaking, must be user
        
        # Calculate RMS of input
        rms = np.sqrt(np.mean(mic_input.flatten() ** 2))
        
        # If reference audio exists, compare
        if len(self.reference_audio) > 0:
            ref_rms = np.sqrt(np.mean(self.reference_audio.flatten() ** 2))
            
            # User voice (close to mic) should be much louder than echo
            # Typical echo is 20-40% of original volume
            if rms > ref_rms * 1.5:  # User voice is 1.5x louder
                return True
            elif rms < ref_rms * 0.7:  # Likely just echo
                return False
        
        # Default: use RMS threshold
        return rms > 0.08  # High threshold = only close voice


class WavesAIEchoCancellation:
    """
    Main echo cancellation module for WavesAI
    Integrates with existing voice assistant
    """
    
    def __init__(self, method: str = "smart"):
        """
        Args:
            method: "adaptive", "simple", or "smart" (recommended)
        """
        self.config = EchoCancelConfig()
        
        if method == "adaptive":
            self.canceller = AdaptiveEchoCanceller(self.config)
        elif method == "simple":
            self.canceller = SimpleEchoCanceller()
        else:  # smart (default)
            self.canceller = SmartEchoCanceller(self.config)
        
        self.method = method
    
    def on_tts_start(self, tts_audio: Optional[np.ndarray] = None):
        """
        Call this when AI starts speaking
        
        Args:
            tts_audio: The audio AI will speak (for reference)
        """
        if tts_audio is not None and hasattr(self.canceller, 'start_speaking'):
            if self.method in ["adaptive", "smart"]:
                self.canceller.start_speaking(tts_audio)
        else:
            self.canceller.start_speaking()
    
    def on_tts_stop(self):
        """Call this when AI stops speaking"""
        self.canceller.stop_speaking()
    
    def process_microphone_input(self, audio: np.ndarray) -> np.ndarray:
        """
        Process microphone input to remove AI's voice
        
        Args:
            audio: Raw microphone input
            
        Returns:
            Clean audio with echo removed
        """
        if self.method == "simple":
            # Simple method: return None if AI is speaking
            if not self.canceller.should_process_audio():
                return np.zeros_like(audio)  # Silence
            return audio
        else:
            # Advanced methods: actually cancel echo
            return self.canceller.cancel_echo(audio)
    
    def should_allow_interrupt(self, audio: np.ndarray) -> bool:
        """
        Determine if audio contains user speech (not echo)
        
        Returns:
            True if user is trying to interrupt, False if it's just echo
        """
        if self.method == "simple":
            return self.canceller.should_process_audio()
        elif self.method == "smart":
            return self.canceller.is_user_speaking(audio)
        else:
            # For adaptive: check if cleaned signal has voice
            cleaned = self.process_microphone_input(audio)
            rms = np.sqrt(np.mean(cleaned ** 2))
            return rms > 0.05  # Threshold for user voice


# ============= INTEGRATION EXAMPLE =============

def example_usage():
    """Example of how to integrate with WavesAI"""
    
    # Initialize echo canceller
    echo_cancel = WavesAIEchoCancellation(method="smart")
    
    # When AI starts speaking (TTS)
    def speak_with_echo_cancel(text: str):
        # Generate TTS audio
        tts_audio = generate_tts(text)  # Your TTS function
        
        # Tell echo canceller AI is speaking
        echo_cancel.on_tts_start(tts_audio)
        
        # Play audio
        play_audio(tts_audio)  # Your audio playback
        
        # Tell echo canceller AI stopped
        echo_cancel.on_tts_stop()
    
    # In your interrupt detection loop
    def check_for_interrupt():
        while True:
            # Capture microphone input
            mic_audio = record_from_mic()  # Your recording function
            
            # Clean audio (remove AI's voice)
            clean_audio = echo_cancel.process_microphone_input(mic_audio)
            
            # Check if user is trying to interrupt
            if echo_cancel.should_allow_interrupt(clean_audio):
                # Transcribe and check for commands
                text = whisper.transcribe(clean_audio)
                
                if contains_interrupt_command(text):
                    stop_speaking()
                    return True
            
            time.sleep(0.1)


def generate_tts(text: str) -> np.ndarray:
    """Placeholder TTS function"""
    pass

def play_audio(audio: np.ndarray):
    """Placeholder audio playback"""
    pass

def record_from_mic() -> np.ndarray:
    """Placeholder recording"""
    pass

def contains_interrupt_command(text: str) -> bool:
    """Check if text contains interrupt keywords"""
    return any(word in text.lower() for word in ["stop", "halt", "pause"])

def stop_speaking():
    """Stop TTS playback"""
    pass


if __name__ == "__main__":
    print("WavesAI Echo Cancellation Module")
    print("=" * 50)
    print("\nAvailable methods:")
    print("1. 'simple' - Time-based muting (easiest, most reliable)")
    print("2. 'smart' - RMS + Spectral analysis (recommended)")
    print("3. 'adaptive' - Full adaptive filtering (most advanced)")
    print("\nIntegrate with WavesAI by wrapping TTS calls with echo cancellation")
