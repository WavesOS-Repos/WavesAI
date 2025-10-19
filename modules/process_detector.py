#!/usr/bin/env python3
"""
Smart Process Detector - Intelligent process name matching
Handles common app name variations and aliases
"""

import subprocess
import re
from typing import List, Dict, Optional

class ProcessDetector:
    def __init__(self):
        # Common app name mappings
        self.app_aliases = {
            # Code Editors
            'windsurf': ['windsurf', 'windsurf-bin', 'windsurf.exe', 'com.codeium.windsurf'],
            'cursor': ['cursor', 'cursor-bin', 'cursor.exe', 'com.todesktop.230313mzl4w4u92'],
            'vscode': ['code', 'code-oss', 'visual-studio-code', 'com.visualstudio.code'],
            'sublime': ['sublime_text', 'subl', 'sublime-text'],
            'atom': ['atom', 'atom-beta'],
            
            # Browsers
            'chrome': ['chrome', 'chromium', 'google-chrome', 'chromium-browser', 'chrome-browser'],
            'firefox': ['firefox', 'firefox-esr', 'firefox-bin', 'mozilla-firefox'],
            'edge': ['microsoft-edge', 'msedge', 'edge'],
            'brave': ['brave', 'brave-browser', 'brave-bin'],
            'opera': ['opera', 'opera-stable', 'opera-beta'],
            
            # Communication
            'discord': ['discord', 'Discord', 'com.discordapp.Discord'],
            'slack': ['slack', 'Slack', 'com.slack.Slack'],
            'teams': ['teams', 'microsoft-teams', 'com.microsoft.Teams'],
            'zoom': ['zoom', 'ZoomLauncher', 'com.zoom.xos'],
            'telegram': ['telegram', 'telegram-desktop', 'Telegram'],
            'whatsapp': ['whatsapp', 'whatsapp-desktop', 'WhatsApp'],
            
            # Media
            'vlc': ['vlc', 'vlc-bin', 'org.videolan.VLC'],
            'spotify': ['spotify', 'Spotify', 'com.spotify.Client'],
            'obs': ['obs', 'obs-studio', 'com.obsproject.Studio'],
            'gimp': ['gimp', 'gimp-2.10', 'org.gimp.GIMP'],
            'blender': ['blender', 'blender-bin', 'org.blender.Blender'],
            
            # Development
            'docker': ['docker', 'dockerd', 'docker-desktop', 'com.docker.docker'],
            'postman': ['postman', 'Postman', 'com.getpostman.Postman'],
            'insomnia': ['insomnia', 'Insomnia', 'com.insomnia.app'],
            
            # System
            'terminal': ['gnome-terminal', 'konsole', 'xterm', 'kitty', 'alacritty', 'terminator'],
            'filemanager': ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'nemo'],
            'calculator': ['gnome-calculator', 'kcalc', 'galculator', 'qalculate'],
            
            # Games
            'steam': ['steam', 'steam-runtime', 'com.valvesoftware.Steam'],
            'minecraft': ['minecraft', 'minecraft-launcher', 'com.mojang.minecraftlauncher'],
            
            # Office
            'libreoffice': ['libreoffice', 'soffice.bin', 'org.libreoffice.LibreOffice'],
            'writer': ['libreoffice --writer', 'soffice.bin --writer'],
            'calc': ['libreoffice --calc', 'soffice.bin --calc'],
            'impress': ['libreoffice --impress', 'soffice.bin --impress'],
            
            # Note-taking
            'obsidian': ['obsidian', 'Obsidian', 'md.obsidian.Obsidian'],
            'notion': ['notion', 'Notion', 'notion-app'],
            'joplin': ['joplin', 'Joplin', '@joplinapp-desktop'],
            
            # Others
            'thunderbird': ['thunderbird', 'thunderbird-bin', 'org.mozilla.Thunderbird'],
            'keepass': ['keepassxc', 'keepass', 'org.keepassxc.KeePassXC'],
        }
    
    def get_all_processes(self) -> List[Dict]:
        """Get all running processes with detailed info"""
        try:
            # Use ps aux to get detailed process info
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = []
            
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split(None, 10)  # Split into max 11 parts
                    if len(parts) >= 11:
                        processes.append({
                            'user': parts[0],
                            'pid': parts[1],
                            'cpu': parts[2],
                            'mem': parts[3],
                            'command': parts[10],
                            'name': parts[10].split()[0] if parts[10] else ''
                        })
            
            return processes
        except Exception:
            return []
    
    def find_process_by_name(self, app_name: str) -> List[Dict]:
        """Find processes matching the app name using smart detection"""
        app_name = app_name.lower().strip()
        processes = self.get_all_processes()
        matches = []
        
        # Get possible process names for this app
        possible_names = self.app_aliases.get(app_name, [app_name])
        
        for process in processes:
            command_lower = process['command'].lower()
            process_name = process['name'].lower()
            
            # Check direct matches
            for possible_name in possible_names:
                possible_name = possible_name.lower()
                
                # Exact match in process name
                if possible_name == process_name:
                    matches.append(process)
                    continue
                
                # Partial match in process name
                if possible_name in process_name:
                    matches.append(process)
                    continue
                
                # Match in full command line
                if possible_name in command_lower:
                    matches.append(process)
                    continue
                
                # Fuzzy matching for similar names
                if self._fuzzy_match(possible_name, process_name):
                    matches.append(process)
                    continue
                
                if self._fuzzy_match(possible_name, command_lower):
                    matches.append(process)
                    continue
        
        # Remove duplicates based on PID
        seen_pids = set()
        unique_matches = []
        for match in matches:
            if match['pid'] not in seen_pids:
                seen_pids.add(match['pid'])
                unique_matches.append(match)
        
        return unique_matches
    
    def _fuzzy_match(self, target: str, text: str) -> bool:
        """Fuzzy matching for process names"""
        # Remove common suffixes/prefixes
        suffixes = ['-bin', '-desktop', '.exe', '-browser', '-app']
        prefixes = ['com.', 'org.', 'md.', '@']
        
        clean_text = text
        for suffix in suffixes:
            clean_text = clean_text.replace(suffix, '')
        for prefix in prefixes:
            clean_text = clean_text.replace(prefix, '')
        
        # Check if target is contained in cleaned text
        if target in clean_text:
            return True
        
        # Check if cleaned text is contained in target
        if clean_text in target:
            return True
        
        # Check for partial matches (at least 70% similarity)
        if len(target) >= 3 and len(clean_text) >= 3:
            common_chars = sum(1 for a, b in zip(target, clean_text) if a == b)
            similarity = common_chars / max(len(target), len(clean_text))
            return similarity >= 0.7
        
        return False
    
    def kill_process_smart(self, app_name: str) -> Dict:
        """Smart process killing with detailed feedback"""
        matches = self.find_process_by_name(app_name)
        
        if not matches:
            # Try alternative search patterns
            alternative_matches = self._search_alternative_patterns(app_name)
            if alternative_matches:
                matches = alternative_matches
            else:
                return {
                    'success': False,
                    'message': f"No running processes found for '{app_name}'. Try 'ps aux | grep {app_name}' to see all processes.",
                    'matches': []
                }
        
        if len(matches) == 1:
            # Single match - kill it
            process = matches[0]
            try:
                subprocess.run(['kill', process['pid']], check=True)
                return {
                    'success': True,
                    'message': f"Killed {app_name} (PID: {process['pid']}, Command: {process['name']})",
                    'matches': matches
                }
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(['kill', '-9', process['pid']], check=True)
                    return {
                        'success': True,
                        'message': f"Force killed {app_name} (PID: {process['pid']}, Command: {process['name']})",
                        'matches': matches
                    }
                except subprocess.CalledProcessError:
                    return {
                        'success': False,
                        'message': f"Failed to kill {app_name} (PID: {process['pid']}). Permission denied or process not found.",
                        'matches': matches
                    }
        
        else:
            # Multiple matches - kill all instances
            killed = []
            failed = []
            
            for process in matches:
                try:
                    subprocess.run(['kill', process['pid']], check=True)
                    killed.append(process)
                except subprocess.CalledProcessError:
                    try:
                        subprocess.run(['kill', '-9', process['pid']], check=True)
                        killed.append(process)
                    except subprocess.CalledProcessError:
                        failed.append(process)
            
            if killed and not failed:
                return {
                    'success': True,
                    'message': f"Killed {len(killed)} {app_name} processes: {', '.join([p['pid'] for p in killed])}",
                    'matches': matches
                }
            elif killed and failed:
                return {
                    'success': True,
                    'message': f"Killed {len(killed)} {app_name} processes, failed to kill {len(failed)} processes",
                    'matches': matches
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to kill any {app_name} processes. Permission denied or processes not found.",
                    'matches': matches
                }
    
    def _search_alternative_patterns(self, app_name: str) -> List[Dict]:
        """Search for processes using alternative patterns"""
        processes = self.get_all_processes()
        matches = []
        
        for process in processes:
            command_lower = process['command'].lower()
            
            # Search for app name anywhere in the command
            if app_name.lower() in command_lower:
                matches.append(process)
        
        return matches
    
    def list_processes_for_app(self, app_name: str) -> List[Dict]:
        """List all processes related to an app"""
        return self.find_process_by_name(app_name)
