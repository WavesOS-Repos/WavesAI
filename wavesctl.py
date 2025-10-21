#!/usr/bin/env python3
"""
WavesAI CLI - Complete command interface
Usage: wavesctl <command> [args]

This script automatically activates the virtual environment and provides
both quick CLI commands and interactive mode access.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add WavesAI directory to path
wavesai_dir = Path.home() / ".wavesai"
venv_dir = wavesai_dir / "venv"
sys.path.insert(0, str(wavesai_dir))

# Activate virtual environment if not already activated
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    # Not in a virtual environment, activate it
    activate_script = venv_dir / "bin" / "activate_this.py"
    if activate_script.exists():
        exec(open(activate_script).read(), {'__file__': str(activate_script)})
    else:
        # Fallback: modify sys.path to use venv packages
        site_packages = venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        if site_packages.exists():
            sys.path.insert(0, str(site_packages))

from modules.system_monitor import SystemMonitor
from modules.command_handler import CommandHandler
from modules.search_engine import SearchEngine
from modules.process_detector import ProcessDetector
from modules.location_weather import LocationWeatherService

class WavesAICLI:
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.command_handler = CommandHandler()
        self.search_engine = SearchEngine()
        self.process_detector = ProcessDetector()
        self.location_weather = LocationWeatherService()
        
        # Set user's actual location for CLI tool
        try:
            from user_location import setup_user_location
            setup_user_location(self.location_weather)
        except ImportError:
            pass
    
    def cmd_status(self, args):
        """Show system status"""
        stats = self.system_monitor.get_system_context()
        
        print("\n╔═══════════════════════════════════════════╗")
        print("║         WavesAI System Status             ║")
        print("╚═══════════════════════════════════════════╝\n")
        
        print(f"User: {stats['username']}@{stats['hostname']}")
        print(f"CPU: {stats['cpu_usage']} | Temp: {stats['cpu_temp']}")
        print(f"RAM: {stats['ram_usage']}")
        print(f"GPU: {stats['gpu_info']}")
        print(f"Uptime: {stats['uptime']}")
        print(f"Time: {stats['current_time']}")
        print(f"{stats.get('location', 'Location: Unknown')}")
        print()
    
    def cmd_top(self, args):
        """Show top processes"""
        processes = self.process_detector.get_all_processes()[:20]
        
        print(f"\nTop 20 Processes:\n")
        print(f"{'PID':<8} {'NAME':<30} {'CPU%':<8} {'MEM%':<8} {'USER':<12}")
        print("="*70)
        
        for proc in processes:
            print(f"{proc['pid']:<8} {proc['name'][:30]:<30} {proc['cpu']:<8} {proc['mem']:<8} {proc['user']:<12}")
        print()
    
    def cmd_kill(self, args):
        """Kill a process by name"""
        if not args.process:
            print("Error: Please provide a process name")
            return
        
        result = self.process_detector.kill_process_smart(args.process)
        print(f"\n{result['message']}\n")
    
    def cmd_find(self, args):
        """Find processes by name"""
        if not args.process:
            print("Error: Please provide a process name")
            return
        
        matches = self.process_detector.find_process_by_name(args.process)
        if matches:
            print(f"\nFound {len(matches)} processes for '{args.process}':")
            for match in matches:
                print(f"  • {match['name']} (PID: {match['pid']}, CPU: {match['cpu']}%, RAM: {match['mem']}%)")
        else:
            print(f"\nNo processes found for '{args.process}'")
        print()
    
    def cmd_search(self, args):
        """Search web or Wikipedia"""
        if not args.query:
            print("Error: Please provide a search query")
            return
        
        query = ' '.join(args.query)
        if hasattr(args, 'wikipedia') and args.wikipedia:
            result = self.search_engine.search_wikipedia(query)
        else:
            result = self.search_engine.search_web(query)
        
        print(f"\nSearch Results:\n{result}\n")
    
    def cmd_news(self, args):
        """Get latest news"""
        region = args.region if hasattr(args, 'region') else 'world'
        query = ' '.join(args.query) if hasattr(args, 'query') and args.query else 'latest news'
        
        result = self.search_engine.search_news(query, region)
        print(f"\nLatest News:\n{result}\n")
    
    def cmd_weather(self, args):
        """Get weather information"""
        location = ' '.join(args.location) if hasattr(args, 'location') and args.location else None
        
        result = self.location_weather.get_weather_summary(location)
        print(f"\n{result}\n")
    
    def cmd_location(self, args):
        """Get current location information"""
        # Check if refresh is requested
        if hasattr(args, 'refresh') and args.refresh:
            print("🔄 Refreshing location...")
            location_data = self.location_weather.refresh_location()
        else:
            location_data = self.location_weather.get_location()
        
        if location_data.get('error'):
            print(f"\nLocation Error: {location_data['error']}\n")
        else:
            print(f"\n📍 Current Location Information:")
            print(f"City: {location_data.get('city', 'Unknown')}")
            print(f"Region: {location_data.get('region', 'Unknown')}")
            print(f"Country: {location_data.get('country', 'Unknown')}")
            print(f"Timezone: {location_data.get('timezone', 'Unknown')}")
            print(f"ISP: {location_data.get('isp', 'Unknown')}")
            print(f"Coordinates: {location_data.get('lat', 0):.4f}, {location_data.get('lon', 0):.4f}")
            
            # Show detection method
            if location_data.get('manual'):
                print(f"Detection: Manual Override")
            else:
                print(f"Detection: Automatic IP-based")
            print()
    
    def cmd_start(self, args):
        """Start WavesAI interactive mode"""
        wavesai_script = wavesai_dir / "wavesai.py"
        
        if not wavesai_script.exists():
            print("❌ Error: wavesai.py not found")
            print(f"Expected location: {wavesai_script}")
            return
        
        # Run wavesai.py using the venv python
        venv_python = venv_dir / "bin" / "python"
        if venv_python.exists():
            os.execv(str(venv_python), [str(venv_python), str(wavesai_script)])
        else:
            # Fallback to system python
            os.execv(sys.executable, [sys.executable, str(wavesai_script)])
    
    def cmd_run(self, args):
        """Alias for start command"""
        self.cmd_start(args)
    
    def cmd_version(self, args):
        """Show version information"""
        print("\n\033[0;35m╔══════════════════════════════════════════════════════════╗\033[0m")
        print("\033[0;35m║              WavesAI Version 3.1                         ║\033[0m")
        print("\033[0;35m╚══════════════════════════════════════════════════════════╝\033[0m")
        print("\n🤖 JARVIS-like AI Assistant for Linux")
        print(f"📁 Installation: {wavesai_dir}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📦 Virtual Environment: {venv_dir}")
        print("\n✨ Features:")
        print("  • JARVIS-like conversational AI")
        print("  • System monitoring and control")
        print("  • 170+ advanced system commands")
        print("  • Intelligent error handling")
        print("  • Dangerous operation protection")
        print("  • Sudo password management")
        print()
    
    def cmd_config(self, args):
        """Edit configuration file"""
        config_file = wavesai_dir / "config" / "config.json"
        
        if not config_file.exists():
            print("⚠️  Configuration file not found. Creating default...")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text('{}')
        
        # Try to open with user's preferred editor
        editor = os.environ.get('EDITOR', 'nano')
        try:
            subprocess.run([editor, str(config_file)])
        except Exception as e:
            print(f"❌ Error opening editor: {e}")
            print(f"📁 Config file location: {config_file}")
    
    def cmd_logs(self, args):
        """View WavesAI logs"""
        log_file = wavesai_dir / "config" / "logs" / "wavesai.log"
        
        if not log_file.exists():
            print("⚠️  No logs found")
            print(f"📁 Log file will be created at: {log_file}")
            return
        
        # Tail the log file
        try:
            subprocess.run(['tail', '-f', str(log_file)])
        except KeyboardInterrupt:
            print("\n✓ Stopped viewing logs")
        except Exception as e:
            print(f"❌ Error viewing logs: {e}")
            print(f"📁 Log file location: {log_file}")

def main():
    parser = argparse.ArgumentParser(
        description='WavesAI CLI Tool - JARVIS-like AI Assistant',
        epilog='Examples:\n'
               '  wavesctl start              # Start interactive mode\n'
               '  wavesctl status             # Show system status\n'
               '  wavesctl top                # Show top processes\n'
               '  wavesctl weather Mumbai     # Get weather\n'
               '  wavesctl search "AI"        # Search web\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command (default)
    start_parser = subparsers.add_parser('start', help='Start WavesAI interactive mode (default)')
    
    # Run command (alias for start)
    run_parser = subparsers.add_parser('run', help='Start WavesAI interactive mode (alias for start)')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Edit configuration file')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View WavesAI logs')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Top command
    top_parser = subparsers.add_parser('top', help='Show top processes')
    
    # Kill command
    kill_parser = subparsers.add_parser('kill', help='Kill a process by name')
    kill_parser.add_argument('process', help='Process name to kill')
    
    # Find command
    find_parser = subparsers.add_parser('find', help='Find processes by name')
    find_parser.add_argument('process', help='Process name to find')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search web or Wikipedia')
    search_parser.add_argument('query', nargs='+', help='Search query')
    search_parser.add_argument('-w', '--wikipedia', action='store_true', help='Search Wikipedia instead of web')
    
    # News command
    news_parser = subparsers.add_parser('news', help='Get latest news')
    news_parser.add_argument('query', nargs='*', help='News query (optional)')
    news_parser.add_argument('-r', '--region', default='world', help='News region (world, usa, uk, india, etc.)')
    
    # Weather command
    weather_parser = subparsers.add_parser('weather', help='Get weather information')
    weather_parser.add_argument('location', nargs='*', help='Location (optional, uses current location if not specified)')
    
    # Location command
    location_parser = subparsers.add_parser('location', help='Get current location information')
    location_parser.add_argument('-r', '--refresh', action='store_true', help='Force refresh location detection')
    
    args = parser.parse_args()
    
    # Default to 'start' if no command provided
    if not args.command:
        args.command = 'start'
    
    cli = WavesAICLI()
    
    # Execute command
    if hasattr(cli, f'cmd_{args.command}'):
        getattr(cli, f'cmd_{args.command}')(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()
