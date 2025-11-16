# WavesAI Interrupt Feature

## Overview

The **Interrupt Feature** allows you to naturally interrupt the AI while it's speaking, just like in a real conversation. The AI will detect your voice, stop speaking, and listen to your new input.

## The Challenge: Echo vs. User Voice

**Problem:** When the microphone is ON during AI speech, it can hear:
1. The AI's own voice from speakers (echo)
2. Your actual voice (what we want)

If not handled properly, the AI would constantly interrupt itself!

## Our Solution: Acoustic Echo Cancellation (AEC)

WavesAI uses intelligent **Acoustic Echo Cancellation** to distinguish between:
- **AI's voice** (from speakers) → Filtered out as echo
- **Your voice** (real interruption) → Detected and triggers stop

### How It Works

1. **Reference Signal Storage**
   - AI stores its own voice output as reference
   - Creates spectral fingerprint of its speech

2. **Real-time Comparison**
   - Incoming audio is compared to AI's voice reference
   - Spectral analysis detects similarity

3. **Intelligent Detection**
   - High similarity + low time offset = Echo (ignore)
   - Low similarity + high energy = User voice (interrupt!)

4. **Multi-layer Filtering**
   ```
   Audio Input → Energy Check → Cooldown Check → Spectral Analysis → Decision
   ```

## Features

### 1. Automatic Echo Filtering
- Spectral analysis compares mic input with AI's voice
- High similarity = echo (ignored)
- Low similarity = user speech (interrupt triggered)

### 2. Energy-Based Detection
- Too quiet = noise (ignored)
- Appropriate energy = potential user speech

### 3. Cooldown Period
- Brief delay after AI starts speaking
- Prevents immediate self-interruption
- Default: 0.5 seconds

### 4. Confidence Scoring
- Each detection has confidence level
- High confidence required for interrupt

## Configuration

### Enable/Disable Interrupt

```python
# In Python
from modules.interrupt_config import enable_interrupt, disable_interrupt

enable_interrupt()   # Turn on interrupt feature
disable_interrupt()  # Turn off (classic mode: mic muted during speech)
```

### Sensitivity Levels

```python
from modules.interrupt_config import set_sensitivity

set_sensitivity('low')     # Harder to interrupt (more echo protection)
set_sensitivity('medium')  # Balanced (default)
set_sensitivity('high')    # Easier to interrupt (more responsive)
```

### Check Status

```python
from modules.interrupt_config import status

status()  # Shows current configuration
```

## Command Line Usage

```bash
# Show current settings
python modules/interrupt_config.py status

# Enable interrupt feature
python modules/interrupt_config.py enable

# Disable interrupt feature
python modules/interrupt_config.py disable

# Set sensitivity
python modules/interrupt_config.py sensitivity medium
```

## Technical Details

### AEC System Parameters

```python
aec_system = {
    'enabled': True,                          # Feature on/off
    'echo_threshold': 0.7,                    # Spectral similarity (0-1)
    'interrupt_energy_threshold': 0.05,       # Min energy for user voice
    'interrupt_duration_threshold': 0.3,      # Min duration (seconds)
    'interrupt_cooldown': 0.5,                # Cooldown after TTS start
    'ai_voice_reference': deque(maxlen=200),  # AI voice history
    'user_voice_profile': deque(maxlen=50)    # User voice learning
}
```

### Detection Algorithm

```python
def is_ai_echo(audio_chunk, sample_rate) -> (is_echo, confidence, is_interrupt):
    # 1. Energy check
    if energy < threshold:
        return True, 0.9, False  # Too quiet = echo/noise

    # 2. Cooldown check
    if time_since_speaking < cooldown:
        return True, 0.95, False  # Too soon = echo

    # 3. Spectral analysis
    if spectral_similarity > echo_threshold:
        return True, similarity, False  # Similar = echo

    # 4. User detection
    if energy > threshold and similarity < 0.5:
        return False, 1.0 - similarity, True  # Different = user!

    return True, 0.5, False  # Default: treat as echo
```

## Behavioral Differences

### With Interrupt ENABLED (Default)
```
AI Speaking: "So the solution to your problem is..."
YOU: "Wait, stop!"
[AI immediately stops]
AI: [Listening for your new input]
```

**Technical:**
- Microphone: ON during AI speech
- Echo: Filtered using AEC
- Interrupt: Detected in ~200ms
- Experience: Natural conversation flow

