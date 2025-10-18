#!/usr/bin/env python3
"""
WavesAI System Modules
Modular functionality for different system operations
"""

import os
import subprocess
import psutil
import json
import requests
from datetime import datetime
from pathlib import Path

class SystemModule:
    """Core system operations"""
    
    @staticmethod
    def get_detailed_stats():
        """Get comprehensive system statistics"""
        stats = {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1, percpu=True),
                "freq": psutil.cpu_freq(),
                "count": psutil.cpu_count(),
                "load_avg": os.getloadavg()
            },
            "memory": {
                "virtual": psutil.virtual_memory()._asdict(),
                "swap": psutil.swap_memory()._asdict()
            },
            "disk": [],
            "network": psutil.net_io_counters()._asdict(),
            "processes": len(psutil.pids())
        }
        
        # Disk info for all partitions
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                stats["disk"].append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "usage": usage._asdict()
                })
            except:
                pass
        
        return stats
    
    @staticmethod
    def system_control(action: str):
        """System power operations"""
        commands = {
            "shutdown": "systemctl poweroff",
            "reboot": "systemctl reboot",
            "suspend": "systemctl suspend",
            "hibernate": "systemctl hibernate",
            "logout": "loginctl terminate-user $USER",
            "lock": "loginctl lock-session"
        }
        
        if action in commands:
            return subprocess.run(commands[action], shell=True, capture_output=True, text=True)
        return None
    
    @staticmethod
    def get_temperature():
        """Get system temperatures"""
        temps = {}
        try:
            sensors = psutil.sensors_temperatures()
            for name, entries in sensors.items():
                temps[name] = [{"label": e.label, "current": e.current, "high": e.high} for e in entries]
        except:
            pass
        return temps

