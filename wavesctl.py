#!/usr/bin/env python3
"""
WavesAI CLI - Quick command interface
Usage: wavesctl <command> [args]
"""

import sys
import os
import argparse
from pathlib import Path

# Add WavesAI directory to path
wavesai_dir = Path.home() / ".wavesai"
sys.path.insert(0, str(wavesai_dir))

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

def main():
    parser = argparse.ArgumentParser(description='WavesAI CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
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
    
    if not args.command:
        parser.print_help()
        return
    
    cli = WavesAICLI()
    
    # Execute command
    if hasattr(cli, f'cmd_{args.command}'):
        getattr(cli, f'cmd_{args.command}')(args)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()
