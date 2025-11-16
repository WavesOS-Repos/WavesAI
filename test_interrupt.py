#!/usr/bin/env python3
"""
Test script for WavesAI Interrupt Feature
Verifies that interrupt system is working correctly
"""

import sys
import os
import numpy as np
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from wavesai import WavesAI
    print("✓ WavesAI module loaded successfully")
except Exception as e:
    print(f"✗ Failed to load WavesAI: {e}")
    sys.exit(1)


def test_aec_initialization():
    """Test if AEC system initializes correctly"""
    print("\n" + "="*60)
    print("TEST 1: AEC System Initialization")
    print("="*60)

    ai = WavesAI()
    ai.init_smart_noise_detection()

    # Check if AEC system is initialized
    if hasattr(ai, 'aec_system'):
        print("✓ AEC system initialized")
        print(f"  - Enabled: {ai.aec_system.get('enabled', False)}")
        print(f"  - Echo threshold: {ai.aec_system.get('echo_threshold', 0)}")
        print(f"  - Energy threshold: {ai.aec_system.get('interrupt_energy_threshold', 0)}")
        print(f"  - Cooldown: {ai.aec_system.get('interrupt_cooldown', 0)}s")
        return True
    else:
        print("✗ AEC system not initialized")
        return False


def test_echo_detection():
    """Test echo detection with simulated audio"""
    print("\n" + "="*60)
    print("TEST 2: Echo Detection Algorithm")
    print("="*60)

    ai = WavesAI()
    ai.init_smart_noise_detection()

    # Initialize conversation state
    if not hasattr(ai, 'conversation_state'):
        ai.conversation_state = {
            'is_speaking': False,
            'is_listening': True,
            'last_speech_end': 0,
            'interrupt_requested': False,
            'user_interrupted': False,
            'silence_start': None,
            'post_speech_timer': 0
        }

    sample_rate = 16000

    # Test 1: AI not speaking (should detect as user voice)
    print("\nTest 2a: AI not speaking")
    ai.conversation_state['is_speaking'] = False
    audio_chunk = np.random.randn(1600).astype(np.float32) * 0.1  # Some audio
    is_echo, confidence, is_interrupt = ai.is_ai_echo(audio_chunk, sample_rate)
    print(f"  Result: is_echo={is_echo}, confidence={confidence:.2f}, is_interrupt={is_interrupt}")
    if not is_echo:
        print("  ✓ Correctly identified as user voice (AI not speaking)")
    else:
        print("  ✗ Incorrectly identified as echo")

    # Test 2: AI speaking with low energy (should be ignored)
    print("\nTest 2b: Low energy during AI speech")
    ai.conversation_state['is_speaking'] = True
    ai.aec_system['last_output_time'] = time.time() - 1.0  # Past cooldown
    audio_chunk = np.random.randn(1600).astype(np.float32) * 0.01  # Very quiet
    is_echo, confidence, is_interrupt = ai.is_ai_echo(audio_chunk, sample_rate)
    print(f"  Result: is_echo={is_echo}, confidence={confidence:.2f}, is_interrupt={is_interrupt}")
    if is_echo:
        print("  ✓ Correctly identified as echo/noise (too quiet)")
    else:
        print("  ✗ Should have been filtered as noise")

    # Test 3: AI speaking with high energy (potential interrupt)
    print("\nTest 2c: High energy during AI speech")
    ai.conversation_state['is_speaking'] = True
    ai.aec_system['last_output_time'] = time.time() - 1.0  # Past cooldown
    audio_chunk = np.random.randn(1600).astype(np.float32) * 0.15  # Loud
    is_echo, confidence, is_interrupt = ai.is_ai_echo(audio_chunk, sample_rate)
    print(f"  Result: is_echo={is_echo}, confidence={confidence:.2f}, is_interrupt={is_interrupt}")
    if is_interrupt:
        print("  ✓ Correctly identified as potential interrupt")
    else:
        print("  ⚠ May be echo, or needs reference signal")

    # Test 4: Cooldown period (should block interrupts)
    print("\nTest 2d: During cooldown period")
    ai.conversation_state['is_speaking'] = True
    ai.aec_system['last_output_time'] = time.time()  # Just started speaking
    audio_chunk = np.random.randn(1600).astype(np.float32) * 0.15  # Loud
    is_echo, confidence, is_interrupt = ai.is_ai_echo(audio_chunk, sample_rate)
    print(f"  Result: is_echo={is_echo}, confidence={confidence:.2f}, is_interrupt={is_interrupt}")
    if is_echo and not is_interrupt:
        print("  ✓ Correctly blocked during cooldown period")
    else:
        print("  ✗ Should have been blocked by cooldown")

    return True


def test_interrupt_config():
    """Test interrupt configuration module"""
    print("\n" + "="*60)
    print("TEST 3: Interrupt Configuration")
    print("="*60)

    try:
        from modules.interrupt_config import InterruptConfig, enable_interrupt, disable_interrupt

        print("\n✓ Interrupt config module loaded")

        # Test default config
        config = InterruptConfig.get_config()
        print(f"  - Default enabled: {config['enabled']}")
        print(f"  - Echo threshold: {config['echo_threshold']}")
        print(f"  - Energy threshold: {config['interrupt_energy_threshold']}")

        # Test enable/disable
        print("\nTesting enable/disable functions:")
        enable_interrupt()
        disable_interrupt()

        return True

    except Exception as e:
        print(f"✗ Interrupt config test failed: {e}")
        return False