class PackageModule:
    """Package management for Arch Linux"""
    
    @staticmethod
    def search_package(query: str):
        """Search for packages"""
        result = subprocess.run(f"pacman -Ss {query}", shell=True, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def install_package(package: str, use_yay: bool = False):
        """Install package"""
        cmd = f"yay -S {package}" if use_yay else f"sudo pacman -S {package}"
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    @staticmethod
    def remove_package(package: str):
        """Remove package"""
        return subprocess.run(f"sudo pacman -R {package}", shell=True, capture_output=True, text=True)
    
    @staticmethod
    def update_system():
        """Update system packages"""
        return subprocess.run("sudo pacman -Syu", shell=True, capture_output=True, text=True)
    
    @staticmethod
    def clean_cache():
        """Clean package cache"""
        commands = [
            "sudo pacman -Sc --noconfirm",
            "yay -Sc --noconfirm",
            "sudo pacman -Rns $(pacman -Qtdq) --noconfirm"  # Remove orphans
        ]
        results = []
        for cmd in commands:
            results.append(subprocess.run(cmd, shell=True, capture_output=True, text=True))
        return results
    
    @staticmethod
    def get_arch_news():
        """Fetch latest Arch Linux news"""
        try:
            response = requests.get("https://archlinux.org/feeds/news/", timeout=5)
            # Parse RSS feed (simplified)
            return response.text[:1000]  # Return first 1000 chars
        except:
            return "Unable to fetch Arch news"

class ProcessModule:
    """Process management"""
    
    @staticmethod
    def list_processes(sort_by: str = "cpu"):
        """List all processes sorted by CPU or memory"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except:
                pass
        
        if sort_by == "cpu":
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        
        return processes[:20]  # Return top 20
    
    @staticmethod
    def kill_process(pid: int, force: bool = False):
        """Kill a process by PID"""
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()
            return True
        except:
            return False
    
    @staticmethod
    def find_process(name: str):
        """Find processes by name"""
        matching = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if name.lower() in proc.info['name'].lower():
                    matching.append(proc.info)
            except:
                pass
        return matching

class ServiceModule:
    """Systemd service management"""
    
    @staticmethod
    def list_services(state: str = "all"):
        """List systemd services"""
        cmd = "systemctl list-units --type=service"
        if state == "active":
            cmd += " --state=active"
        elif state == "failed":
            cmd += " --state=failed"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def service_action(service: str, action: str):
        """Control systemd service"""
        actions = ["start", "stop", "restart", "enable", "disable", "status"]
        if action in actions:
            cmd = f"sudo systemctl {action} {service}"
            return subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return None
    
    @staticmethod
    def get_service_status(service: str):
        """Get detailed service status"""
        result = subprocess.run(f"systemctl status {service}", shell=True, capture_output=True, text=True)
        return result.stdout

class NetworkModule:
    """Network operations"""
    
    @staticmethod
    def get_network_info():
        """Get network information"""
        info = {
            "interfaces": {},
            "connections": psutil.net_connections(),
            "io_counters": psutil.net_io_counters()._asdict()
        }
        
        # Get interface addresses
        for iface, addrs in psutil.net_if_addrs().items():
            info["interfaces"][iface] = [addr._asdict() for addr in addrs]
        
        return info
    
    @staticmethod
    def ping(host: str, count: int = 4):
        """Ping a host"""
        result = subprocess.run(f"ping -c {count} {host}", shell=True, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def get_public_ip():
        """Get public IP address"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            return "Unable to fetch public IP"
    
    @staticmethod
    def speedtest():
        """Run network speed test"""
        try:
            result = subprocess.run("speedtest-cli --simple", shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout
        except:
            return "Speedtest not available or timed out"

class FileModule:
    """File operations"""
    
    @staticmethod
    def search_files(pattern: str, directory: str = ".", depth: int = 3):
        """Search for files"""
        result = subprocess.run(
            f"find {directory} -maxdepth {depth} -iname '*{pattern}*'",
            shell=True, capture_output=True, text=True, timeout=10
        )
        return result.stdout.split('\n')[:50]  # Limit to 50 results
    
    @staticmethod
    def get_disk_usage(path: str = "/"):
        """Get disk usage for path"""
        result = subprocess.run(f"du -sh {path}/*", shell=True, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def archive_files(source: str, output: str, format: str = "tar.gz"):
        """Create archive"""
        if format == "tar.gz":
            cmd = f"tar -czf {output} {source}"
        elif format == "zip":
            cmd = f"zip -r {output} {source}"
        else:
            return None
        
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    @staticmethod
    def extract_archive(archive: str, destination: str = "."):
        """Extract archive"""
        if archive.endswith('.tar.gz') or archive.endswith('.tgz'):
            cmd = f"tar -xzf {archive} -C {destination}"
        elif archive.endswith('.zip'):
            cmd = f"unzip {archive} -d {destination}"
        elif archive.endswith('.tar.xz'):
            cmd = f"tar -xJf {archive} -C {destination}"
        else:
            return None
        
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)

class DevelopmentModule:
    """Development tools"""
    
    @staticmethod
    def git_status(repo_path: str = "."):
        """Get git repository status"""
        result = subprocess.run(f"git -C {repo_path} status", shell=True, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def git_commit(repo_path: str, message: str):
        """Commit changes"""
        result = subprocess.run(
            f"git -C {repo_path} add . && git -C {repo_path} commit -m '{message}'",
            shell=True, capture_output=True, text=True
        )
        return result.stdout
    
    @staticmethod
    def git_push(repo_path: str = "."):
        """Push to remote"""
        result = subprocess.run(f"git -C {repo_path} push", shell=True, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def run_build(project_path: str, build_cmd: str = "make"):
        """Run build command"""
        result = subprocess.run(
            f"cd {project_path} && {build_cmd}",
            shell=True, capture_output=True, text=True, timeout=300
        )
        return result.stdout

class MediaModule:
    """Media and UI operations"""
    
    @staticmethod
    def set_wallpaper(image_path: str):
        """Set wallpaper (Hyprland)"""
        # For Hyprland
        result = subprocess.run(
            f"hyprctl hyprpaper preload {image_path} && hyprctl hyprpaper wallpaper ,{image_path}",
            shell=True, capture_output=True, text=True
        )
        return result.returncode == 0
    
    @staticmethod
    def get_brightness():
        """Get screen brightness"""
        result = subprocess.run("brightnessctl g", shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    
    @staticmethod
    def set_brightness(level: int):
        """Set screen brightness (0-100)"""
        result = subprocess.run(f"brightnessctl s {level}%", shell=True, capture_output=True, text=True)
        return result.returncode == 0
    
    @staticmethod
    def control_rgb(mode: str = "static", color: str = "ffffff"):
        """Control RGB lighting via OpenRGB"""
        result = subprocess.run(
            f"openrgb --mode {mode} --color {color}",
            shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

class AutomationModule:
    """Task automation"""
    
    @staticmethod
    def create_cron_job(schedule: str, command: str):
        """Create a cron job"""
        cron_line = f"{schedule} {command}\n"
        result = subprocess.run(
            f"(crontab -l 2>/dev/null; echo '{cron_line}') | crontab -",
            shell=True, capture_output=True, text=True
        )
        return result.returncode == 0
    
    @staticmethod
    def list_cron_jobs():
        """List all cron jobs"""
        result = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def run_at_time(time: str, command: str):
        """Schedule one-time command"""
        result = subprocess.run(
            f"echo '{command}' | at {time}",
            shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

# Export all modules
__all__ = [
    'SystemModule',
    'PackageModule', 
    'ProcessModule',
    'ServiceModule',
    'NetworkModule',
    'FileModule',
    'DevelopmentModule',
    'MediaModule',
    'AutomationModule'
]
