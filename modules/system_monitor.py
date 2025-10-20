#!/usr/bin/env python3
"""
WavesAI System Monitor Module
Handles system monitoring, stats, and process management
"""

import os
import psutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from .location_weather import LocationWeatherService


class SystemMonitor:
    """Handles all system monitoring operations"""
    
    def __init__(self):
        self.location_weather = LocationWeatherService()
        # Set user's actual location
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from user_location import setup_user_location
            setup_user_location(self.location_weather)
        except ImportError:
            pass  # Use IP geolocation if user_location.py doesn't exist
    
    def get_system_context(self) -> Dict:
        """Gather comprehensive system information for AI context"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            # Get GPU info (NVIDIA)
            gpu_info = "N/A"
            try:
                nvidia_smi = subprocess.check_output(
                    ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu', 
                     '--format=csv,noheader,nounits'],
                    encoding='utf-8'
                ).strip().split(',')
                gpu_info = f"GPU: {nvidia_smi[0]}% | VRAM: {nvidia_smi[1]}/{nvidia_smi[2]}MB | Temp: {nvidia_smi[3]}°C"
            except:
                pass
            
            # Get CPU temperature
            cpu_temp = "N/A"
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    cpu_temp = f"{temps['coretemp'][0].current}°C"
            except:
                pass
            
            # Get process count and top processes
            process_count = len(psutil.pids())
            top_processes = self.get_top_processes(5)
            
            # Get network stats
            network_stats = self.get_network_stats()
            
            # Get system load
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            # Get location information
            location_summary = self.location_weather.get_location_summary()
            
            return {
                "username": os.getenv("USER"),
                "hostname": os.uname().nodename,
                "cpu_usage": f"{cpu_percent}%",
                "cpu_temp": cpu_temp,
                "ram_usage": f"{memory.percent}% ({memory.used // (1024**3)}GB/{memory.total // (1024**3)}GB)",
                "disk_usage": f"{disk.percent}% ({disk.used // (1024**3)}GB/{disk.total // (1024**3)}GB)",
                "gpu_info": gpu_info,
                "uptime": str(uptime).split('.')[0],
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "distro": "Arch Linux",
                "process_count": process_count,
                "top_processes": top_processes,
                "network_stats": network_stats,
                "load_avg": f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}",
                "location": location_summary
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_top_processes(self, count: int = 10) -> List[Dict]:
        """Get top processes by CPU and memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent'],
                        'memory_mb': proc.info['memory_info'].rss / (1024 * 1024),
                        'status': proc.info['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:count]
        except Exception as e:
            return []
    
    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "active_connections": net_connections
            }
        except Exception as e:
            return {"error": str(e)}
    
    def monitor_process(self, process_name: str = None, pid: int = None) -> Dict:
        """Monitor a specific process"""
        try:
            if pid:
                proc = psutil.Process(pid)
            elif process_name:
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == process_name.lower():
                        proc = psutil.Process(proc.info['pid'])
                        break
                else:
                    return {"error": f"Process '{process_name}' not found"}
            else:
                return {"error": "Either process_name or pid must be specified"}
            
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "memory_mb": proc.memory_info().rss / (1024 * 1024),
                "status": proc.status(),
                "create_time": datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "num_threads": proc.num_threads(),
                "connections": len(proc.connections()) if proc.connections() else 0
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            return {"error": str(e)}
    
    def get_system_alerts(self) -> List[str]:
        """Check for system alerts and warnings"""
        alerts = []
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                alerts.append(f"⚠️  High CPU usage: {cpu_percent}%")
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                alerts.append(f"⚠️  High memory usage: {memory.percent}%")
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                alerts.append(f"⚠️  High disk usage: {disk.percent}%")
            
            # Check temperature
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    cpu_temp = temps['coretemp'][0].current
                    if cpu_temp > 80:
                        alerts.append(f"🌡️  High CPU temperature: {cpu_temp}°C")
            except:
                pass
            
            # Check for zombie processes
            zombie_count = 0
            for proc in psutil.process_iter(['status']):
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    zombie_count += 1
            
            if zombie_count > 0:
                alerts.append(f"🧟 Found {zombie_count} zombie processes")
            
            return alerts
        except Exception as e:
            return [f"Error checking alerts: {str(e)}"]
    
    def get_detailed_system_info(self) -> str:
        """Get detailed system information for monitoring"""
        try:
            system_info = self.get_system_context()
            alerts = self.get_system_alerts()
            
            info_parts = []
            info_parts.append("🔍 **SYSTEM MONITORING REPORT**")
            info_parts.append(f"🖥️  **Host:** {system_info['hostname']}")
            info_parts.append(f"👤 **User:** {system_info['username']}")
            info_parts.append(f"⏰ **Time:** {system_info['current_time']}")
            info_parts.append(f"🔄 **Uptime:** {system_info['uptime']}")
            info_parts.append("")
            
            info_parts.append("📊 **PERFORMANCE METRICS:**")
            info_parts.append(f"🔧 **CPU:** {system_info['cpu_usage']} | {system_info['cpu_temp']}")
            info_parts.append(f"🧠 **RAM:** {system_info['ram_usage']}")
            info_parts.append(f"💾 **Disk:** {system_info['disk_usage']}")
            info_parts.append(f"🎮 **{system_info['gpu_info']}**")
            info_parts.append(f"📈 **Load Avg:** {system_info['load_avg']}")
            info_parts.append("")
            
            if alerts:
                info_parts.append("⚠️  **ALERTS:**")
                for alert in alerts:
                    info_parts.append(alert)
                info_parts.append("")
            
            # Top processes
            if system_info.get('top_processes'):
                info_parts.append("🔝 **TOP PROCESSES:**")
                for proc in system_info['top_processes'][:5]:
                    info_parts.append(f"  • {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']}% | RAM: {proc['memory_mb']:.1f}MB")
            
            return "\n".join(info_parts)
        except Exception as e:
            return f"Error generating system report: {str(e)}"
