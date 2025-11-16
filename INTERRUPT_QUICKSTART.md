# Interrupt Feature - Quick Start Guide

## What's New?

WavesAI now supports **natural interruptions** during AI responses! You can speak while the AI is talking, and it will automatically detect your voice, stop speaking, and listen to you.

## How It Works

**Before (Classic Mode):**
- AI speaks → Mic MUTED → Wait for AI to finish → Mic ON → You speak

**Now (Interrupt Mode - Default):**
- AI speaks → Mic ON → You speak anytime → AI stops immediately → You continue

## The Magic: Acoustic Echo Cancellation

The system intelligently distinguishes between:
- **AI's voice from speakers** (filtered out as echo)
- **Your voice** (detected as interrupt)

This prevents the AI from interrupting itself!

## Quick Start

### 1. Test the Feature

```bash
# Run the test suite to verify everything works
python test_interrupt.py
```

Expected output: All tests pass ✓

### 2. Use Voice Mode

```bash
# Start WavesAI in voice mode
wavesctl start
# or
python wavesai.py
```

Then select voice mode when prompted.

### 3. Try Interrupting

```
AI: "So the solution to your problem is to first configure the..."
YOU: "Wait, stop!" ← Speak while AI is talking
AI: [Immediately stops and listens]
AI: "Yes, what would you like to know?"
```

## Configuration Options

### Check Current Status

```bash
python modules/interrupt_config.py status
```

### Enable/Disable

```python
from modules.interrupt_config import enable_interrupt, disable_interrupt

enable_interrupt()   # Turn on (default)
disable_interrupt()  # Turn off (classic behavior)
```

### Adjust Sensitivity

```python
from modules.interrupt_config import set_sensitivity

set_sensitivity('low')     # Harder to interrupt (more echo protection)
set_sensitivity('medium')  # Balanced (default)
set_sensitivity('high')    # Easier to interrupt (more responsive)
```

### Command Line

```bash
# Enable
python modules/interrupt_config.py enable

# Disable
python modules/interrupt_config.py disable

# Set sensitivity
python modules/interrupt_config.py sensitivity high
```

## Troubleshooting

### Problem: AI keeps interrupting itself

**Cause:** Echo from speakers detected as your voice

**Solutions:**
1. Use headphones (best solution!)
2. Lower speaker volume
3. Decrease sensitivity: `set_sensitivity('low')`
4. Increase `echo_threshold` in config

```python
# In wavesai.py, increase echo protection
ai.aec_system['echo_threshold'] = 0.8  # Default: 0.7
ai.aec_system['interrupt_cooldown'] = 0.8  # Default: 0.5
```

### Problem: Can't interrupt the AI

**Cause:** Your voice not detected or filtered as noise

**Solutions:**
1. Speak louder or closer to mic
2. Increase sensitivity: `set_sensitivity('high')`
3. Check microphone levels
4. Lower `echo_threshold` in config

```python
# In wavesai.py, make interrupts easier
ai.aec_system['echo_threshold'] = 0.6  # Default: 0.7
ai.aec_system['interrupt_energy_threshold'] = 0.03  # Default: 0.05
```

### Problem: Echo still getting through

**Cause:** Poor speaker/mic isolation

**Solutions:**
1. Use headphones (eliminates echo completely)
2. Increase distance between speakers and mic
3. Use directional microphone
4. Add acoustic treatment to room
5. Disable interrupt feature if unusable:

```bash
python modules/interrupt_config.py disable
```

## Best Setup for Interrupt Feature

### Optimal Hardware Setup

1. **Headphones + Microphone**
   - Best: USB headset with mic
   - Good: Separate headphones + USB mic
   - Avoid: Laptop speakers + built-in mic

2. **Microphone Quality**
   - USB microphone with noise cancellation
   - Directional/cardioid pattern preferred
   - Positioned 6-12 inches from mouth

3. **Environment**
   - Quiet room
   - Soft surfaces (carpets, curtains)
   - Minimal echo/reverb

### Software Settings

```python
# For best results (adjust to your setup)
from modules.interrupt_config import InterruptConfig

config = InterruptConfig.DEFAULT_CONFIG
config['echo_threshold'] = 0.7        # 0.6-0.8 range
config['interrupt_energy_threshold'] = 0.05  # 0.03-0.08 range
config['interrupt_cooldown'] = 0.5    # 0.3-0.8 range
```

## Performance Impact

- **CPU Usage:** +5-10% during speech
- **Latency:** ~200ms interrupt detection
- **Memory:** +200KB for reference buffers
- **Minimal impact on conversation quality**

## Technical Details

For developers and advanced users, see:
- `INTERRUPT_FEATURE.md` - Complete technical documentation
- `modules/interrupt_config.py` - Configuration module
- `test_interrupt.py` - Test suite

## Examples

### Example 1: Quick Question

```
AI: "Let me explain the entire history of computing, starting with..."
YOU: "Actually, just tell me about Python"
AI: [Stops immediately]
AI: "Python is a high-level programming language..."
```

### Example 2: Correction

```
AI: "You should use Java for this task because..."
YOU: "No, I want Python"
AI: [Stops]
AI: "Ah, for Python, here's what you should do..."
```

### Example 3: Urgent Interrupt

```
AI: "First, we need to configure X, then Y, then Z..."
YOU: "Stop, I just need X"
AI: [Stops immediately]
AI: "Understood, let me focus on X only..."
```

## Summary

- **Default:** Interrupt feature ENABLED
- **Recommended:** Keep enabled for natural conversation
- **Alternative:** Disable for classic turn-based mode
- **Best Hardware:** Headphones + USB microphone
- **Adjustment:** Use sensitivity settings if needed

## Next Steps

1. Run test: `python test_interrupt.py`
2. Try voice mode: `wavesctl start`
3. Test interrupts with simple queries
4. Adjust sensitivity if needed
5. Use headphones for best results

**Enjoy natural conversations with WavesAI!**

---

Need help? Check `INTERRUPT_FEATURE.md` for detailed troubleshooting and technical information.
