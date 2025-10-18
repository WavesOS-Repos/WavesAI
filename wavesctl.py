#!/usr/bin/env python3
"""
WavesAI CLI - Quick command interface
Usage: wavesctl <command> [args]
"""

import sys
import argparse
from pathlib import Path

# Import modules
sys.path.insert(0, str(Path.home() / ".local/share/wavesai"))
from modules import *

class WavesAICLI:
    def __init__(self):
        self.system = SystemModule()
        self.package = PackageModule()
        self.process = ProcessModule()
        self.service = ServiceModule()
        self.network = NetworkModule()
        self.file = FileModule()
        self.dev = DevelopmentModule()
        self.media = MediaModule()
        self.automation = AutomationModule()
    
    def cmd_status(self, args):
        """Show system status"""
        stats = self.system.get_detailed_stats()
        
        print("\n╔═══════════════════════════════════════════╗")
        print("║         WavesAI System Status             ║")
        print("╚═══════════════════════════════════════════╝\n")
        
        # CPU
        cpu_avg = sum(stats['cpu']['percent']) / len(stats['cpu']['percent'])
        print(f"CPU: {cpu_avg:.1f}% | Cores: {stats['cpu']['count']}")
        
        # Memory
        mem = stats['memory']['virtual']
        print(f"RAM: {mem['percent']:.1f}% ({mem['used']/(1024**3):.1f}GB / {mem['total']/(1024**3):.1f}GB)")
        
        # Disk
        for disk in stats['disk']:
            usage = disk['usage']
            print(f"Disk {disk['mountpoint']}: {usage['percent']:.1f}% ({usage['used']/(1024**3):.1f}GB / {usage['total']/(1024**3):.1f}GB)")
        
        # Processes
        print(f"Processes: {stats['processes']}")
        
        # Temperature
        temps = self.system.get_temperature()
        if temps:
            for sensor, readings in temps.items():
                for reading in readings[:1]:  # First reading only
                    print(f"Temperature ({sensor}): {reading['current']:.1f}°C")
        
        print()
    
    def cmd_top(self, args):
        """Show top processes"""
        sort_by = args.sort if hasattr(args, 'sort') else 'cpu'
        processes = self.process.list_processes(sort_by)
        
        print(f"\nTop 20 Processes (by {sort_by}):\n")
        print(f"{'PID':<8} {'NAME':<30} {'CPU%':<8} {'MEM%':<8} {'STATUS':<12}")
        print("="*70)
        
        for proc in processes:
            print(f"{proc['pid']:<8} {proc['name'][:30]:<30} {proc['cpu_percent']:<8.1f} {proc['memory_percent']:<8.1f} {proc['status']:<12}")
        print()
    
    def cmd_services(self, args):
        """List systemd services"""
        state = args.state if hasattr(args, 'state') else 'all'
        output = self.service.list_services(state)
        print(output)
    
    def cmd_network(self, args):
        """Show network information"""
        info = self.network.get_network_info()
        
        print("\n╔═══════════════════════════════════════════╗")
        print("║         Network Information               ║")
        print("╚═══════════════════════════════════════════╝\n")
        
        # Interfaces
        for iface, addrs in info['interfaces'].items():
            print(f"Interface: {iface}")
            for addr in addrs:
                if addr['family'].name == 'AF_INET':
                    print(f"  IPv4: {addr['address']}")
                elif addr['family'].name == 'AF_INET6':
                    print(f"  IPv6: {addr['address'][:30]}")
            print()
        
        # Public IP
        public_ip = self.network.get_public_ip()
        print(f"Public IP: {public_ip}\n")
        
        # IO Stats
        io = info['io_counters']
        print(f"Sent: {io['bytes_sent']/(1024**2):.2f} MB")
        print(f"Received: {io['bytes_recv']/(1024**2):.2f} MB\n")
    
    def cmd_search(self, args):
        """Search for files"""
        if not args.pattern:
            print("Error: Please provide a search pattern")
            return
        
        directory = args.directory if hasattr(args, 'directory') else '.'
        results = self.file.search_files(args.pattern, directory)
        
        print(f"\nSearching for: {args.pattern}\n")
        for result in results:
            if result:
                print(result)
        print()
    
    def cmd_package(self, args):
        """Package management"""
        if args.action == 'search':
            output = self.package.search_package(args.name)
            print(output)
        elif args.action == 'install':
            print(f"Installing {args.name}...")
            result = self.package.install_package(args.name, args.yay)
            print(result.stdout if result.returncode == 0 else result.stderr)
        elif args.action == 'remove':
            print(f"Removing {args.name}...")
            result = self.package.remove_package(args.name)
            print(result.stdout if result.returncode == 0 else result.stderr)
        elif args.action == 'update':
            print("Updating system...")
            result = self.package.update_system()
            print(result.stdout if result.returncode == 0 else result.stderr)
        elif args.action == 'clean':
            print("Cleaning cache...")
            results = self.package.clean_cache()
            for result in results:
                print(result.stdout)
    
    def cmd_git(self, args):
        """Git operations"""
        if args.action == 'status':
            output = self.dev.git_status(args.path if hasattr(args, 'path') else '.')
            print(output)
        elif args.action == 'commit':
            if not hasattr(args, 'message'):
                print("Error: Commit message required")
                return
            output = self.dev.git_commit(args.path if hasattr(args, 'path') else '.', args.message)
            print(output)
        elif args.action == 'push':
            output = self.dev.git_push(args.path if hasattr(args, 'path') else '.')
            print(output)
    
    def cmd_brightness(self, args):
        """Control screen brightness"""
        if args.action == 'get':
            level = self.media.get_brightness()
            print(f"Current brightness: {level}")
        elif args.action == 'set':
            if not hasattr(args, 'level'):
                print("Error: Brightness level required (0-100)")
                return
            success = self.media.set_brightness(args.level)
            print(f"Brightness set to {args.level}%" if success else "Failed to set brightness")
    
    def cmd_kill(self, args):
        """Kill a process"""
        if not args.pid:
            print("Error: PID required")
            return
        
        success = self.process.kill_process(args.pid, args.force)
        print(f"Process {args.pid} killed" if success else f"Failed to kill process {args.pid}")

