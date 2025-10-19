#!/usr/bin/env python3
"""
Pacman Handler - Intelligent pacman command processing
Filters verbose output and provides clean user interaction
"""

import subprocess
import re
import sys
from typing import Dict, List, Optional, Tuple

class PacmanHandler:
    def __init__(self):
        self.verbose_patterns = [
            r':: Synchronizing package databases\.\.\.',
            r'.*is up to date',
            r':: Starting full system upgrade\.\.\.',
            r'resolving dependencies\.\.\.',
            r'looking for conflicting packages\.\.\.',
            r'\(\d+/\d+\) checking.*\[#+\] \d+%',
            r'\(\d+/\d+\) loading.*\[#+\] \d+%',
            r'\(\d+/\d+\) upgrading.*\[#+\] \d+%',
            r'\(\d+/\d+\) installing.*\[#+\] \d+%',
            r':: Processing package changes\.\.\.',
            r':: Running post-transaction hooks\.\.\.',
            r'\(\d+/\d+\) Reloading.*',
            r'\(\d+/\d+\) Updating.*',
            r'\(\d+/\d+\) Arming.*'
        ]
    
    def should_handle_command(self, command: str) -> bool:
        """Check if this command should be handled by pacman handler"""
        pacman_commands = [
            'sudo pacman -Syu', 'pacman -Syu',
            'sudo pacman -S', 'pacman -S',
            'sudo pacman -R', 'pacman -R',
            'sudo pacman -U', 'pacman -U'
        ]
        return any(cmd in command for cmd in pacman_commands)
    
    def filter_verbose_output(self, output: str) -> str:
        """Filter out verbose pacman output, keep only essential info"""
        lines = output.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Check if line matches verbose patterns
            is_verbose = False
            for pattern in self.verbose_patterns:
                if re.match(pattern, line.strip()):
                    is_verbose = True
                    break
            
            if not is_verbose:
                # Keep important lines
                if any(keyword in line for keyword in [
                    'Packages (', 'Total Installed Size:', 'Net Upgrade Size:',
                    'Total Download Size:', ':: Proceed with', 'warning:',
                    '[sudo] password', 'error:', 'failed', 'conflict'
                ]):
                    filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def parse_package_info(self, output: str) -> Optional[Dict]:
        """Parse package information from pacman output"""
        lines = output.split('\n')
        
        packages = []
        total_size = None
        net_size = None
        download_size = None
        
        for line in lines:
            # Extract package list
            if line.startswith('Packages ('):
                # Extract package names from the line
                match = re.search(r'Packages \((\d+)\)(.*)', line)
                if match:
                    count = match.group(1)
                    package_line = match.group(2).strip()
                    # Split by spaces and filter out empty strings
                    package_parts = [p.strip() for p in package_line.split() if p.strip()]
                    packages = package_parts
            
            # Extract sizes
            elif 'Total Installed Size:' in line:
                match = re.search(r'Total Installed Size:\s*(.+)', line)
                if match:
                    total_size = match.group(1).strip()
            
            elif 'Net Upgrade Size:' in line:
                match = re.search(r'Net Upgrade Size:\s*(.+)', line)
                if match:
                    net_size = match.group(1).strip()
            
            elif 'Total Download Size:' in line:
                match = re.search(r'Total Download Size:\s*(.+)', line)
                if match:
                    download_size = match.group(1).strip()
        
        if packages or total_size:
            return {
                'packages': packages,
                'total_size': total_size,
                'net_size': net_size,
                'download_size': download_size
            }
        
        return None
    
    def execute_pacman_command(self, command: str) -> Dict:
        """Execute pacman command with intelligent output processing"""
        try:
            # Start the process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_buffer = ""
            
            while True:
                # Read output line by line
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    output_buffer += line
                    
                    # Check for password prompt
                    if '[sudo] password' in line:
                        print(f"\033[1;33m[WavesAI]\033[0m ➜ Please enter your sudo password:")
                        # Let user enter password directly
                        continue
                    
                    # Check for installation prompt
                    if ':: Proceed with installation? [Y/n]' in line:
                        # Parse package information from buffer
                        package_info = self.parse_package_info(output_buffer)
                        
                        if package_info and package_info['packages']:
                            package_count = len(package_info['packages'])
                            package_list = ', '.join(package_info['packages'][:3])  # Show first 3
                            if package_count > 3:
                                package_list += f" and {package_count - 3} more"
                            
                            size_info = ""
                            if package_info['total_size']:
                                size_info += f"Total Size: {package_info['total_size']}"
                            if package_info['net_size']:
                                size_info += f", Net Change: {package_info['net_size']}"
                            
                            print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Would you like to proceed with installation of {package_count} packages?")
                            print(f"  Packages: {package_list}")
                            if size_info:
                                print(f"  {size_info}")
                            
                            user_choice = input("  Proceed? [Y/n]: ").strip().lower()
                            
                            # Send response to pacman
                            if user_choice in ['', 'y', 'yes']:
                                process.stdin.write('y\n')
                            else:
                                process.stdin.write('n\n')
                            process.stdin.flush()
                        else:
                            # Fallback to original prompt
                            user_choice = input(":: Proceed with installation? [Y/n] ").strip()
                            process.stdin.write(f'{user_choice}\n')
                            process.stdin.flush()
            
            # Wait for process to complete
            process.wait()
            
            return {
                "success": process.returncode == 0,
                "output": "Package operation completed" if process.returncode == 0 else "Package operation failed",
                "error": "" if process.returncode == 0 else f"Command failed with exit code {process.returncode}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Error executing pacman command: {str(e)}"
            }
