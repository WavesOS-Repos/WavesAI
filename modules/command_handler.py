#!/usr/bin/env python3
"""
WavesAI Command Handler Module
Handles command parsing, execution, and quick responses
"""

import os
import subprocess
from typing import Optional, Dict
from .pacman_handler import PacmanHandler
from .process_detector import ProcessDetector
from .error_analyzer import get_error_analyzer


class CommandHandler:
    """Handles command parsing and execution"""
    
    def __init__(self):
        self.pacman_handler = PacmanHandler()
        self.process_detector = ProcessDetector()
    
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
        
        # News queries - let AI handle with search context
        news_keywords = ['latest news', 'indian news', 'world news', 'breaking news', 'news today', 'current news']
        if any(keyword in lower_input for keyword in news_keywords):
            return None  # Let AI handle with search context
        
        # Weather queries - let AI handle with weather context
        weather_keywords = ['weather', 'temperature', 'climate', 'forecast', 'rain', 'sunny', 'cloudy']
        if any(keyword in lower_input for keyword in weather_keywords):
            return None  # Let AI handle with weather context
        
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
            # Use smart process detector for better results
            matches = self.process_detector.find_process_by_name(process)
            if matches:
                result = f"Found {len(matches)} processes for '{process}':\n"
                for match in matches:
                    result += f"  • {match['name']} (PID: {match['pid']}, CPU: {match['cpu']}%, RAM: {match['mem']}%)\n"
                return result.rstrip()
            else:
                return f"No processes found for '{process}'. Try 'ps aux | grep {process}' for raw search."
        
        # Resource monitoring commands
        if 'how much ram' in lower_input or 'memory usage' in lower_input:
            # Extract app name
            for word in ['ram', 'memory', 'using', 'usage', 'by', 'is', 'much', 'how']:
                lower_input = lower_input.replace(word, '').strip()
            app = lower_input.strip()
            if app:
                return f"EXECUTE_COMMAND:ps aux | grep -i {app} | grep -v grep | awk '{{sum+=$6}} END {{printf \"%.1f MB\\n\", sum/1024}}'"
        
        if 'how much cpu' in lower_input or 'cpu usage' in lower_input:
            # Extract app name
            for word in ['cpu', 'usage', 'using', 'by', 'is', 'much', 'how']:
                lower_input = lower_input.replace(word, '').strip()
            app = lower_input.strip()
            if app:
                return f"EXECUTE_COMMAND:ps aux | grep -i {app} | grep -v grep | awk '{{sum+=$3}} END {{print sum \"%\"}}'"
        
        if 'disk space' in lower_input and ('used by' in lower_input or 'being used by' in lower_input):
            # Extract app name
            parts = lower_input.split('by')
            if len(parts) > 1:
                app = parts[-1].strip()
                # Common app installation paths
                if app == 'obsidian':
                    return f"EXECUTE_COMMAND:du -sh /opt/Obsidian ~/.config/obsidian"
                elif app == 'firefox':
                    return f"EXECUTE_COMMAND:du -sh ~/.mozilla/firefox"
                elif app == 'chrome' or app == 'chromium':
                    return f"EXECUTE_COMMAND:du -sh ~/.config/chromium ~/.cache/chromium"
                else:
                    return f"EXECUTE_COMMAND:du -sh /opt/{app} ~/.config/{app} 2>/dev/null || echo 'App directory not found'"
        
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
        """Handle close/kill application command with smart process detection"""
        app = lower_input.replace('close ', '').replace('kill ', '').replace(' app', '').strip()
        
        # Use smart process detector
        result = self.process_detector.kill_process_smart(app)
        
        if result['success']:
            return result['message']
        else:
            # Show what processes were found (if any) to help user
            if result['matches']:
                process_info = []
                for match in result['matches'][:3]:  # Show first 3 matches
                    process_info.append(f"{match['name']} (PID: {match['pid']})")
                
                return f"Found {len(result['matches'])} processes for '{app}' but couldn't kill them: {', '.join(process_info)}. Try with sudo or check permissions."
            else:
                return result['message']
    
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
            if sudo and not command.startswith('sudo'):
                command = f"sudo {command}"
            
            # Check if this is an interactive command that needs user input
            interactive_commands = [
                'sudo pacman -Syu', 'sudo pacman -S', 'pacman -Syu', 'pacman -S',
                'sudo apt update', 'sudo apt upgrade', 'sudo apt install',
                'nano', 'vim', 'vi', 'emacs', 'htop', 'top', 'less', 'more',
                'sudo systemctl', 'systemctl', 'ssh', 'scp', 'rsync',
                'git commit', 'git rebase', 'git merge'
            ]
            
            is_interactive = any(cmd in command for cmd in interactive_commands)
            
            if is_interactive:
                # Check if this is a pacman command that needs special handling
                if self.pacman_handler.should_handle_command(command):
                    print(f"\n\033[1;32m[Smart Pacman]\033[0m Processing package management command...")
                    return self.pacman_handler.execute_pacman_command(command)
                else:
                    # Run other interactive commands directly in terminal (no output capture)
                    print(f"\n\033[1;32m[Interactive]\033[0m Running command in terminal...")
                    print("\033[1;33m[Note]\033[0m You can interact with this command normally (enter passwords, make selections, etc.)")
                    result = subprocess.run(command, shell=True)
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "output": "Command completed successfully",
                            "error": ""
                        }
                    else:
                        return {
                            "success": False,
                            "output": "",
                            "error": f"Command exited with code {result.returncode}"
                        }
            else:
                # Non-interactive commands - capture output
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "output": result.stdout,
                        "error": ""
                    }
                else:
                    # Analyze error and provide intelligent solution
                    error_analyzer = get_error_analyzer()
                    error_analysis = error_analyzer.analyze_error(result.stderr, command)
                    
                    return {
                        "success": False,
                        "output": result.stdout,
                        "error": result.stderr,
                        "error_analysis": error_analysis
                    }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out (may need user input)",
                "error_analysis": {
                    "summary": "Command timeout",
                    "solution": "The command took too long. It may require user input or be stuck.",
                    "category": "timeout"
                }
            }
        except Exception as e:
            error_analyzer = get_error_analyzer()
            error_analysis = error_analyzer.analyze_error(str(e), command)
            return {
                "success": False,
                "error": str(e),
                "error_analysis": error_analysis
            }
