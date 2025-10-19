#!/usr/bin/env python3
"""
WavesAI Command Handler Module
Handles command parsing, execution, and quick responses
"""

import os
import subprocess
from typing import Optional, Dict


class CommandHandler:
    """Handles command parsing and execution"""
    
    def __init__(self):
        pass
    
    def smart_execute(self, user_input: str, system_context: Dict) -> Optional[str]:
        """Handle common queries without AI inference"""
        lower_input = user_input.lower().strip()
        
        # Time/Date queries
        time_keywords = ['what time', 'what is the time', 'tell me the time', 'current time', 
                        'what\'s the time', 'time is it', 'show time']
        if any(keyword in lower_input for keyword in time_keywords):
            return f"The current time is {system_context['current_time']}, sir."
        
        # System update commands
        if any(phrase in lower_input for phrase in ['update system', 'update arch', 'system update', 
                                                      'upgrade system', 'pacman -syu', 'pacman update']):
            return None  # Let AI handle to generate proper command
        
        # Open application
        if lower_input.startswith('open '):
            return self._handle_open_command(lower_input)
        
        # Close/Kill application
        if lower_input.startswith('close ') or lower_input.startswith('kill '):
            return self._handle_close_command(lower_input)
        
        # Launch application
        if lower_input.startswith('launch ') or lower_input.startswith('run '):
            return self._handle_launch_command(lower_input)
        
        # Quick system stats
        if lower_input in ['stats', 'quick status', 'system']:
            return f"System Status: CPU {system_context['cpu_usage']}, RAM {system_context['ram_usage']}, {system_context['gpu_info']}"
        
        # System control commands
        system_commands = {
            'reboot': 'sudo reboot',
            'restart': 'sudo reboot',
            'shutdown': 'sudo shutdown -h now',
            'shutdown now': 'sudo shutdown -h now',
            'poweroff': 'sudo poweroff',
            'halt': 'sudo halt',
            'suspend': 'sudo systemctl suspend',
            'hibernate': 'sudo systemctl hibernate',
            'lock': 'gnome-screensaver-command -l || xlock',
            'logout': 'gnome-session-quit --logout',
            'update system': 'sudo pacman -Syu',
            'update': 'sudo pacman -Syu',
            'upgrade': 'sudo pacman -Syu'
        }
        
        if lower_input in system_commands:
            command = system_commands[lower_input]
            return f"EXECUTE_COMMAND:{command}"
        
        # File operations
        if lower_input.startswith('create file ') or lower_input.startswith('make file '):
            filename = lower_input.replace('create file ', '').replace('make file ', '').strip()
            return f"EXECUTE_COMMAND:touch {filename}"
        
        if lower_input.startswith('delete file ') or lower_input.startswith('remove file '):
            filename = lower_input.replace('delete file ', '').replace('remove file ', '').strip()
            return f"EXECUTE_COMMAND:rm {filename}"
        
        if lower_input.startswith('list files') or lower_input.startswith('show files'):
            return f"EXECUTE_COMMAND:ls -la"
        
        if lower_input.startswith('show directory') or lower_input.startswith('current directory'):
            return f"EXECUTE_COMMAND:pwd && ls -la"
        
        # Package management
        if lower_input.startswith('install '):
            package = lower_input.replace('install ', '').strip()
            return f"EXECUTE_COMMAND:sudo pacman -S {package}"
        
        if lower_input.startswith('reinstall ') or lower_input.startswith('re-install ') or lower_input.startswith('re install ') or 'please reinstall' in lower_input:
            package = lower_input.replace('reinstall ', '').replace('re-install ', '').replace('re install ', '').replace('please reinstall ', '').replace(' in this system', '').replace(' on this system', '').strip()
            return f"EXECUTE_COMMAND:sudo pacman -S {package}"
        
        if lower_input.startswith('uninstall ') or lower_input.startswith('remove package '):
            package = lower_input.replace('uninstall ', '').replace('remove package ', '').strip()
            return f"EXECUTE_COMMAND:sudo pacman -R {package}"
        
        if lower_input.startswith('search package '):
            package = lower_input.replace('search package ', '').strip()
            return f"EXECUTE_COMMAND:pacman -Ss {package}"
        
        # Process management
        if lower_input.startswith('kill process ') or lower_input.startswith('stop process '):
            process = lower_input.replace('kill process ', '').replace('stop process ', '').strip()
            return f"EXECUTE_COMMAND:killall {process}"
        
        if lower_input.startswith('find process ') or lower_input.startswith('search process '):
            process = lower_input.replace('find process ', '').replace('search process ', '').strip()
            return f"EXECUTE_COMMAND:ps aux | grep {process}"
        
        return None  # Let AI handle
    
    def _handle_open_command(self, lower_input: str) -> str:
        """Handle open application command"""
        app_command = lower_input.replace('open ', '').strip()
        
        # Handle "open X in Y" pattern (e.g., "open nvim in kitty")
        if ' in ' in app_command:
            parts = app_command.split(' in ')
            inner_app = parts[0].strip()
            terminal = parts[1].strip()
            
            # Check if terminal exists
            check = subprocess.run(f"which {terminal}", shell=True, capture_output=True, text=True)
            if check.returncode == 0:
                subprocess.Popen(f"{terminal} -e {inner_app}", shell=True, 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Opening {inner_app} in {terminal}, sir."
            else:
                return f"Terminal '{terminal}' is not installed."
        
        # Simple app opening - extract just the app name
        app = app_command.split()[0]
        check = subprocess.run(f"which {app}", shell=True, capture_output=True, text=True)
        if check.returncode == 0:
            subprocess.Popen(app, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opening {app}, sir."
        else:
            return f"Application '{app}' is not installed, sir. Would you like me to install it?"
    
    def _handle_close_command(self, lower_input: str) -> str:
        """Handle close/kill application command"""
        app = lower_input.replace('close ', '').replace('kill ', '').replace(' app', '').strip()
        result = subprocess.run(f"killall {app}", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Closed {app}, sir."
        else:
            return f"Could not find {app} process."
    
    def _handle_launch_command(self, lower_input: str) -> str:
        """Handle launch/run application command"""
        app = lower_input.replace('launch ', '').replace('run ', '').strip()
        check = subprocess.run(f"which {app}", shell=True, capture_output=True, text=True)
        if check.returncode == 0:
            subprocess.Popen(app, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launching {app}, sir."
        else:
            return f"'{app}' is not found. Shall I search for it?"
    
    def is_safe_command(self, command: str) -> bool:
        """Check if command is safe to auto-execute"""
        safe_commands = [
            'touch', 'mkdir', 'ls', 'cat', 'echo', 'pwd', 'date',
            'cp', 'mv', 'which', 'find', 'grep', 'nano', 'vim',
            'gedit', 'code', 'firefox', 'chromium', 'kitty'
        ]
        
        dangerous_patterns = ['rm -rf', 'sudo', 'dd', 'mkfs', 'chmod 777', 'chown']
        
        # Check if starts with safe command
        cmd_start = command.split()[0] if command.split() else ""
        
        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if pattern in command:
                return False
        
        # Check if it's a safe command or app launch
        return any(command.startswith(safe) for safe in safe_commands) or '&' in command
    
    def execute_command(self, command: str, sudo: bool = False, timeout: int = 30) -> Dict:
        """Execute shell command with safety checks"""
        dangerous_commands = ['rm -rf /', 'mkfs', 'dd if=', ':(){:|:&};:', 'chmod -R 777 /', '> /dev/sda']
        
        for dangerous in dangerous_commands:
            if dangerous in command:
                return {"success": False, "error": "Dangerous command blocked for safety"}
        
        try:
            # Check if this is a background process (ends with &)
            is_background = command.strip().endswith('&')
            
            if is_background:
                # Remove the & since we'll handle backgrounding properly
                command = command.strip().rstrip('&').strip()
                
                # Use setsid for complete detachment (most reliable method)
                full_command = f"setsid {command} >/dev/null 2>&1 </dev/null &"
                process = subprocess.Popen(
                    full_command,
                    shell=True,
                    start_new_session=True
                )
                
                return {
                    "success": True,
                    "output": f"Process started in background",
                    "error": ""
                }
            
            # For foreground commands
            # Check if command needs sudo interaction
            if 'sudo' in command:
                print("\n\033[1;33m[Warning]\033[0m Command requires sudo password. You have 60 seconds to enter it.")
                timeout = 60  # Increase timeout for sudo commands
            
            if sudo and not command.startswith('sudo'):
                command = f"sudo {command}"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out (may need user input)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