def main():
    parser = argparse.ArgumentParser(
        description='WavesAI CLI - Quick system control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wavesctl status              Show system status
  wavesctl top                 Show top processes
  wavesctl top --sort memory   Sort by memory usage
  wavesctl services --state failed   Show failed services
  wavesctl network             Show network info
  wavesctl search myfile       Search for files
  wavesctl package search vim  Search for package
  wavesctl package install vim Install package
  wavesctl git status          Show git status
  wavesctl brightness get      Get brightness level
  wavesctl kill 1234           Kill process by PID
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status
    subparsers.add_parser('status', help='Show system status')
    
    # Top
    top_parser = subparsers.add_parser('top', help='Show top processes')
    top_parser.add_argument('--sort', choices=['cpu', 'memory'], default='cpu')
    
    # Services
    services_parser = subparsers.add_parser('services', help='List systemd services')
    services_parser.add_argument('--state', choices=['all', 'active', 'failed'], default='all')
    
    # Network
    subparsers.add_parser('network', help='Show network information')
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search for files')
    search_parser.add_argument('pattern', help='Search pattern')
    search_parser.add_argument('--directory', '-d', default='.', help='Directory to search in')
    
    # Package
    package_parser = subparsers.add_parser('package', help='Package management')
    package_parser.add_argument('action', choices=['search', 'install', 'remove', 'update', 'clean'])
    package_parser.add_argument('name', nargs='?', help='Package name')
    package_parser.add_argument('--yay', action='store_true', help='Use yay instead of pacman')
    
    # Git
    git_parser = subparsers.add_parser('git', help='Git operations')
    git_parser.add_argument('action', choices=['status', 'commit', 'push'])
    git_parser.add_argument('--path', '-p', default='.', help='Repository path')
    git_parser.add_argument('--message', '-m', help='Commit message')
    
    # Brightness
    brightness_parser = subparsers.add_parser('brightness', help='Control brightness')
    brightness_parser.add_argument('action', choices=['get', 'set'])
    brightness_parser.add_argument('level', nargs='?', type=int, help='Brightness level (0-100)')
    
    # Kill
    kill_parser = subparsers.add_parser('kill', help='Kill a process')
    kill_parser.add_argument('pid', type=int, help='Process ID')
    kill_parser.add_argument('--force', '-f', action='store_true', help='Force kill')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = WavesAICLI()
    
    # Execute command
    command_map = {
        'status': cli.cmd_status,
        'top': cli.cmd_top,
        'services': cli.cmd_services,
        'network': cli.cmd_network,
        'search': cli.cmd_search,
        'package': cli.cmd_package,
        'git': cli.cmd_git,
        'brightness': cli.cmd_brightness,
        'kill': cli.cmd_kill
    }
    
    if args.command in command_map:
        try:
            command_map[args.command](args)
        except Exception as e:
            print(f"Error: {e}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
