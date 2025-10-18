#!/usr/bin/env python3
import os
from pathlib import Path

# Add smart_execute method after __init__
patch_content = '''
    def smart_execute(self, user_input: str):
        """Handle common queries without AI inference"""
        lower_input = user_input.lower()
        
        if any(word in lower_input for word in ['time', 'date', 'clock']):
            info = self.get_system_context()
            return f"The current time is {info['current_time']}, sir."
        
        if lower_input.startswith('open '):
            app = lower_input.replace('open ', '').strip()
            check = subprocess.run(f"which {app}", shell=True, capture_output=True)
            if check.returncode == 0:
                result = self.execute_command(f"{app} > /dev/null 2>&1 &")
                return f"Opening {app}, sir." if result['success'] else f"Failed to open {app}."
            else:
                return f"'{app}' is not installed. Shall I install it for you?"
        
        return None
'''

print("Patch created! Add the smart_execute method to your WavesAI class.")