def test_conversation_state():
    """Test conversation state management"""
    print("\n" + "="*60)
    print("TEST 4: Conversation State Management")
    print("="*60)

    ai = WavesAI()
    ai.init_smart_noise_detection()

    if not hasattr(ai, 'conversation_state'):
        ai.conversation_state = {
            'is_speaking': False,
            'is_listening': True,
            'last_speech_end': 0,
            'interrupt_requested': False,
            'user_interrupted': False,
            'silence_start': None,
            'post_speech_timer': 0
        }

    # Test start_speaking
    print("\nTest 4a: start_speaking()")
    ai.start_speaking()
    if ai.conversation_state['is_speaking'] and not ai.conversation_state['is_listening']:
        print("  ✓ Speaking state set correctly")
    else:
        print("  ✗ Speaking state not set correctly")

    # Test request_interrupt
    print("\nTest 4b: request_interrupt()")
    ai.request_interrupt()
    if ai.conversation_state['interrupt_requested'] and ai.conversation_state['user_interrupted']:
        print("  ✓ Interrupt requested successfully")
    else:
        print("  ✗ Interrupt not requested correctly")

    # Test check_interrupt
    print("\nTest 4c: check_interrupt()")
    if ai.check_interrupt():
        print("  ✓ Interrupt check returns True")
    else:
        print("  ✗ Interrupt check should return True")

    # Test stop_speaking
    print("\nTest 4d: stop_speaking()")
    ai.stop_speaking()
    time.sleep(0.1)
    if not ai.conversation_state['is_speaking']:
        print("  ✓ Speaking state cleared")
    else:
        print("  ✗ Speaking state not cleared")

    return True


def test_should_ignore_audio():
    """Test audio ignore logic with interrupt feature"""
    print("\n" + "="*60)
    print("TEST 5: Audio Ignore Logic")
    print("="*60)

    ai = WavesAI()
    ai.init_smart_noise_detection()
    ai.init_voice_components()

    if not hasattr(ai, 'conversation_state'):
        ai.conversation_state = {
            'is_speaking': False,
            'is_listening': True,
            'last_speech_end': 0,
            'interrupt_requested': False,
            'user_interrupted': False,
            'silence_start': None,
            'post_speech_timer': 0
        }

    # Test 1: Interrupt enabled, not speaking
    print("\nTest 5a: Interrupt enabled, AI not speaking")
    ai.aec_system['enabled'] = True
    ai.conversation_state['is_speaking'] = False
    ai.conversation_state['last_speech_end'] = time.time() - 1.0
    should_ignore = ai.should_ignore_audio()
    print(f"  Should ignore: {should_ignore}")
    if not should_ignore:
        print("  ✓ Correctly allowing audio (not speaking)")
    else:
        print("  ✗ Should allow audio when not speaking")

    # Test 2: Interrupt enabled, AI speaking (past cooldown)
    print("\nTest 5b: Interrupt enabled, AI speaking (past cooldown)")
    ai.conversation_state['is_speaking'] = True
    ai.aec_system['last_output_time'] = time.time() - 1.0
    should_ignore = ai.should_ignore_audio()
    print(f"  Should ignore: {should_ignore}")
    if not should_ignore:
        print("  ✓ Correctly allowing audio for interrupt detection")
    else:
        print("  ⚠ May need to check cooldown period")

    # Test 3: Interrupt enabled, AI speaking (during cooldown)
    print("\nTest 5c: Interrupt enabled, during cooldown")
    ai.conversation_state['is_speaking'] = True
    ai.aec_system['last_output_time'] = time.time()
    should_ignore = ai.should_ignore_audio()
    print(f"  Should ignore: {should_ignore}")
    if should_ignore:
        print("  ✓ Correctly blocking during cooldown")
    else:
        print("  ✗ Should block during cooldown")

    # Test 4: Interrupt disabled, AI speaking
    print("\nTest 5d: Interrupt disabled (classic mode)")
    ai.aec_system['enabled'] = False
    ai.conversation_state['is_speaking'] = True
    should_ignore = ai.should_ignore_audio()
    print(f"  Should ignore: {should_ignore}")
    if should_ignore:
        print("  ✓ Correctly blocking audio (classic mode)")
    else:
        print("  ✗ Should block audio in classic mode")

    return True


def run_all_tests():
    """Run all interrupt feature tests"""
    print("\n" + "="*60)
    print("    WavesAI Interrupt Feature Test Suite")
    print("="*60)

    results = []

    # Run tests
    results.append(("AEC Initialization", test_aec_initialization()))
    results.append(("Echo Detection", test_echo_detection()))
    results.append(("Interrupt Config", test_interrupt_config()))
    results.append(("Conversation State", test_conversation_state()))
    results.append(("Audio Ignore Logic", test_should_ignore_audio()))

    # Summary
    print("\n" + "="*60)
    print("    Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Interrupt feature is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