### With Interrupt DISABLED (Classic)
```
AI Speaking: "So the solution to your problem is..."
YOU: "Wait, stop!"
[Your voice is not heard - mic is muted]
[AI continues speaking]
[AI finishes]
[2 second delay]
AI: [Now listening]
```

**Technical:**
- Microphone: MUTED during AI speech
- Echo: No issue (mic is off)
- Interrupt: Not possible
- Experience: Turn-based conversation

## Performance Impact

### CPU Usage
- AEC adds ~5-10% CPU overhead
- Spectral analysis runs in real-time
- Optimized with numpy/FFT

### Latency
- Echo detection: <50ms
- Interrupt trigger: ~200ms total
- TTS stop: ~100ms

### Memory
- Reference buffer: ~200 audio chunks
- Each chunk: ~1KB
- Total: ~200KB additional memory

## Troubleshooting

### AI Keeps Interrupting Itself

**Problem:** False interrupts from echo
**Solutions:**
1. Decrease sensitivity: `set_sensitivity('low')`
2. Increase cooldown period
3. Lower speaker volume
4. Improve room acoustics

### Can't Interrupt AI

**Problem:** Your voice not detected
**Solutions:**
1. Increase sensitivity: `set_sensitivity('high')`
2. Speak louder/closer to microphone
3. Check microphone levels
4. Reduce background noise

### Echo Still Getting Through

**Problem:** AI voice detected as user
**Solutions:**
1. Increase `echo_threshold` (0.7 → 0.8)
2. Use headphones instead of speakers
3. Increase distance between speakers and mic
4. Lower speaker volume

## Advanced Configuration

### Manual Configuration

Edit `wavesai.py` directly:

```python
self.aec_system = {
    'enabled': True,
    'echo_threshold': 0.75,              # Adjust for your setup
    'interrupt_energy_threshold': 0.06,   # Higher = louder voice needed
    'interrupt_cooldown': 0.6,            # Longer = more protection
}
```

### Room-Specific Tuning

Different rooms have different acoustics:

```python
# Large room with echo
aec_system['echo_threshold'] = 0.8
aec_system['interrupt_cooldown'] = 0.7

# Small room, close mic
aec_system['echo_threshold'] = 0.6
aec_system['interrupt_cooldown'] = 0.3

# Noisy environment
aec_system['interrupt_energy_threshold'] = 0.1
```

## Best Practices

### For Best Results

1. **Use Headphones**
   - Eliminates speaker echo completely
   - Most reliable setup
   - No AEC needed

2. **Proper Speaker Placement**
   - Place speakers away from microphone
   - Use directional microphone if possible
   - Reduce volume if echo detected

3. **Acoustic Treatment**
   - Reduce room echo with soft furnishings
   - Avoid hard, reflective surfaces near mic/speakers
   - Carpets, curtains, and cushions help

4. **Microphone Selection**
   - Use quality USB microphone
   - Noise-cancelling/directional preferred
   - Avoid built-in laptop mics with speakers

## Examples

### Enable with Custom Settings

```python
from modules.interrupt_config import InterruptConfig

# Create custom config
config = InterruptConfig()
config.DEFAULT_CONFIG.update({
    'enabled': True,
    'echo_threshold': 0.75,
    'interrupt_energy_threshold': 0.06,
    'interrupt_cooldown': 0.6
})

# Apply and check
config.enable_interrupt()
config.print_status()
```

### Runtime Toggle

```python
# During conversation, toggle interrupt
if user_wants_classic_mode:
    disable_interrupt()
else:
    enable_interrupt()
```

## Future Enhancements

Planned improvements:

1. **Adaptive AEC**
   - Learn user's voice profile over time
   - Automatically adjust thresholds

2. **Multi-speaker Detection**
   - Distinguish between multiple speakers
   - Different echo profiles per speaker

3. **Context-Aware Interrupts**
   - Allow interrupts for questions
   - Prevent interrupts during critical info

4. **Visual Feedback**
   - Real-time confidence display
   - Echo detection indicator
   - Interrupt success rate

## Summary

The interrupt feature brings natural conversation flow to WavesAI:

✓ Speak anytime during AI response
✓ AI automatically stops when interrupted
✓ Intelligent echo cancellation
✓ Configurable sensitivity
✓ Low latency (~200ms)
✓ Minimal performance impact

**Default:** Enabled with medium sensitivity
**Recommended:** Keep enabled for natural experience
**Alternative:** Disable for classic turn-based mode

---

**Need Help?**
- Check troubleshooting section
- Adjust sensitivity levels
- Use headphones for best results
- Report issues on GitHub
