#!/usr/bin/env python3
"""
WavesAI Interrupt Feature Configuration
Control interrupt behavior and acoustic echo cancellation
"""


class InterruptConfig:
    """Configuration for voice interrupt feature"""

    # Default settings for interrupt feature
    DEFAULT_CONFIG = {
        'enabled': True,  # Enable interrupt feature (allows user to interrupt AI during speech)
        'echo_threshold': 0.7,  # Spectral similarity threshold (0-1, higher = more strict)
        'interrupt_energy_threshold': 0.05,  # Minimum energy to consider as user voice
        'interrupt_duration_threshold': 0.3,  # Minimum duration for valid interrupt (seconds)
        'interrupt_cooldown': 0.5,  # Cooldown after TTS starts (prevents immediate self-interruption)
        'confidence_threshold': 0.6,  # Minimum confidence for interrupt detection
    }

    @staticmethod
    def get_config():
        """Get current interrupt configuration"""
        return InterruptConfig.DEFAULT_CONFIG.copy()

    @staticmethod
    def enable_interrupt():
        """Enable interrupt feature"""
        InterruptConfig.DEFAULT_CONFIG['enabled'] = True
        print("Interrupt feature enabled. You can now speak during AI responses.")
        print("The AI will automatically detect and stop speaking when you interrupt.")

    @staticmethod
    def disable_interrupt():
        """Disable interrupt feature (classic behavior)"""
        InterruptConfig.DEFAULT_CONFIG['enabled'] = False
        print("Interrupt feature disabled. Microphone will be muted during AI speech.")

    @staticmethod
    def set_sensitivity(level: str):
        """
        Set interrupt sensitivity
        Args:
            level: 'low', 'medium', 'high'
        """
        if level == 'low':
            # Less sensitive - harder to interrupt
            InterruptConfig.DEFAULT_CONFIG['echo_threshold'] = 0.8
            InterruptConfig.DEFAULT_CONFIG['interrupt_energy_threshold'] = 0.08
            InterruptConfig.DEFAULT_CONFIG['interrupt_cooldown'] = 0.8
            print("Interrupt sensitivity: LOW (harder to interrupt, more echo protection)")

        elif level == 'medium':
            # Balanced (default)
            InterruptConfig.DEFAULT_CONFIG['echo_threshold'] = 0.7
            InterruptConfig.DEFAULT_CONFIG['interrupt_energy_threshold'] = 0.05
            InterruptConfig.DEFAULT_CONFIG['interrupt_cooldown'] = 0.5
            print("Interrupt sensitivity: MEDIUM (balanced)")

        elif level == 'high':
            # More sensitive - easier to interrupt
            InterruptConfig.DEFAULT_CONFIG['echo_threshold'] = 0.6
            InterruptConfig.DEFAULT_CONFIG['interrupt_energy_threshold'] = 0.03
            InterruptConfig.DEFAULT_CONFIG['interrupt_cooldown'] = 0.3
            print("Interrupt sensitivity: HIGH (easier to interrupt)")

        else:
            print(f"Unknown sensitivity level: {level}")
            print("Available levels: low, medium, high")

    @staticmethod
    def print_status():
        """Print current configuration"""
        config = InterruptConfig.DEFAULT_CONFIG
        print("\nInterrupt Feature Configuration:")
        print(f"  Status: {'ENABLED' if config['enabled'] else 'DISABLED'}")
        print(f"  Echo Threshold: {config['echo_threshold']:.2f}")
        print(f"  Energy Threshold: {config['interrupt_energy_threshold']:.3f}")
        print(f"  Cooldown Period: {config['interrupt_cooldown']:.2f}s")
        print(f"  Confidence Threshold: {config['confidence_threshold']:.2f}")
        print()

        if config['enabled']:
            print("How it works:")
            print("  • Microphone stays ON during AI speech")
            print("  • AI's voice is filtered using Acoustic Echo Cancellation")
            print("  • Your voice is detected and AI stops speaking")
            print("  • Natural conversation flow with interruptions")
        else:
            print("Classic Mode:")
            print("  • Microphone is MUTED during AI speech")
            print("  • Wait for AI to finish before speaking")
            print("  • No echo issues but less natural")


# Quick access functions
def enable_interrupt():
    """Enable interrupt feature"""
    InterruptConfig.enable_interrupt()


def disable_interrupt():
    """Disable interrupt feature"""
    InterruptConfig.disable_interrupt()


def set_sensitivity(level: str):
    """Set interrupt sensitivity (low/medium/high)"""
    InterruptConfig.set_sensitivity(level)


def status():
    """Show interrupt feature status"""
    InterruptConfig.print_status()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("WavesAI Interrupt Feature Configuration")
        print()
        print("Usage:")
        print("  python interrupt_config.py status          - Show current settings")
        print("  python interrupt_config.py enable          - Enable interrupt feature")
        print("  python interrupt_config.py disable         - Disable interrupt feature")
        print("  python interrupt_config.py sensitivity <level>  - Set sensitivity (low/medium/high)")
        print()
        status()
    else:
        cmd = sys.argv[1].lower()

        if cmd == 'status':
            status()
        elif cmd == 'enable':
            enable_interrupt()
        elif cmd == 'disable':
            disable_interrupt()
        elif cmd == 'sensitivity' and len(sys.argv) > 2:
            set_sensitivity(sys.argv[2].lower())
        else:
            print(f"Unknown command: {cmd}")
            print("Use 'python interrupt_config.py' for help")
