#!/usr/bin/env python3
"""
WavesAI - JARVIS-like AI Assistant for Arch Linux
Optimized for Intel i5 12th Gen + RTX 3050 8GB + 16GB RAM
Fixed Version with Smart Command Handling
"""

import os
import sys
import json
import sqlite3
import subprocess
import psutil
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import time
import tempfile
import shutil
import wave
import struct
import queue
import io
from collections import deque
import re

# Audio and ML dependencies
try:
    import numpy as np
except ImportError:
    np = None

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import webrtcvad
except ImportError:
    webrtcvad = None

try:
    import whisper
except ImportError:
    whisper = None

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    torch = None
    CUDA_AVAILABLE = False

try:
    import noisereduce as nr
except ImportError:
    nr = None

# Import WavesAI modules
from modules.search_engine import SearchEngine
from modules.system_monitor import SystemMonitor
from modules.command_handler import CommandHandler

# Configuration - Load from config file
def load_config():
    config_path = Path.home() / ".wavesai/config/config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                cfg = json.load(f)
                return {
                    "model_path": os.path.expanduser(cfg['model']['path']),
                    "database": os.path.expanduser(cfg['paths']['database']),
                    "log_file": os.path.expanduser(cfg['paths']['log_file']),
                    "context_length": cfg['model']['context_length'],
                    "gpu_layers": cfg['model']['gpu_layers'],
                    "threads": cfg['model']['threads'],
                    "temperature": cfg['generation']['temperature'],
                    "max_tokens": cfg['generation']['max_tokens']
                }
        except:
            pass
    
    # Fallback to defaults
    return {
        "model_path": str(Path.home() / ".wavesai/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        "database": str(Path.home() / ".wavesai/config/memory.db"),
        "log_file": str(Path.home() / ".wavesai/config/logs/wavesai.log"),
        "context_length": 4096,
        "gpu_layers": 35,
        "threads": 8,
        "temperature": 0.7,
        "max_tokens": 1024  # Increased from 512 for longer, complete responses
    }

CONFIG = load_config()

class WavesAI:
    def __init__(self):
        self.setup_directories()
        self.init_database()
        self.llm = None
        self.conversation_history = []
        self.sudo_password = None  # Store sudo password temporarily
        self.pending_dangerous_command = None  # Store dangerous command awaiting confirmation
        self.confirmation_code = None  # Store current confirmation code
        
        # Initialize modules
        self.search_engine = SearchEngine()
        self.system_monitor = SystemMonitor()
        self.command_handler = CommandHandler()
        
        self.system_context = self.system_monitor.get_system_context()
        self.system_prompt_template = self.load_system_prompt()
        
        # Define dangerous command patterns
        self.dangerous_patterns = [
            'rm -rf', 'mkfs', 'dd if=', 'shred', 'wipe', 
            'fdisk', 'parted', 'lvremove', 'vgremove',
            'mdadm --zero-superblock', 'iptables -F',
            'systemctl isolate', 'reboot', 'shutdown', 
            'poweroff', 'halt'
        ]
    
    def get_system_context(self):
        """Wrapper for system_monitor.get_system_context()"""
        return self.system_monitor.get_system_context()
    
    def get_system_alerts(self):
        """Wrapper for system_monitor.get_system_alerts()"""
        return self.system_monitor.get_system_alerts()
    
    def get_top_processes(self, count: int = 10):
        """Wrapper for system_monitor.get_top_processes()"""
        return self.system_monitor.get_top_processes(count)
    
    def get_network_stats(self):
        """Wrapper for system_monitor.get_network_stats()"""
        return self.system_monitor.get_network_stats()
    
    def monitor_process(self, process_name: str = None, pid: int = None):
        """Wrapper for system_monitor.monitor_process()"""
        return self.system_monitor.monitor_process(process_name, pid)
    
    def get_detailed_system_info(self):
        """Wrapper for system_monitor.get_detailed_system_info()"""
        return self.system_monitor.get_detailed_system_info()
    
    def search_wikipedia(self, query: str) -> str:
        """Wrapper for search_engine.search_wikipedia()"""
        return self.search_engine.search_wikipedia(query)
    
    def search_web(self, query: str) -> str:
        """Wrapper for search_engine.search_web()"""
        return self.search_engine.search_web(query)
    
    def search_news(self, query: str = "latest news", region: str = "india") -> str:
        """Wrapper for search_engine.search_news()"""
        return self.search_engine.search_news(query, region)
    
    def _detect_news_region(self, user_input: str) -> str:
        """Detect news region from user input - globally aware"""
        user_input_lower = user_input.lower()
        
        # Check for specific countries/regions mentioned
        country_keywords = {
            'usa': ['usa', 'america', 'american', 'united states', 'us news'],
            'uk': ['uk', 'britain', 'british', 'england', 'united kingdom'],
            'canada': ['canada', 'canadian'],
            'australia': ['australia', 'australian'],
            'germany': ['germany', 'german'],
            'france': ['france', 'french'],
            'italy': ['italy', 'italian'],
            'spain': ['spain', 'spanish'],
            'russia': ['russia', 'russian'],
            'china': ['china', 'chinese'],
            'japan': ['japan', 'japanese'],
            'south korea': ['korea', 'korean', 'south korea'],
            'india': ['india', 'indian'],
            'brazil': ['brazil', 'brazilian'],
            'mexico': ['mexico', 'mexican'],
            'argentina': ['argentina', 'argentinian'],
            'south africa': ['south africa', 'south african'],
            'egypt': ['egypt', 'egyptian'],
            'nigeria': ['nigeria', 'nigerian'],
            'thailand': ['thailand', 'thai'],
            'singapore': ['singapore', 'singaporean'],
            'malaysia': ['malaysia', 'malaysian'],
            'indonesia': ['indonesia', 'indonesian'],
            'philippines': ['philippines', 'filipino'],
            'vietnam': ['vietnam', 'vietnamese'],
            'turkey': ['turkey', 'turkish'],
            'israel': ['israel', 'israeli'],
            'uae': ['uae', 'emirates', 'dubai'],
            'saudi arabia': ['saudi', 'saudi arabia']
        }
        
        # Check for country-specific keywords
        for country, keywords in country_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return country
        
        # Check for regional keywords
        if any(keyword in user_input_lower for keyword in ['world', 'global', 'international']):
            return 'world'
        
        if any(keyword in user_input_lower for keyword in ['local', 'here', 'my area', 'current location']):
            # Try to get user's location for local news
            try:
                location_data = self.system_monitor.location_weather.get_location()
                if not location_data.get('error'):
                    return location_data.get('country', 'world')
            except:
                pass
            return 'local'
        
        # Default to world news for global audience
        return 'world'
    
    def smart_execute(self, user_input: str):
        """Wrapper for command_handler.smart_execute()"""
        return self.command_handler.smart_execute(user_input, self.system_context)
    
    def is_safe_command(self, command: str) -> bool:
        """Wrapper for command_handler.is_safe_command()"""
        return self.command_handler.is_safe_command(command)
    
    def execute_command(self, command: str, sudo: bool = False, timeout: int = 30):
        """Wrapper for command_handler.execute_command()"""
        return self.command_handler.execute_command(command, sudo, timeout)
        
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            Path.home() / ".wavesai/config",
            Path.home() / ".wavesai/config/logs",
            Path.home() / ".wavesai/modules"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def load_system_prompt(self) -> str:
        """Load system prompt from external file"""
        prompt_path = Path.home() / ".wavesai/system_prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[Warning] System prompt file not found at {prompt_path}")
            return "You are WavesAI, an AI assistant for Arch Linux."
    
    def init_database(self):
        """Initialize SQLite database for persistent memory"""
        db_path = Path(CONFIG["database"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(CONFIG["database"])
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                context TEXT,
                user_input TEXT,
                ai_response TEXT,
                executed_command TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT
            )
        """)
        
        self.conn.commit()
    
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
                "load_avg": f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
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
        """Check for system alerts and warnings with proactive suggestions"""
        alerts = []
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:
                alerts.append(f"Sir, CPU usage is critically high at {cpu_percent}%. Would you like me to identify the process?")
            elif cpu_percent > 85:
                alerts.append(f"CPU usage is elevated at {cpu_percent}%")
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                alerts.append(f"Sir, memory usage is at {memory.percent}%. Consider closing some applications.")
            elif memory.percent > 80:
                alerts.append(f"Memory usage is high at {memory.percent}%")
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                alerts.append(f"Sir, disk space is critically low ({disk.percent}% used). Shall I clean up temporary files?")
            elif disk.percent > 85:
                alerts.append(f"Disk space is running low ({disk.percent}% used)")
            
            # Check temperature
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    cpu_temp = temps['coretemp'][0].current
                    if cpu_temp > 90:
                        alerts.append(f"Sir, CPU temperature is critically high at {cpu_temp}°C. Consider checking cooling.")
                    elif cpu_temp > 80:
                        alerts.append(f"CPU temperature is elevated at {cpu_temp}°C")
            except:
                pass
            
            # Check for zombie processes
            zombie_count = 0
            for proc in psutil.process_iter(['status']):
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    zombie_count += 1
            
            if zombie_count > 5:
                alerts.append(f"Sir, found {zombie_count} zombie processes. Would you like me to clean them up?")
            elif zombie_count > 0:
                alerts.append(f"Found {zombie_count} zombie process(es)")
            
            # Check for high swap usage
            swap = psutil.swap_memory()
            if swap.percent > 80:
                alerts.append(f"Swap usage is high at {swap.percent}%. System may be slow.")
            
            return alerts
        except Exception as e:
            return [f"Error checking alerts: {str(e)}"]
    
    def init_voice_components(self):
        """Initialize voice assistant components"""
        # Get custom threshold from environment or use defaults based on testing
        # Your mic shows avg 560, max 12069, so we need higher threshold
        energy_threshold = int(os.getenv('WAVESAI_ENERGY_THRESHOLD', '1200'))
        
        self.voice_config = {
            'sample_rate': 44100,  # Your device's native rate
            'channels': 1,
            'chunk_size': 2048,  # Larger chunks for 44100 Hz
            'format': pyaudio.paInt16 if pyaudio else None,
            'vad_mode': 3,  # Most aggressive VAD
            'silence_threshold': 0.8,  # seconds of silence to stop recording
            'energy_threshold': energy_threshold,  # Higher threshold for your mic
            'silence_energy_ratio': 0.3,  # Silence is 30% of speech energy  
            'min_speech_duration': 0.3,  # Minimum speech duration in seconds
            'max_recording_duration': 20,  # Maximum recording duration
            'pre_recording_buffer': 0.3,  # seconds to keep before speech
            'whisper_model': os.getenv('WAVESAI_WHISPER_MODEL', 'base.en'),
            'piper_model': os.getenv('WAVESAI_PIPER_MODEL'),
            'tts_speed': float(os.getenv('WAVESAI_TTS_SPEED', '1.0')),
            'enable_noise_reduction': os.getenv('WAVESAI_NOISE_REDUCTION', 'false').lower() == 'true',
            'debug_audio': os.getenv('WAVESAI_DEBUG_AUDIO', 'false').lower() == 'true',
            'use_dynamic_threshold': os.getenv('WAVESAI_DYNAMIC_THRESHOLD', 'false').lower() == 'true'
        }
        
        # Audio processing queues
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.is_speaking = False
        self.stop_listening = False
        
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
            
            info_parts.append(f"⚙️  **PROCESSES:** {system_info['process_count']} total")
            if system_info.get('top_processes'):
                info_parts.append("🔥 **Top CPU Consumers:**")
                for i, proc in enumerate(system_info['top_processes'][:3], 1):
                    info_parts.append(f"   {i}. {proc['name']} (PID: {proc['pid']}) - {proc['cpu_percent']:.1f}% CPU, {proc['memory_mb']:.1f}MB RAM")
            info_parts.append("")
            
            if system_info.get('network_stats'):
                net = system_info['network_stats']
                info_parts.append(f"🌐 **NETWORK:** {net['active_connections']} connections")
                info_parts.append(f"   📤 Sent: {net['bytes_sent'] // (1024*1024)}MB | 📥 Received: {net['bytes_recv'] // (1024*1024)}MB")
            info_parts.append("")
            
            if alerts:
                info_parts.append("🚨 **ALERTS:**")
                for alert in alerts:
                    info_parts.append(f"   {alert}")
            else:
                info_parts.append("✅ **System Status:** All systems normal")
            
            return "\n".join(info_parts)
            
        except Exception as e:
            return f"Error generating system report: {str(e)}"
    
    def apply_noise_reduction(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply noise reduction to audio data"""
        if nr is None or not self.voice_config.get('enable_noise_reduction'):
            return audio_data
        try:
            # Apply noise reduction
            reduced = nr.reduce_noise(y=audio_data, sr=sample_rate, stationary=True)
            return reduced
        except Exception:
            return audio_data
    
    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to prevent clipping"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data * (0.95 / max_val)
        return audio_data
    
    def tts_speak_advanced(self, text: str, interrupt_check=None):
        """Advanced TTS with interruption support"""
        # Clean text for TTS
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # Remove markdown
        text = re.sub(r'```[^`]*```', '', text)  # Remove code blocks
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Convert links
        text = text.strip()
        
        if not text:
            return
            
        model = self.voice_config.get('piper_model')
        speed = self.voice_config.get('tts_speed', 1.0)
        
        # Try Piper first (best quality)
        if model and shutil.which("piper"):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                out = tmp.name
            try:
                # Generate speech
                cmd = ["piper", "--model", model, "--output_file", out]
                if speed != 1.0:
                    cmd.extend(["--length_scale", str(1.0/speed)])
                
                subprocess.run(cmd + ["--text", text], check=True, capture_output=True)
                
                # Play with interruption support
                self.is_speaking = True
                if shutil.which("aplay"):
                    proc = subprocess.Popen(["aplay", "-q", out])
                    while proc.poll() is None:
                        if interrupt_check and interrupt_check():
                            proc.terminate()
                            break
                        time.sleep(0.05)
                elif shutil.which("ffplay"):
                    proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", out])
                    while proc.poll() is None:
                        if interrupt_check and interrupt_check():
                            proc.terminate()
                            break
                        time.sleep(0.05)
                self.is_speaking = False
            except Exception as e:
                self.is_speaking = False
                print(f"[TTS Error] {e}")
            finally:
                try:
                    os.unlink(out)
                except Exception:
                    pass
            return
            
        # Fallback to espeak-ng
        elif shutil.which("espeak-ng"):
            self.is_speaking = True
            try:
                speed_param = str(int(175 * speed))  # Default espeak speed is 175
                proc = subprocess.Popen(["espeak-ng", "-s", speed_param, text])
                while proc.poll() is None:
                    if interrupt_check and interrupt_check():
                        proc.terminate()
                        break
                    time.sleep(0.05)
            except Exception:
                pass
            self.is_speaking = False
            return
            
        # Last resort: print
        print(f"\n\033[1;35m[WavesAI]\033[0m ➜ {text}")
    
    def voice_mode(self):
        """New voice mode using sounddevice like the working prototype"""
        try:
            import sounddevice as sd
            import numpy as np
            from scipy.io import wavfile
            import tempfile
            import time
            from faster_whisper import WhisperModel
        except ImportError as e:
            print(f"\033[1;31m[Error]\033[0m Missing dependencies: {e}")
            print("\033[1;33m[Install]\033[0m pip install sounddevice faster-whisper")
            return
        
        # Load LLM if not already loaded
        if not self.llm:
            print("\033[1;33m[Loading]\033[0m Loading AI model...")
            if not self.load_llm():
                print("\033[1;31m[Error]\033[0m Failed to load AI model. Voice mode cannot continue.")
                return
        
        config = {
            'sample_rate': 16000,  # Start with 16kHz like your prototype
            'channels': 1,
            'vad_threshold': 0.015,  # From your prototype
            'silence_duration': 1.5,
            'min_recording_duration': 0.5,
            'whisper_model': 'base'
        }
        
        # Smart device detection (from your prototype)
        def find_best_device():
            """Find the best working microphone - exact logic from your prototype"""
            print("\033[1;36m[🔍 Device Detection]\033[0m Scanning all audio devices...\n")
            
            devices = sd.query_devices()
            candidates = []
            
            # Score all input devices (your exact scoring logic)
            for idx, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name'].lower()
                    score = 0
                    
                    # Positive indicators (from your prototype)
                    microphone_keywords = ['mic', 'microphone', 'webcam', 'camera', 'usb', 'input', 'capture']
                    for keyword in microphone_keywords:
                        if keyword in name:
                            score += 20
                    
                    # Prefer USB devices
                    if 'usb' in name:
                        score += 15
                    
                    # Prefer webcam mics
                    if 'webcam' in name or 'camera' in name:
                        score += 25
                    
                    # Negative indicators
                    bad_keywords = ['monitor', 'hdmi', 'displayport', 'output', 'speaker', 'headphone', 'sink']
                    for keyword in bad_keywords:
                        if keyword in name:
                            score -= 50
                    
                    # Check channels
                    channels = device.get('max_input_channels', 0)
                    if 1 <= channels <= 2:
                        score += 10
                    elif channels > 8:
                        score -= 10
                    
                    if score > 0:
                        candidates.append((idx, device, score))
                        print(f"  \033[1;32m[Device {idx}]\033[0m {device['name'][:50]} (Score: {score}, Channels: {channels})")
            
            if not candidates:
                print("\033[1;31m[Error]\033[0m No input devices found!")
                return None, None
            
            # Sort by score
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            print("\n\033[1;36m[Testing Devices]\033[0m In order of preference...\n")
            
            # Test each device (your exact test logic)
            sample_rates = [16000, 44100, 48000, 22050, 32000, 8000]
            
            for idx, device, score in candidates:
                device_name = device['name']
                print(f"  Testing: {device_name[:50]}...", end='')
                
                for rate in sample_rates:
                    try:
                        # Test recording
                        test_duration = 0.1
                        recording = sd.rec(
                            int(test_duration * rate),
                            samplerate=rate,
                            channels=1,
                            device=idx,
                            dtype='float32'
                        )
                        sd.wait()
                        
                        # Check if we got real audio
                        if recording is not None and len(recording) > 0:
                            rms = np.sqrt(np.mean(recording**2))
                            if not (np.isnan(rms) or rms == 0.0):
                                print(f" \033[1;32m✓\033[0m")
                                print(f"\n\033[1;32m[✓ Selected Device]\033[0m")
                                print(f"  Name: {device_name}")
                                print(f"  Index: {idx}")
                                print(f"  Sample Rate: {rate} Hz")
                                print(f"  Channels: {device['max_input_channels']}")
                                print(f"  Score: {score}\n")
                                return idx, rate
                    except:
                        continue
                print(f" \033[1;31m✗\033[0m")
            
            return None, None
        
        # Find best device
        device_index, sample_rate = find_best_device()
        if device_index is None:
            print("\033[1;31m[Failed]\033[0m Could not find working microphone")
            return
        
        config['sample_rate'] = sample_rate
        
        # Load Whisper model
        print("\033[1;33m[Loading]\033[0m Whisper model...", end='')
        try:
            if CUDA_AVAILABLE:
                whisper_model = WhisperModel(config['whisper_model'], device="cuda", compute_type="float16")
                print(" \033[1;32m✓ (CUDA)\033[0m")
            else:
                whisper_model = WhisperModel(config['whisper_model'], device="cpu", compute_type="int8")
                print(" \033[1;32m✓ (CPU)\033[0m")
        except:
            print(" \033[1;31m✗\033[0m")
            return
        
        # Voice activity detection (from your prototype)
        class VoiceActivityDetector:
            def __init__(self):
                self.noise_floor = None
                self.calibration_samples = []
                self.is_calibrated = False
                
            def calibrate(self, audio_chunk):
                if len(self.calibration_samples) < 10:
                    rms = np.sqrt(np.mean(audio_chunk.flatten()**2))
                    if not np.isnan(rms):
                        self.calibration_samples.append(rms)
                elif not self.is_calibrated:
                    self.noise_floor = np.mean(self.calibration_samples) * 1.5
                    self.is_calibrated = True
                    print(f"\033[1;32m[Calibrated]\033[0m Noise floor: {self.noise_floor:.4f}")
            
            def is_voice_detected(self, audio_chunk):
                rms = np.sqrt(np.mean(audio_chunk.flatten()**2))
                threshold = self.noise_floor if self.is_calibrated else config['vad_threshold']
                return rms > threshold and not np.isnan(rms), rms
        
        # Setup audio stream
        audio_queue = queue.Queue()
        vad = VoiceActivityDetector()
        self.stop_listening = False
        
        def audio_callback(indata, frames, time_info, status):
            if not vad.is_calibrated:
                vad.calibrate(indata)
            audio_queue.put(indata.copy())
        
        # Start stream
        print("\033[1;36m[Starting Audio]\033[0m Opening stream...")
        stream = sd.InputStream(
            device=device_index,
            samplerate=sample_rate,
            channels=config['channels'],
            callback=audio_callback,
            blocksize=int(sample_rate * 0.1)
        )
        stream.start()
        
        # Calibration
        print("\033[1;36m[Calibrating]\033[0m Adjusting to ambient noise...")
        time.sleep(1.5)
        
        print("\033[1;32m[Ready]\033[0m Voice assistant active! Say 'exit' to quit.\n")
        
        # Main loop (exact logic from your prototype)
        try:
            while not self.stop_listening:
                print("\033[1;32m[👂 Listening]\033[0m", end='', flush=True)
                
                recording_buffer = []
                is_recording = False
                silence_start = None
                recording_start = None
                
                # Wait for speech
                while not self.stop_listening:
                    try:
                        audio_chunk = audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    
                    voice_detected, energy = vad.is_voice_detected(audio_chunk)
                    
                    if voice_detected and not is_recording:
                        print(f"\n\033[1;33m[🎤 Recording]\033[0m Energy: {energy:.4f}", end='', flush=True)
                        is_recording = True
                        recording_start = time.time()
                        recording_buffer = []
                        silence_start = None
                    
                    if is_recording:
                        recording_buffer.append(audio_chunk)
                        
                        if not voice_detected:
                            if silence_start is None:
                                silence_start = time.time()
                            elif time.time() - silence_start >= config['silence_duration']:
                                if time.time() - recording_start >= config['min_recording_duration']:
                                    print(f"\n\033[1;32m[✓ Complete]\033[0m {time.time()-recording_start:.1f}s")
                                    break
                        else:
                            silence_start = None
                            print(".", end='', flush=True)
                
                if not recording_buffer or self.stop_listening:
                    continue
                
                # Save and transcribe
                audio_data = np.concatenate(recording_buffer, axis=0)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    # Normalize
                    max_val = np.max(np.abs(audio_data))
                    if max_val > 0:
                        audio_normalized = audio_data / max_val
                    else:
                        audio_normalized = audio_data
                    
                    audio_int16 = np.int16(audio_normalized * 32767)
                    
                    with wave.open(tmp_file.name, 'wb') as wf:
                        wf.setnchannels(config['channels'])
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(audio_int16.tobytes())
                    
                    tmp_path = tmp_file.name
                
                # Transcribe
                print("\033[1;36m[Transcribing]\033[0m", end='', flush=True)
                try:
                    segments, _ = whisper_model.transcribe(
                        tmp_path,
                        beam_size=5,
                        language="en",
                        vad_filter=True,
                        condition_on_previous_text=False
                    )
                    
                    text = " ".join([s.text for s in segments]).strip()
                    os.unlink(tmp_path)
                    
                    if text:
                        print(" ✓")
                        print(f"\n\033[1;36m[You]\033[0m {text}")
                        
                        # Check for exit
                        if text.lower() in ['exit', 'quit', 'goodbye', 'bye', 'stop']:
                            print("\033[1;35m[WavesAI]\033[0m Goodbye!")
                            self.stop_listening = True
                            break
                        
                        # Process with AI
                        response = self.generate_response(text)
                        print(f"\033[1;35m[WavesAI]\033[0m {response}")
                        
                        # TTS if available
                        if hasattr(self, 'tts_speak_advanced'):
                            self.tts_speak_advanced(response[:500])
                    else:
                        print(" (no speech)")
                        
                except Exception as e:
                    print(f" ✗ {e}")
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                
        except KeyboardInterrupt:
            print("\n\033[1;33m[Interrupted]\033[0m")
        finally:
            stream.stop()
            stream.close()
            print("\033[1;35m[WavesAI]\033[0m Voice mode terminated.")
    
    def voice_mode_old(self):
        """Enhanced voice mode with professional features"""
        # Suppress ALSA warnings
        import os
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
        
        # Redirect ALSA errors to /dev/null
        try:
            import ctypes
            ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, 
                                                  ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
            def py_error_handler(filename, line, function, err, fmt):
                pass
            c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
            try:
                asound = ctypes.cdll.LoadLibrary('libasound.so.2')
                asound.snd_lib_error_set_handler(c_error_handler)
            except:
                pass
        except:
            pass
        
        # Check dependencies
        if pyaudio is None or np is None:
            print("\033[1;31m[Error]\033[0m PyAudio and numpy required. Install: pip install pyaudio numpy")
            return
        if whisper is None:
            print("\033[1;31m[Error]\033[0m Whisper required. Install: pip install openai-whisper")
            return
            
        # Initialize components
        self.init_voice_components()
        
        if not self.load_llm():
            return
            
        # Start background services
        self.start_monitoring_thread()
        
        # Custom voice startup
        print("\n" + "="*60)
        print("\033[1;36m         WAVESAI VOICE ASSISTANT ACTIVATED\033[0m")
        print("="*60)
        
        # Load Whisper model
        print(f"\n\033[1;33m[Initializing]\033[0m Loading Whisper model: {self.voice_config['whisper_model']}...")
        try:
            device = "cuda" if CUDA_AVAILABLE else "cpu"
            self.whisper_model = whisper.load_model(
                self.voice_config['whisper_model'],
                device=device
            )
            print(f"\033[1;32m[Ready]\033[0m Whisper loaded on {device.upper()}")
        except Exception as e:
            print(f"\033[1;31m[Error]\033[0m Failed to load Whisper: {e}")
            return
            
        # Initialize PyAudio with error suppression
        import warnings
        warnings.filterwarnings("ignore")
        self.pa = pyaudio.PyAudio()
        
        # Initialize VAD
        self.vad = None
        if webrtcvad is not None:
            try:
                self.vad = webrtcvad.Vad(self.voice_config['vad_mode'])
                print(f"\033[1;32m[Ready]\033[0m WebRTC VAD initialized (mode {self.voice_config['vad_mode']})")
            except Exception:
                print("\033[1;33m[Warning]\033[0m WebRTC VAD unavailable, using energy-based detection")
                
        # Audio processing state - IMPORTANT: Initialize recording state to False
        self.audio_buffer = deque(maxlen=int(self.voice_config['sample_rate'] * 10))  # 10 seconds max
        self.pre_buffer = deque(maxlen=int(self.voice_config['sample_rate'] * self.voice_config['pre_recording_buffer']))
        self.is_recording = False  # MUST be False initially
        self.silence_frames = 0
        self.speech_frames = []
        self.speech_energy_max = 0  # Track max energy during speech
        self.ambient_noise_level = []  # Track ambient noise for dynamic threshold
        self.recording_start_time = None  # Track when recording started
        
        # Welcome message
        print("\n\033[1;35m[WavesAI]\033[0m Voice mode active. Speak naturally, I'm listening...")
        print(f"\033[1;33m[Settings]\033[0m Initial energy threshold: {self.voice_config['energy_threshold']}")
        print(f"\033[1;33m[Info]\033[0m Dynamic threshold enabled - will adjust to your environment")
        print(f"\033[1;33m[Debug]\033[0m Run with WAVESAI_DEBUG_AUDIO=true to see real-time audio levels\n")
        self.tts_speak_advanced("Voice assistant ready. How may I assist you today?")
        
        def process_audio_frame(frame_data: bytes) -> tuple:
            """Process a single audio frame and return True if speech detected"""
            # Convert to numpy
            audio_np = np.frombuffer(frame_data, dtype=np.int16).astype(np.float32)
            
            # Calculate energy
            energy = np.sqrt(np.mean(audio_np ** 2))
            
            # For VAD, we need exactly 10, 20, or 30ms of audio at supported rates
            # Calculate the required frame size for VAD
            vad_frame_duration_ms = 30  # Use 30ms frames for VAD
            vad_frame_size = int(self.voice_config['sample_rate'] * vad_frame_duration_ms / 1000) * 2  # *2 for int16
            
            is_speech = False
            
            # Since we're using 44100 Hz, VAD won't work - use energy-based detection only
            # VAD only supports 8000, 16000, 32000, 48000 Hz
            is_speech = energy > self.voice_config['energy_threshold']
            
            # Optional: Add a minimum energy to avoid noise
            if is_speech and energy < 100:  # Ignore very quiet sounds
                is_speech = False
                
            return is_speech, energy
            
        def transcribe_audio(audio_data: np.ndarray) -> str:
            """Transcribe audio using Whisper"""
            try:
                # Ensure we have enough audio (at least 0.5 seconds)
                min_samples = int(self.voice_config['sample_rate'] * 0.5)
                if len(audio_data) < min_samples:
                    print(f"\033[1;33m[Warning]\033[0m Audio too short: {len(audio_data)} samples")
                    return ""
                
                # Apply noise reduction
                if self.voice_config.get('enable_noise_reduction'):
                    audio_data = self.apply_noise_reduction(audio_data, self.voice_config['sample_rate'])
                    
                # Normalize audio to prevent clipping
                audio_data = self.normalize_audio(audio_data)
                
                # Ensure audio is float32 in range [-1, 1]
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                
                # Pad audio if needed (Whisper prefers at least 1 second)
                if len(audio_data) < self.voice_config['sample_rate']:
                    padding = self.voice_config['sample_rate'] - len(audio_data)
                    audio_data = np.pad(audio_data, (0, padding), mode='constant')
                
                # Transcribe with optimized parameters
                result = self.whisper_model.transcribe(
                    audio_data,
                    language='en',
                    temperature=0.2,  # Slightly higher for better recognition
                    no_speech_threshold=0.4,  # Lower threshold to catch more speech
                    logprob_threshold=-1.0,
                    compression_ratio_threshold=2.4,
                    condition_on_previous_text=False,  # Faster without context
                    fp16=CUDA_AVAILABLE  # Use FP16 on GPU to save memory
                )
                
                text = result['text'].strip()
                
                # Filter out common noise transcriptions (single words that are often mistakes)
                noise_patterns = ['you', 'yeah', 'yes', 'no', 'oh', 'um', 'uh', 'thank you', 'thanks', '[Music]', '[Applause]']
                if text.lower() in noise_patterns and len(text.split()) == 1:
                    print(f"\033[1;33m[Filtered]\033[0m Noise pattern: {text}")
                    return ""
                
                # Only filter if it's too short and looks like noise
                if len(text) < 3 and not any(c.isalnum() for c in text):
                    return ""
                    
                return text
            except Exception as e:
                print(f"\033[1;31m[Transcription Error]\033[0m {e}")
                return ""
                
        def process_user_input(text: str):
            """Process transcribed text and generate response"""
            if not text:
                return
                
            print(f"\n\033[1;36m[You]\033[0m {text}")
            
            # Check for exit commands
            if text.lower() in ['exit', 'quit', 'goodbye', 'bye', 'stop']:
                self.tts_speak_advanced("Goodbye! Have a great day.")
                self.stop_listening = True
                return
                
            # Process through existing handlers
            try:
                # Check file operations
                file_response = self._handle_file_operations(text)
                if file_response:
                    self.tts_speak_advanced(file_response[:500])
                    return
                    
                # Check smart commands
                smart_response = self.smart_execute(text)
                if smart_response:
                    self.tts_speak_advanced(smart_response[:500])
                    return
                    
                # Generate AI response
                print("\033[1;33m[Processing]\033[0m Thinking...", end='\r')
                response = self.generate_response(text)
                response = self.validate_response(text, response)
                
                # Clean up the processing message
                print(" " * 50, end='\r')
                
                # Speak response (limit length for voice)
                if len(response) > 500:
                    spoken_response = response[:497] + "..."
                    print(f"\033[1;35m[WavesAI]\033[0m {response}")
                    self.tts_speak_advanced(spoken_response)
                else:
                    print(f"\033[1;35m[WavesAI]\033[0m {response}")
                    self.tts_speak_advanced(response)
                    
            except Exception as e:
                error_msg = f"I encountered an error: {str(e)[:100]}"
                print(f"\033[1;31m[Error]\033[0m {e}")
                self.tts_speak_advanced(error_msg)
                
        def audio_callback(in_data, frame_count, time_info, status):
            """PyAudio callback for continuous audio processing"""
            # Ignore status messages unless it's an error
            if status and status != 2:  # 2 is input overflow, common and harmless
                print(f"\033[1;33m[Audio Warning]\033[0m Status code: {status}")
                
            # Add to pre-buffer
            self.pre_buffer.append(in_data)
            
            # Process frame
            is_speech, energy = process_audio_frame(in_data)
            
            # Dynamic threshold adjustment - track ambient noise when not recording
            if not self.is_recording and not self.is_speaking:
                self.ambient_noise_level.append(energy)
                if len(self.ambient_noise_level) > 50:  # Keep last 50 samples
                    self.ambient_noise_level.pop(0)
                    # Adjust threshold based on ambient noise
                    if self.voice_config.get('use_dynamic_threshold'):
                        avg_noise = sum(self.ambient_noise_level) / len(self.ambient_noise_level)
                        # Set threshold to 2x ambient noise, but keep minimum of 600
                        self.voice_config['energy_threshold'] = max(600, min(1500, avg_noise * 2))
            
            # Debug mode - show energy levels
            if self.voice_config.get('debug_audio'):
                energy_bar = '█' * min(int(energy / 50), 40)
                threshold_marker = '|' if energy > self.voice_config['energy_threshold'] else ' '
                print(f"\r\033[1;34m[Energy: {energy:4.0f}/{self.voice_config['energy_threshold']:.0f}]\033[0m {threshold_marker} {energy_bar}", end='', flush=True)
            
            if not self.is_speaking:  # Don't record while speaking
                if is_speech and not self.is_recording:
                    # Start recording
                    self.is_recording = True
                    self.recording_start_time = time.time()
                    self.speech_frames = list(self.pre_buffer)[-10:]  # Include last 10 frames of pre-buffer
                    self.silence_frames = 0
                    self.speech_energy_max = energy
                    if self.voice_config.get('debug_audio'):
                        print(f"\n\033[1;32m[Speech Detected! Energy: {energy:.0f} > {self.voice_config['energy_threshold']}]\033[0m", flush=True)
                    print("\n\033[1;32m[Recording]\033[0m", end='', flush=True)
                        
                elif self.is_recording:
                    # Track max energy during speech
                    if energy > self.speech_energy_max:
                        self.speech_energy_max = energy
                    
                    # Add frame to recording
                    self.speech_frames.append(in_data)
                    
                    # Calculate recording duration
                    recording_duration = len(self.speech_frames) * (self.voice_config['chunk_size'] / self.voice_config['sample_rate'])
                    
                    # Check for maximum recording duration
                    if recording_duration >= self.voice_config.get('max_recording_duration', 30):
                        print(" \033[1;33m[Max duration reached, processing]\033[0m", flush=True)
                        self.is_recording = False
                        # Process the audio...
                        audio_bytes = b''.join(self.speech_frames)
                        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                        
                        def transcribe_and_respond():
                            text = transcribe_audio(audio_np)
                            if text:
                                process_user_input(text)
                        
                        thread = threading.Thread(target=transcribe_and_respond)
                        thread.daemon = True
                        thread.start()
                        
                        self.speech_frames = []
                        self.silence_frames = 0
                        self.speech_energy_max = 0
                        return (in_data, pyaudio.paContinue)
                    
                    # Dynamic silence threshold - use fixed ratio of initial threshold
                    silence_threshold = self.voice_config['energy_threshold'] * 0.3  # 30% of speech threshold
                    
                    if energy < silence_threshold:  # This is silence
                        self.silence_frames += 1
                        
                        # Check if we have enough speech and silence threshold reached
                        silence_duration = self.silence_frames * (self.voice_config['chunk_size'] / self.voice_config['sample_rate'])
                        
                        if recording_duration >= self.voice_config['min_speech_duration'] and silence_duration >= self.voice_config['silence_threshold']:
                            # Stop recording and process
                            print(" \033[1;33m[Processing]\033[0m", flush=True)
                            self.is_recording = False
                            
                            # Convert frames to numpy array
                            audio_bytes = b''.join(self.speech_frames)
                            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                            
                            # Transcribe in thread to not block audio
                            def transcribe_and_respond():
                                text = transcribe_audio(audio_np)
                                if text:
                                    process_user_input(text)
                                    
                            thread = threading.Thread(target=transcribe_and_respond)
                            thread.daemon = True
                            thread.start()
                            
                            # Reset
                            self.speech_frames = []
                            self.silence_frames = 0
                            self.speech_energy_max = 0
                    else:  # Still speaking
                        self.silence_frames = 0  # Reset silence counter
                        if not self.voice_config.get('debug_audio'):
                            print(".", end='', flush=True)
            return (in_data, pyaudio.paContinue)
            
        # Start audio stream with fallback sample rates
        try:
            # Try to get default input device info
            try:
                default_device = self.pa.get_default_input_device_info()
                max_sample_rate = int(default_device.get('defaultSampleRate', 16000))
                print(f"\033[1;32m[Audio]\033[0m Default device: {default_device.get('name', 'Unknown')}")
                print(f"\033[1;32m[Audio]\033[0m Max sample rate: {max_sample_rate} Hz")
            except:
                max_sample_rate = 48000
            
            # Try different sample rates - start with what the device supports
            sample_rates_to_try = [44100, 48000, 16000, 8000]
            if max_sample_rate not in sample_rates_to_try and max_sample_rate > 0:
                sample_rates_to_try.insert(0, max_sample_rate)
            
            stream = None
            actual_sample_rate = None
            
            for rate in sample_rates_to_try:
                try:
                    # Update config with working sample rate
                    self.voice_config['sample_rate'] = rate
                    # Adjust chunk size based on sample rate (aim for ~50ms chunks)
                    self.voice_config['chunk_size'] = int(rate * 0.05)  # 50ms of audio
                    
                    stream = self.pa.open(
                        format=self.voice_config['format'],
                        channels=self.voice_config['channels'],
                        rate=rate,
                        input=True,
                        frames_per_buffer=self.voice_config['chunk_size'],
                        stream_callback=audio_callback
                    )
                    actual_sample_rate = rate
                    print(f"\033[1;32m[Audio]\033[0m Using sample rate: {rate} Hz with chunk size: {self.voice_config['chunk_size']}")
                    break
                except Exception as e:
                    if rate == sample_rates_to_try[-1]:
                        raise Exception(f"Could not open audio stream with any sample rate. Last error: {e}")
                    continue
            
            if stream is None:
                raise Exception("Failed to open audio stream")
                
            stream.start_stream()
            
            # Main loop
            while stream.is_active() and not self.stop_listening:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\033[1;33m[Interrupted]\033[0m Shutting down...")
        except Exception as e:
            print(f"\n\033[1;31m[Error]\033[0m {e}")
        finally:
            # Cleanup
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            try:
                self.pa.terminate()
            except Exception:
                pass
                
            print("\n\033[1;35m[WavesAI]\033[0m Voice mode terminated. Goodbye!\n")
    
    # Removed duplicate smart_execute method - now uses command_handler.smart_execute() only
    
    def load_llm(self):
        """Load LLM model using llama-cpp-python"""
        try:
            from llama_cpp import Llama
            
            # Extract model filename from path
            model_filename = os.path.basename(CONFIG["model_path"])
            print(f"[WavesAI] Loading model: {model_filename}")
            
            # Check if model exists
            if not os.path.exists(CONFIG["model_path"]):
                print(f"[ERROR] Model not found at: {CONFIG['model_path']}")
                print("Please ensure the model file exists at the specified path.")
                return False
            
            # Show model size
            model_size_gb = os.path.getsize(CONFIG["model_path"]) / (1024**3)
            print(f"[WavesAI] Model size: {model_size_gb:.2f} GB")
            
            self.llm = Llama(
                model_path=CONFIG["model_path"],
                n_ctx=CONFIG["context_length"],
                n_gpu_layers=CONFIG["gpu_layers"],
                n_threads=CONFIG["threads"],
                verbose=False
            )
            print(f"[WavesAI] ✓ {model_filename} loaded successfully with GPU acceleration")
            print(f"[WavesAI] Context: {CONFIG['context_length']} tokens | GPU Layers: {CONFIG['gpu_layers']} | Threads: {CONFIG['threads']}")
            return True
        except ImportError:
            print("[ERROR] llama-cpp-python not installed. Install with:")
            print("CMAKE_ARGS='-DLLAMA_CUBLAS=on' pip install llama-cpp-python")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return False
    
    def generate_response(self, user_input: str) -> str:
        """Generate AI response using loaded LLM with search context"""
        if not self.llm:
            return "Error: Model not loaded"
        
        system_info = self.get_system_context()
        
        # Check for file writing operations first
        file_writing_keywords = ['write', 'create', 'generate']
        file_indicators = [' in ', ' to ', '.txt', '.md', '.py', '.js', '.html', '.css']
        
        if (any(keyword in user_input.lower() for keyword in file_writing_keywords) and 
            any(indicator in user_input.lower() for indicator in file_indicators)):
            return self._handle_file_writing(user_input)
        
        # Check if this is an information query - ALWAYS search the internet for facts
        search_context = ""
        
        # Keywords that indicate the user wants information (not system commands)
        info_keywords = ['what', 'who', 'when', 'where', 'why', 'how', 'tell me', 'explain', 'about', 'is', 'are', 'was', 'were', 'define', 'meaning', 'search']
        news_keywords = ['news', 'headlines', 'breaking', 'latest news', 'current events', 'updates', 'indian news', 'us news', 'uk news', 'world news', 'local news', 'ndtv', 'bbc', 'cnn', 'reuters', 'news today', 'current news', 'breaking news']
        
        # System command keywords (don't search for these)
        command_keywords = ['open', 'close', 'kill', 'start', 'stop', 'install', 'remove', 'delete', 'create file', 'write to', 'execute', 'run', 'launch']
        
        # Determine if this is an information query
        is_info_query = any(keyword in user_input.lower() for keyword in info_keywords)
        is_command = any(keyword in user_input.lower() for keyword in command_keywords)
        is_news_query = any(keyword in user_input.lower() for keyword in news_keywords)
        
        # For news queries, use specialized news fetching
        if is_news_query:
            try:
                # Handle news queries with AI processing
                region = self._detect_news_region(user_input)
                print(f"\n[DEBUG] Fetching {region} news from internet...")
                news_results = self.search_news(user_input, region)
                print(f"[DEBUG] Fetched {len(news_results)} characters of news data")
                print(f"[DEBUG] First 200 chars: {news_results[:200]}...")
                
                # AI should ALWAYS process and refine the results
                search_context = f"""

🚨 CRITICAL - REAL-TIME NEWS DATA FETCHED FROM INTERNET 🚨

The following news was JUST FETCHED from live news websites RIGHT NOW in {datetime.now().strftime('%B %Y')}. This is NOT from your training data. This is CURRENT, REAL-TIME news:

{news_results}

⚠️ INSTRUCTIONS:
- PROCESS these 7 articles conversationally (NOT raw data)
- Use ONLY these articles (NOT your training data - it's outdated)
- ~400 words default | "in short" = ~150 words | "in detail" = ~600 words
- Narrate naturally with sources, end with question
- JARVIS-like: sophisticated, engaging, complete thoughts"""
            except Exception as e:
                search_context = f"\n\nNews search failed: {str(e)}. Respond conversationally like JARVIS, acknowledging the limitation and suggesting alternatives like visiting news websites directly."
        
        # For ALL other information queries (not news, not commands), search the internet
        elif is_info_query and not is_command:
            try:
                print(f"\n[DEBUG] Information query detected, searching internet...")
                
                # Search both Wikipedia and Web for comprehensive results
                wiki_results = self.search_wikipedia(user_input)
                web_results = self.search_web(user_input)
                
                print(f"[DEBUG] Wikipedia: {len(wiki_results)} chars, Web: {len(web_results)} chars")
                
                # Combine results intelligently
                combined_results = []
                
                if wiki_results and not ("failed" in wiki_results.lower() or "not found" in wiki_results.lower()):
                    combined_results.append(f"📚 WIKIPEDIA KNOWLEDGE (Authoritative):\n{wiki_results}")
                
                if web_results and not ("couldn't find" in web_results.lower() or "unable to fetch" in web_results.lower()):
                    combined_results.append(f"🌐 WEB SEARCH RESULTS (Current):\n{web_results}")
                
                if combined_results:
                    search_context = f"""

🚨 CRITICAL - REAL-TIME INTERNET DATA 🚨

The following information was JUST FETCHED from the internet RIGHT NOW in {datetime.now().strftime('%B %Y')}:

{chr(10).join(combined_results)}

⚠️ INSTRUCTIONS:
- PROCESS data conversationally (NOT raw)
- Use internet data for facts, your knowledge for analysis
- ~400 words default | "in short" = ~150 words | "in detail" = ~600 words
- JARVIS-like: sophisticated, engaging, synthesize naturally"""
                else:
                    print("[DEBUG] No internet results, using LLM knowledge")
            except Exception as e:
                print(f"[DEBUG] Search failed: {e}")
                pass
        
        # Check for weather and location queries
        weather_keywords = ['weather', 'temperature', 'climate', 'forecast', 'rain', 'sunny', 'cloudy', 'hot', 'cold', 'warm']
        location_keywords = ['location', 'where am i', 'my location', 'current location', 'where i am']
        
        if (any(keyword in user_input.lower() for keyword in weather_keywords) or 
            any(keyword in user_input.lower() for keyword in location_keywords)):
            try:
                # For location queries, provide location info
                if any(keyword in user_input.lower() for keyword in location_keywords):
                    location_data = self.system_monitor.location_weather.get_location()
                    if not location_data.get('error'):
                        city = location_data.get('city', 'Unknown')
                        region = location_data.get('region', '')
                        country = location_data.get('country', 'Unknown')
                        location_str = f"{city}"
                        if region and region != city:
                            location_str += f", {region}"
                        location_str += f", {country}"
                        
                        search_context = f"\n\nLOCATION INFORMATION:\nCurrent Location: {location_str}\nTimezone: {location_data.get('timezone', 'Unknown')}\n\nIMPORTANT: Process this location data and respond conversationally like JARVIS. Be sophisticated, friendly, and natural. Don't just state the raw data - present it in an engaging, helpful way."
                
                # For weather queries, provide weather info
                if any(keyword in user_input.lower() for keyword in weather_keywords):
                    # Extract location from query if specified
                    location = None
                    if " in " in user_input.lower():
                        location_part = user_input.lower().split(" in ")[-1].strip()
                        location = location_part
                    elif " at " in user_input.lower():
                        location_part = user_input.lower().split(" at ")[-1].strip()
                        location = location_part
                    elif "here" in user_input.lower() or "my location" in user_input.lower():
                        # Use current location
                        location = None
                    
                    # Get weather information
                    weather_results = self.system_monitor.location_weather.get_weather_summary(location)
                    
                    if weather_results and not ("error" in weather_results.lower()):
                        search_context = f"\n\nWEATHER INFORMATION:\n{weather_results}\n\nIMPORTANT: Process this weather data and respond conversationally like JARVIS. Don't just repeat the raw data - analyze it and present it in a sophisticated, engaging way. Comment on the conditions, temperature, and any relevant details. Be helpful and natural."
            except Exception as e:
                # Fallback: at least provide location
                try:
                    location_data = self.system_monitor.location_weather.get_location()
                    if not location_data.get('error'):
                        city = location_data.get('city', 'Unknown')
                        region = location_data.get('region', '')
                        country = location_data.get('country', 'Unknown')
                        search_context = f"\n\nCURRENT LOCATION: {city}, {region}, {country}\n\nUse this location information in your response."
                except:
                    pass
        
        # Format system status for the prompt
        system_status = f"""- User: {system_info['username']}@{system_info['hostname']}
- CPU: {system_info['cpu_usage']} | Temp: {system_info['cpu_temp']}
- RAM: {system_info['ram_usage']}
- {system_info['gpu_info']}
- Uptime: {system_info['uptime']}
- Time: {system_info['current_time']}
- {system_info.get('location', 'Location: Unknown')}"""
        
        # Load system prompt from file and inject system status
        system_prompt = self.system_prompt_template.replace("{system_status}", system_status)

        # Llama 3.1 prompt format (without <|begin_of_text|> - model adds it automatically)
        prompt = f"""<|start_header_id|>system<|end_header_id|>

{system_prompt}{search_context}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

        try:
            response = self.llm(
                prompt,
                max_tokens=CONFIG["max_tokens"],
                temperature=CONFIG["temperature"],
                stop=["<|eot_id|>", "<|end_of_text|>", "User:", "[You]"],
                echo=False
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"Error: {e}"
    
    def _handle_file_writing(self, response: str):
        """Handle file writing operations smoothly"""
        try:
            # Extract file path and content
            lines = response.split('\n')
            file_path = None
            content_lines = []
            in_content = False
            
            for line in lines:
                if line.startswith("WRITE_TO_FILE:"):
                    file_path = line.replace("WRITE_TO_FILE:", "").strip()
                elif line.startswith("CONTENT_START"):
                    in_content = True
                elif line.startswith("CONTENT_END"):
                    in_content = False
                elif in_content:
                    content_lines.append(line)
            
            if not file_path:
                print(f"\033[1;31m[Error]\033[0m No file path specified")
                return
            
            # Expand home directory
            if file_path.startswith("~/"):
                file_path = os.path.expanduser(file_path)
            
            # Write content to file
            content = '\n'.join(content_lines)
            
            print(f"\033[1;35m[WavesAI]\033[0m ➜ Writing {len(content)} characters to {file_path}")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"\033[1;32m[Success]\033[0m File written successfully: {file_path}")
            print(f"\033[1;36m[Info]\033[0m Content length: {len(content)} characters, {len(content_lines)} lines")
            
        except Exception as e:
            print(f"\033[1;31m[Error]\033[0m Failed to write file: {e}")
    
    def _handle_file_operations(self, user_input: str) -> Optional[str]:
        """Handle common file operations with smart detection"""
        lower_input = user_input.lower()
        
        # Read file operations
        read_patterns = ['read', 'show', 'display', 'cat', 'view', 'open and show']
        if any(pattern in lower_input for pattern in read_patterns) and ('file' in lower_input or '.txt' in lower_input or '.py' in lower_input or '.json' in lower_input):
            # Extract file path
            for word in user_input.split():
                if '/' in word or '.' in word:
                    file_path = word.strip('.,;:')
                    if file_path.startswith('~/'):
                        file_path = os.path.expanduser(file_path)
                    
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Show file info
                            lines = len(content.split('\n'))
                            chars = len(content)
                            
                            print(f"\033[1;36m[File Info]\033[0m {file_path}")
                            print(f"\033[1;36m[Size]\033[0m {chars} characters, {lines} lines")
                            print(f"\033[1;32m[Content]\033[0m\n{content}")
                            return f"File '{file_path}' displayed successfully"
                        except Exception as e:
                            return f"Error reading file: {e}"
                    else:
                        return f"File not found: {file_path}"
        
        # List files operations
        if 'list files' in lower_input or 'show files' in lower_input:
            # Extract directory path or use current
            directory = '.'
            if ' in ' in lower_input:
                dir_part = lower_input.split(' in ')[-1].strip()
                directory = dir_part if dir_part else '.'
            
            if directory.startswith('~/'):
                directory = os.path.expanduser(directory)
            
            return None  # Let it fall through to execute ls command
        
        return None

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
    
    def extract_and_execute_command(self, text: str, user_input: str) -> str:
        """Extract command from AI response and execute it automatically if safe"""
        # Check if response contains a bash command
        if "```bash" in text:
            cmd_start = text.find("```bash") + 7
            cmd_end = text.find("```", cmd_start)
            if cmd_end > cmd_start:
                command = text[cmd_start:cmd_end].strip()
                
                # Auto-execute safe commands
                if self.is_safe_command(command):
                    result = self.execute_command(command)
                    
                    # Return clean response based on success
                    if result['success']:
                        # Extract just the conversational part before the code block
                        response_text = text[:text.find("```bash")].strip()
                        if not response_text:
                            response_text = "Done, sir."
                        self.save_interaction(user_input, response_text, command)
                        return response_text
                    else:
                        return f"I encountered an error: {result['error']}"
                else:
                    # For non-safe commands, ask for confirmation
                    return command  # Return command for confirmation
        
        return None
    
    # Removed duplicate execute_command - using command_handler.execute_command() instead
    
    def validate_response(self, user_input: str, ai_response: str) -> str:
        """Validate AI response to prevent hallucinations"""
        lower_input = user_input.lower()
        lower_response = ai_response.lower()
        
        # Allow all search results - we now have enhanced search capabilities
        # No longer blocking legitimate search results
        
        # Check for claims about executing commands that weren't actually executed
        if any(claim in lower_response for claim in ['done', 'completed', 'executed', 'finished']):
            if 'command' in lower_response and '```' not in ai_response:
                # This might be a hallucinated execution claim
                return "I cannot execute that command directly. Please provide the specific command you'd like me to run, sir."
        
        return ai_response  # Response is valid
    
    def save_interaction(self, user_input: str, ai_response: str, command: str = None):
        """Save interaction to database"""
        try:
            self.cursor.execute("""
                INSERT INTO memory (timestamp, context, user_input, ai_response, executed_command)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                json.dumps(self.system_context),
                user_input,
                ai_response,
                command
            ))
            self.conn.commit()
        except Exception as e:
            print(f"[Warning] Failed to save interaction: {e}")
    
    def is_valid_news_title(self, title: str) -> bool:
        """Check if a title is a valid news headline (not metadata)"""
        title_lower = title.lower()
        
        # Filter out common metadata patterns
        invalid_patterns = [
            'search records',
            'rss feed',
            'feedburner',
            'ndtv news search',
            'site feed',
            'channel feed',
            'news feed',
            'rss channel',
            'feed:',
            'xml version',
            'encoding=',
            '<?xml',
            '<rss',
            '<channel>',
            'description:',
            'link:',
            'generator:',
            'lastbuilddate:',
            'copyright:',
            'language:',
            'managingeditor:',
            'webmaster:',
            'ttl:',
            'image:',
            'category:'
        ]
        
        # Check if title contains any invalid patterns
        for pattern in invalid_patterns:
            if pattern in title_lower:
                return False
        
        # Valid news title should be reasonably long and contain meaningful content
        return (len(title) > 15 and 
                len(title) < 200 and
                not title.startswith('<?') and
                not title.startswith('<') and
                ':' in title or len(title.split()) >= 4)
    
    def fetch_real_news(self, location: str = None) -> str:
        """Fetch real news from RSS feeds and news APIs"""
        try:
            news_sources = []
            
            # Define news sources based on location
            if location == 'india':
                news_sources = [
                    'https://www.ndtv.com/rss',
                    'https://feeds.feedburner.com/ndtvnews-india-news',
                    'https://www.thehindu.com/news/national/?service=rss',
                    'https://timesofindia.indiatimes.com/rssfeeds/1221656.cms'
                ]
            else:  # world news or default
                news_sources = [
                    'https://feeds.bbci.co.uk/news/world/rss.xml',
                    'https://rss.cnn.com/rss/edition.rss',
                    'https://feeds.reuters.com/reuters/worldNews'
                ]
            
            # Try to fetch from news sources
            for source in news_sources:
                try:
                    response = requests.get(source, timeout=10)
                    if response.status_code == 200:
                        # Parse RSS feed (improved parsing)
                        content = response.text
                        
                        # Extract actual news item titles (skip feed metadata)
                        import re
                        news_items = []
                        
                        # Try different RSS parsing approaches
                        # Method 1: Look for item blocks
                        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
                        for item in items[:10]:  # Check first 10 items
                            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
                            if title_match:
                                title = title_match.group(1) if title_match.group(1) else title_match.group(2)
                                if title and self.is_valid_news_title(title):
                                    news_items.append(f"• {title}")
                                    if len(news_items) >= 5:
                                        break
                        
                        # Method 2: If no items found, try simpler approach
                        if not news_items:
                            all_titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', content)
                            for title_tuple in all_titles:
                                title = title_tuple[0] if title_tuple[0] else title_tuple[1]
                                if title and self.is_valid_news_title(title):
                                    news_items.append(f"• {title}")
                                    if len(news_items) >= 5:
                                        break
                        
                        if news_items:
                            return f"Latest news from {location or 'world'}:\n\n" + "\n".join(news_items)
                
                except Exception as e:
                    continue
            
            # Fallback to web search for news
            return self.search_web(f"latest news {location or 'world'}")
            
        except Exception as e:
            return f"Unable to fetch news: {str(e)}"
    
    def fetch_news_details(self, news_topic: str) -> str:
        """Fetch detailed information about a specific news topic"""
        try:
            # Use web search to find more details about the specific news story
            search_query = f"{news_topic} news details latest"
            
            # Try DuckDuckGo API first
            url = f"https://api.duckduckgo.com/?q={search_query}&format=json"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            result = ""
            
            # Get abstract if available
            if data.get('AbstractText'):
                abstract = data['AbstractText']
                if len(abstract) > 50:  # Ensure it's substantial content
                    result = f"Here's what I found about {news_topic}:\n\n{abstract}"
            
            # Get related topics for more context
            if data.get('RelatedTopics'):
                related_info = []
                for topic in data['RelatedTopics'][:3]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        related_info.append(f"• {topic['Text']}")
                
                if related_info:
                    if result:
                        result += "\n\nAdditional information:\n" + '\n'.join(related_info)
                    else:
                        result = f"Related information about {news_topic}:\n\n" + '\n'.join(related_info)
            
            # If no good results from DuckDuckGo, try web scraping
            if not result or len(result) < 100:
                try:
                    # Try to get more detailed content from web search
                    search_url = f"https://html.duckduckgo.com/html/?q={search_query.replace(' ', '+')}"
                    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
                    response = requests.get(search_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        content = response.text
                        # Simple content extraction (look for result snippets)
                        import re
                        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', content)
                        
                        if snippets:
                            details = []
                            for snippet in snippets[:3]:
                                clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                                if len(clean_snippet) > 30:
                                    details.append(f"• {clean_snippet}")
                            
                            if details:
                                result = f"Here's what I found about {news_topic}:\n\n" + '\n'.join(details)
                
                except Exception as e:
                    pass
            
            # If still no results, be honest about limitations
            if not result:
                return f"I can see that '{news_topic}' was in recent headlines, but I don't have access to the full article content. For complete details, please visit news websites like NDTV, The Hindu, or Times of India, sir."
            
            return result
            
        except Exception as e:
            return f"I'm having trouble getting detailed information about '{news_topic}'. Please check news websites directly for the full story, sir."
    
    def get_weather(self, location: str = None) -> str:
        """Fetch weather information"""
        try:
            if not location:
                # Try to get location from IP
                loc_response = requests.get('https://ipapi.co/json/', timeout=5)
                location = loc_response.json().get('city', 'London')
            
            # Use wttr.in for weather
            response = requests.get(f'https://wttr.in/{location}?format=3', timeout=5)
            return response.text.strip()
        except:
            return "Unable to fetch weather data"
    
    def search_wikipedia(self, query: str) -> str:
        """Search Wikipedia for comprehensive information"""
        try:
            # Wikipedia API search
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(' ', '_')
            
            headers = {
                'User-Agent': 'WavesAI/1.0 (https://github.com/wavesai/wavesai)'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                result_parts = []
                
                # Get title
                if data.get('title'):
                    result_parts.append(f"**{data['title']}**")
                
                # Get extract (summary)
                if data.get('extract'):
                    extract = data['extract']
                    result_parts.append(f"**Summary:**\n{extract}")
                
                # Get description
                if data.get('description'):
                    result_parts.append(f"**Description:** {data['description']}")
                
                # Get coordinates for places
                if data.get('coordinates'):
                    coords = data['coordinates']
                    result_parts.append(f"**Location:** {coords.get('lat', 'N/A')}°N, {coords.get('lon', 'N/A')}°E")
                
                # Get page URL
                if data.get('content_urls', {}).get('desktop', {}).get('page'):
                    page_url = data['content_urls']['desktop']['page']
                    result_parts.append(f"*Source: [Wikipedia]({page_url})*")
                
                if result_parts:
                    return "\n\n".join(result_parts)
            
            # If direct page doesn't exist, try search
            return self.search_wikipedia_articles(query)
            
        except Exception as e:
            return f"Wikipedia search failed: {str(e)}"
    
    def search_wikipedia_articles(self, query: str) -> str:
        """Search for Wikipedia articles when direct page doesn't exist"""
        try:
            # Wikipedia search API
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 3,
                'srprop': 'snippet|size'
            }
            
            headers = {
                'User-Agent': 'WavesAI/1.0 (https://github.com/wavesai/wavesai)'
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if data.get('query', {}).get('search'):
                    for article in data['query']['search'][:3]:
                        title = article.get('title', '')
                        snippet = article.get('snippet', '')
                        
                        # Clean up HTML entities in snippet
                        import html
                        snippet = html.unescape(snippet)
                        snippet = snippet.replace('<span class="searchmatch">', '').replace('</span>', '')
                        
                        if title and snippet:
                            results.append(f"**{title}**\n{snippet}")
                
                if results:
                    return "**Wikipedia Search Results:**\n\n" + "\n\n".join(results)
            
            return "No Wikipedia articles found for that query."
            
        except Exception as e:
            return f"Wikipedia search failed: {str(e)}"
    
    def get_wikipedia_content(self, title: str) -> str:
        """Get full Wikipedia article content"""
        try:
            # Get page content
            content_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{title.replace(' ', '_')}"
            
            headers = {
                'User-Agent': 'WavesAI/1.0 (https://github.com/wavesai/wavesai)'
            }
            
            response = requests.get(content_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Parse HTML content to extract text
                import re
                from html import unescape
                
                content = response.text
                
                # Extract main content (simplified parsing)
                # Remove HTML tags but keep structure
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                content = unescape(content)
                
                # Get first few paragraphs (approximately 1000 characters)
                paragraphs = content.split('.')
                summary = ""
                for para in paragraphs:
                    if len(summary + para) < 1000:
                        summary += para + "."
                    else:
                        break
                
                return summary.strip() if summary else content[:1000] + "..."
            
            return "Could not retrieve Wikipedia content."
            
        except Exception as e:
            return f"Wikipedia content retrieval failed: {str(e)}"
    
    def search_web(self, query: str) -> str:
        """Enhanced web search using DuckDuckGo's full potential"""
        try:
            # Try DuckDuckGo Instant Answer API first with enhanced parameters
            api_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1&t=wavesai"
            api_response = requests.get(api_url, timeout=10)
            api_data = api_response.json()
            
            result_parts = []
            
            # Get instant answer/abstract
            if api_data.get('AbstractText'):
                abstract = api_data['AbstractText']
                abstract_source = api_data.get('AbstractSource', 'Wikipedia')
                result_parts.append(f"**{api_data.get('Abstract', 'Information')}:**\n{abstract}\n*Source: {abstract_source}*")
            
            # Get definition if available
            if api_data.get('Definition'):
                result_parts.append(f"**Definition:** {api_data['Definition']}")
            
            # Get answer (for direct questions)
            if api_data.get('Answer'):
                result_parts.append(f"**Answer:** {api_data['Answer']}")
            
            # Get related topics
            if api_data.get('RelatedTopics'):
                related_info = []
                for topic in api_data['RelatedTopics'][:5]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        related_info.append(f"• {topic['Text']}")
                if related_info:
                    result_parts.append("**Related Information:**\n" + '\n'.join(related_info))
            
            # Get definitions from definitions array
            if api_data.get('Definitions'):
                definitions = []
                for def_item in api_data['Definitions'][:3]:
                    if isinstance(def_item, dict) and 'Definition' in def_item:
                        definitions.append(f"• {def_item['Definition']}")
                if definitions:
                    result_parts.append("**Definitions:**\n" + '\n'.join(definitions))
            
            # Get infobox data for biographical information
            if api_data.get('Infobox'):
                infobox = api_data['Infobox']
                if isinstance(infobox, dict):
                    infobox_info = []
                    for key, value in infobox.items():
                        if isinstance(value, str) and len(value) > 5:
                            infobox_info.append(f"• **{key.replace('_', ' ').title()}:** {value}")
                    if infobox_info:
                        result_parts.append("**Key Details:**\n" + '\n'.join(infobox_info[:8]))  # Limit to 8 items
            
            # If we have good results from API, return them
            if result_parts:
                return "\n\n".join(result_parts)
            
            # If API doesn't have enough info, try HTML search for more comprehensive results
            html_result = self.search_web_html(query)
            
            # If HTML search also fails or returns generic error, try to provide some basic info
            if ("couldn't extract" in html_result.lower() or 
                "couldn't find" in html_result.lower() or
                "no results were found" in html_result.lower()):
                
                # Try one more fallback: return basic API info even if minimal
                if api_data.get('AbstractText') or api_data.get('RelatedTopics'):
                    fallback_parts = []
                    if api_data.get('AbstractText'):
                        fallback_parts.append(f"**Basic Information:** {api_data['AbstractText']}")
                    if api_data.get('RelatedTopics'):
                        related = []
                        for topic in api_data['RelatedTopics'][:2]:
                            if isinstance(topic, dict) and 'Text' in topic:
                                related.append(f"• {topic['Text']}")
                        if related:
                            fallback_parts.append("**Related:**\n" + '\n'.join(related))
                    
                    if fallback_parts:
                        return "\n\n".join(fallback_parts) + "\n\n*Note: Limited information available. For more details, please check the source websites directly.*"
            
            return html_result
            
        except Exception as e:
            return f"Search failed: {str(e)}. Please try again or check your internet connection, sir."
    
    def search_web_html(self, query: str) -> str:
        """Enhanced HTML search using DuckDuckGo for comprehensive results"""
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                results = []
                
                import re
                
                # Strategy 1: Try DuckDuckGo's current HTML structure patterns
                # Look for result containers with various possible class names
                result_patterns = [
                    r'<div class="result"[^>]*>(.*?)</div>',
                    r'<div class="web-result"[^>]*>(.*?)</div>',
                    r'<div class="result__body"[^>]*>(.*?)</div>',
                    r'<article[^>]*>(.*?)</article>',
                    r'<div class="result__snippet"[^>]*>(.*?)</div>'
                ]
                
                for pattern in result_patterns:
                    result_blocks = re.findall(pattern, content, re.DOTALL)
                    if result_blocks:
                        break
                
                if result_blocks:
                    for block in result_blocks[:5]:  # Get top 5 results
                        # Try multiple title extraction patterns
                        title_patterns = [
                            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="[^"]*"[^>]*>(.*?)</a>',
                            r'<a[^>]*href="[^"]*"[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>',
                            r'<h2[^>]*><a[^>]*href="[^"]*"[^>]*>(.*?)</a></h2>',
                            r'<h3[^>]*><a[^>]*href="[^"]*"[^>]*>(.*?)</a></h3>',
                            r'<a[^>]*href="[^"]*"[^>]*>(.*?)</a>'
                        ]
                        
                        title = None
                        for title_pattern in title_patterns:
                            title_match = re.search(title_pattern, block)
                            if title_match:
                                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                                if title and len(title) > 5:
                                    break
                        
                        # Try multiple snippet extraction patterns
                        snippet_patterns = [
                            r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
                            r'<div[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>',
                            r'<span[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</span>',
                            r'<p[^>]*>(.*?)</p>',
                            r'<div[^>]*class="[^"]*snippet[^"]*"[^>]*>(.*?)</div>',
                            r'<div[^>]*class="[^"]*result__body[^"]*"[^>]*>(.*?)</div>',
                            r'<span[^>]*class="[^"]*result__body[^"]*"[^>]*>(.*?)</span>',
                            r'<div[^>]*class="[^"]*web-result[^"]*"[^>]*>(.*?)</div>'
                        ]
                        
                        snippet = None
                        for snippet_pattern in snippet_patterns:
                            snippet_match = re.search(snippet_pattern, block)
                            if snippet_match:
                                snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                                if snippet and len(snippet) > 15:
                                    break
                        
                        # If no snippet found, try to extract any meaningful text from the block
                        if not snippet:
                            # Remove HTML tags and get clean text
                            clean_block = re.sub(r'<[^>]+>', ' ', block)
                            clean_block = re.sub(r'\s+', ' ', clean_block).strip()
                            
                            # Look for sentences that might be descriptions
                            sentences = clean_block.split('.')
                            for sentence in sentences:
                                sentence = sentence.strip()
                                if (len(sentence) > 30 and len(sentence) < 300 and 
                                    not sentence.lower().startswith('http') and
                                    'click' not in sentence.lower() and
                                    'visit' not in sentence.lower()):
                                    snippet = sentence
                                    break
                        
                        # Format the result with title and snippet
                        if title and len(title) > 5:
                            if snippet and len(snippet) > 10:
                                results.append(f"**{title}**\n{snippet}")
                            else:
                                results.append(f"**{title}**\n*No additional details available*")
                
                # Strategy 2: If no results from structured parsing, try general text extraction
                if not results:
                    # Look for any links that might be search results
                    link_patterns = [
                        r'<a[^>]*href="http[^"]*"[^>]*>(.*?)</a>',
                        r'<h[2-4][^>]*>(.*?)</h[2-4]>'
                    ]
                    
                    for pattern in link_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches[:5]:
                            clean_text = re.sub(r'<[^>]+>', '', match).strip()
                            if clean_text and len(clean_text) > 10 and len(clean_text) < 200:
                                results.append(f"• {clean_text}")
                        if results:
                            break
                
                # Strategy 3: Fallback to simple text extraction
                if not results:
                    # Extract any meaningful text content
                    text_content = re.sub(r'<[^>]+>', ' ', content)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    
                    # Look for sentences that might be relevant
                    sentences = text_content.split('.')
                    for sentence in sentences[:10]:
                        sentence = sentence.strip()
                        if (len(sentence) > 30 and len(sentence) < 300 and 
                            any(word in sentence.lower() for word in query.lower().split())):
                            results.append(f"• {sentence}")
                            if len(results) >= 3:
                                break
                
                if results:
                    return "**Search Results:**\n\n" + "\n\n".join(results[:5])
                else:
                    # Debug information for troubleshooting
                    debug_info = f"Debug: Found {len(content)} characters in response. "
                    debug_info += f"Tried {len(result_patterns)} result patterns. "
                    debug_info += f"Response contains 'result' class: {'result' in content}. "
                    return f"I found search results but couldn't extract meaningful content. {debug_info}Please try rephrasing your query, sir."
            
            return "Search completed but no results were found. Please try a different query, sir."
            
        except Exception as e:
            return f"Search failed: {str(e)}. Please try again, sir."
    
    def debug_search_html(self, query: str) -> str:
        """Debug function to help troubleshoot HTML parsing issues"""
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Analyze the HTML structure
                analysis = []
                analysis.append(f"Response length: {len(content)} characters")
                analysis.append(f"Contains 'result' class: {'result' in content}")
                analysis.append(f"Contains 'result__a' class: {'result__a' in content}")
                analysis.append(f"Contains 'result__snippet' class: {'result__snippet' in content}")
                analysis.append(f"Contains 'web-result' class: {'web-result' in content}")
                analysis.append(f"Contains 'article' tag: {'<article' in content}")
                
                # Find all unique class names containing 'result'
                import re
                class_matches = re.findall(r'class="[^"]*result[^"]*"', content)
                unique_classes = list(set(class_matches))
                analysis.append(f"Found result-related classes: {unique_classes[:10]}")
                
                # Look for any links
                link_matches = re.findall(r'<a[^>]*href="http[^"]*"[^>]*>(.*?)</a>', content)
                analysis.append(f"Found {len(link_matches)} external links")
                
                return "\n".join(analysis)
            else:
                return f"HTTP Error: {response.status_code}"
                
        except Exception as e:
            return f"Debug failed: {str(e)}"
    
    def startup_briefing(self):
        """Display startup information with enhanced monitoring"""
        info = self.get_system_context()
        
        # Handle error case
        if 'error' in info:
            print(f"\n\033[1;31m[WavesAI Error]\033[0m ➜ System monitoring failed: {info['error']}")
            print("\n\033[1;32m[WavesAI]\033[0m ➜ System initialized with limited monitoring.")
            return
        
        weather = self.get_weather()
        alerts = self.get_system_alerts()
        
        briefing = f"""
╔══════════════════════════════════════════════════════════╗
║              WavesAI - System Online                     ║
║              Enhanced Monitoring Active                  ║
╚══════════════════════════════════════════════════════════╝

Good day, {info.get('username', 'sir')}. WavesAI systems initialized with full monitoring.

System Status:
  • CPU Usage: {info.get('cpu_usage', 'N/A')} | Temperature: {info.get('cpu_temp', 'N/A')}
  • Memory: {info.get('ram_usage', 'N/A')}
  • {info.get('gpu_info', 'GPU: N/A')}
  • Disk: {info.get('disk_usage', 'N/A')}
  • Uptime: {info.get('uptime', 'N/A')}
  • Processes: {info.get('process_count', 'N/A')} active
  • Load Average: {info.get('load_avg', 'N/A')}

Weather: {weather}
Time: {info.get('current_time', 'N/A')}

Monitoring Commands Available:
  • 'monitor' - Detailed system report
  • 'alerts' - Check system warnings
  • 'top processes' - CPU-heavy processes
  • 'monitor process [name]' - Track specific process
  • 'network' - Network statistics

{f"🚨 System Alerts: {'; '.join(alerts)}" if alerts else "✅ All systems operational"}

How may I assist you?
"""
        print(briefing)
    
    def start_monitoring_thread(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while True:
                try:
                    alerts = self.get_system_alerts()
                    if alerts:
                        print(f"\n\033[1;33m[WavesAI Alert]\033[0m ➜ {'; '.join(alerts)}")
                    time.sleep(30)  # Check every 30 seconds
                except:
                    time.sleep(60)  # If error, wait longer
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def setup_sudo_access(self):
        """Setup sudo access with user confirmation - JARVIS style"""
        print("\n\033[1;35m[WavesAI]\033[0m ➜ Sir, some operations may require elevated privileges.")
        print("\033[1;36m[Info]\033[0m I can temporarily store your sudo password for seamless operation.")
        print("\033[1;36m[Info]\033[0m The password will only be kept in memory during this session.")
        
        confirm = input("\n\033[1;33m[Confirm?]\033[0m Would you like to enable sudo access? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'confirm']:
            import getpass
            password = getpass.getpass("\033[1;32m[Sudo Password]\033[0m ➜ ")
            
            # Verify the password works
            print("\n\033[1;35m[WavesAI]\033[0m ➜ Verifying credentials...", end='\r')
            test_command = f"echo '{password}' | sudo -S echo 'verified' 2>/dev/null"
            result = subprocess.run(test_command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and 'verified' in result.stdout:
                self.sudo_password = password
                print("\033[1;35m[WavesAI]\033[0m ➜ Sudo access confirmed. I'll handle privileged operations seamlessly, sir.    ")
                return True
            else:
                print("\033[1;35m[WavesAI]\033[0m ➜ I'm afraid that password didn't work, sir. Continuing without sudo access.    ")
                return False
        else:
            print("\n\033[1;35m[WavesAI]\033[0m ➜ Understood, sir. I'll request sudo access when needed.")
            return False
    
    def execute_with_sudo(self, command: str) -> Dict:
        """Execute command with sudo using stored password"""
        if self.sudo_password:
            # Use stored password
            sudo_command = f"echo '{self.sudo_password}' | sudo -S {command}"
            try:
                result = subprocess.run(
                    sudo_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Clean up sudo password prompt from output
                stdout = result.stdout
                stderr = result.stderr
                if '[sudo]' in stderr:
                    stderr = '\n'.join([line for line in stderr.split('\n') if '[sudo]' not in line])
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "output": stdout,
                        "error": ""
                    }
                else:
                    # Analyze error
                    from modules.error_analyzer import get_error_analyzer
                    error_analyzer = get_error_analyzer()
                    error_analysis = error_analyzer.analyze_error(stderr, command)
                    
                    return {
                        "success": False,
                        "output": stdout,
                        "error": stderr,
                        "error_analysis": error_analysis
                    }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": "Command timed out",
                    "error_analysis": {
                        "summary": "Command timeout",
                        "solution": "The command took too long. It may require user input or be stuck.",
                        "category": "timeout"
                    }
                }
            except Exception as e:
                from modules.error_analyzer import get_error_analyzer
                error_analyzer = get_error_analyzer()
                error_analysis = error_analyzer.analyze_error(str(e), command)
                return {
                    "success": False,
                    "error": str(e),
                    "error_analysis": error_analysis
                }
        else:
            # No stored password, ask user
            print(f"\n\033[1;35m[WavesAI]\033[0m ➜ This operation requires sudo privileges, sir.")
            return self.command_handler.execute_command(f"sudo {command}")
    
    def is_dangerous_command(self, command: str) -> bool:
        """Check if command is dangerous and requires confirmation"""
        command_lower = command.lower()
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                return True
        return False
    
    def generate_confirmation_code(self) -> str:
        """Generate a random 5-digit confirmation code"""
        import random
        return str(random.randint(10000, 99999))
    
    def request_confirmation(self, command: str) -> str:
        """Request confirmation for dangerous command and return confirmation message"""
        self.confirmation_code = self.generate_confirmation_code()
        self.pending_dangerous_command = command
        
        # Determine what the command will do
        risk_message = ""
        if 'mkfs' in command.lower():
            risk_message = "will PERMANENTLY ERASE all data on the specified drive"
        elif 'rm -rf' in command.lower():
            risk_message = "will PERMANENTLY DELETE files and directories"
        elif 'dd if=' in command.lower():
            risk_message = "will OVERWRITE data and can destroy entire drives"
        elif 'shred' in command.lower() or 'wipe' in command.lower():
            risk_message = "will SECURELY ERASE data making it unrecoverable"
        elif 'fdisk' in command.lower() or 'parted' in command.lower():
            risk_message = "will MODIFY disk partitions which can cause data loss"
        elif 'lvremove' in command.lower() or 'vgremove' in command.lower():
            risk_message = "will REMOVE LVM volumes and all data on them"
        elif 'iptables -F' in command.lower():
            risk_message = "will FLUSH all firewall rules leaving system unprotected"
        elif 'reboot' in command.lower() or 'shutdown' in command.lower() or 'poweroff' in command.lower():
            risk_message = "will RESTART/SHUTDOWN the system immediately"
        elif 'systemctl isolate' in command.lower():
            risk_message = "will CHANGE system target which may kill running processes"
        else:
            risk_message = "is a DANGEROUS operation that may cause system damage"
        
        return f"Sir, this command {risk_message}. This action cannot be undone. Please confirm with code: {self.confirmation_code}"
    
    def check_confirmation(self, user_input: str) -> bool:
        """Check if user provided correct confirmation code"""
        if not self.confirmation_code or not self.pending_dangerous_command:
            return False
        
        # Check if user input contains the confirmation code
        if f"confirm with code {self.confirmation_code}" in user_input.lower():
            return True
        elif self.confirmation_code in user_input:
            return True
        
        return False
    
    def interactive_mode(self):
        """Main interactive loop"""
        if not self.load_llm():
            return
        
        # Start background monitoring
        self.start_monitoring_thread()
        self.startup_briefing()
        
        # Setup sudo access
        self.setup_sudo_access()
        
        while True:
            try:
                user_input = input("\n\033[1;36m[You]\033[0m ➜ ").strip()
                
                if not user_input:
                    continue
                
                # Check if user is confirming a dangerous command
                if self.check_confirmation(user_input):
                    command = self.pending_dangerous_command
                    print(f"\n\033[1;32m[Confirmed]\033[0m Executing dangerous command: {command}")
                    
                    # Execute the dangerous command
                    if command.startswith('sudo '):
                        actual_command = command[5:].strip()
                        result = self.execute_with_sudo(actual_command)
                    else:
                        result = self.execute_command(command)
                    
                    # Clear pending command and code
                    self.pending_dangerous_command = None
                    self.confirmation_code = None
                    
                    # Show result
                    if result['success']:
                        if result['output']:
                            print(f"\n\033[1;32m[Output]\033[0m\n{result['output']}")
                        print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Operation completed, sir.")
                    else:
                        # Handle error conversationally
                        if 'error_analysis' in result:
                            analysis = result['error_analysis']
                            error_prompt = f"""The command failed: {command}
Error: {analysis['summary']}
Details: {analysis.get('original_error', result.get('error', ''))}
Solution: {analysis['solution']}

Explain this error conversationally like JARVIS would."""
                            print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Analyzing error...", end='\r')
                            conversational_response = self.generate_response(error_prompt)
                            print(f"\033[1;35m[WavesAI]\033[0m ➜ {conversational_response}                    ")
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'goodbye', 'bye']:
                    print("\n\033[1;35m[WavesAI]\033[0m ➜ Shutting down. Until next time, sir.")
                    break
                
                # Special commands
                if user_input.lower() == 'status':
                    self.startup_briefing()
                    continue
                elif user_input.lower().startswith('weather'):
                    location = user_input[7:].strip() or None
                    print(f"\n\033[1;35m[WavesAI]\033[0m ➜ {self.get_weather(location)}")
                    continue
                elif user_input.lower().startswith('search') or user_input.lower().startswith('news') or user_input.lower().startswith('what is') or user_input.lower().startswith('who is') or user_input.lower().startswith('how to') or user_input.lower().startswith('explain') or user_input.lower().startswith('wikipedia'):
                    # Let AI handle search queries conversationally
                    print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Let me look that up for you, sir.")
                    # Continue to AI processing below
                
                # Try file operations first
                file_response = self._handle_file_operations(user_input)
                if file_response:
                    print(f"\n\033[1;35m[WavesAI]\033[0m ➜ {file_response}")
                    continue
                
                # Try smart_execute for direct commands
                smart_response = self.smart_execute(user_input)
                if smart_response:
                    print(f"\n\033[1;35m[WavesAI]\033[0m ➜ {smart_response}")
                    continue
                
                # Generate AI response
                print("\n\033[1;35m[WavesAI]\033[0m ➜ Processing...", end='\r')
                response = self.generate_response(user_input)
                # Validate response to prevent hallucinations
                response = self.validate_response(user_input, response)
                
                # Check if AI wants to write to a file
                if "WRITE_TO_FILE:" in response:
                    self._handle_file_writing(response)
                    continue
                
                # Check if AI wants to execute a command
                elif "EXECUTE_COMMAND:" in response:
                    command = response.split("EXECUTE_COMMAND:")[1].strip().split()[0] if " " in response.split("EXECUTE_COMMAND:")[1] else response.split("EXECUTE_COMMAND:")[1].strip()
                    # Extract full command line
                    cmd_start = response.find("EXECUTE_COMMAND:") + 16
                    cmd_end = response.find("\n", cmd_start) if "\n" in response[cmd_start:] else len(response)
                    command = response[cmd_start:cmd_end].strip()
                    
                    print(f"\033[1;35m[WavesAI]\033[0m ➜ Executing: {command}                    ")
                    
                    # Check if command is dangerous and requires confirmation code
                    if self.is_dangerous_command(command):
                        confirmation_message = self.request_confirmation(command)
                        print(f"\n\033[1;33m[⚠️  Warning]\033[0m {confirmation_message}")
                        continue  # Wait for user to provide confirmation code
                    
                    # Check if command requires sudo
                    if command.startswith('sudo '):
                        # Remove 'sudo' from command and use our sudo handler
                        actual_command = command[5:].strip()
                        result = self.execute_with_sudo(actual_command)
                    else:
                        # Execute normally
                        result = self.execute_command(command)
                    if result['success']:
                        if result['output']:
                            print(f"\n\033[1;32m[Output]\033[0m\n{result['output']}")
                            
                            # For resource monitoring commands, ask AI to provide a summary
                            monitoring_keywords = ['ps aux', 'du -', 'df -', 'free', 'top -', 'htop', 'awk', 'grep']
                            if any(keyword in command.lower() for keyword in monitoring_keywords):
                                summary_prompt = f"The user asked: '{user_input}'\nCommand executed: {command}\nOutput:\n{result['output']}\n\nProvide a brief, conversational summary of this information like JARVIS would."
                                summary = self.generate_response(summary_prompt)
                                print(f"\n\033[1;35m[WavesAI]\033[0m ➜ {summary}")
                    else:
                        # Pass error through LLM for conversational response
                        if 'error_analysis' in result:
                            analysis = result['error_analysis']
                            error_prompt = f"""The user tried to execute: {command}
The command failed with this error:

Error Type: {analysis['summary']}
Error Details: {analysis.get('original_error', result.get('error', 'Unknown error'))}
Recommended Solution: {analysis['solution']}

Explain this error to the user conversationally like JARVIS would. Be brief (2-3 sentences), explain what went wrong, and tell them how to fix it. Address them as 'sir' if appropriate."""
                            
                            print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Analyzing error...", end='\r')
                            conversational_response = self.generate_response(error_prompt)
                            print(f"\033[1;35m[WavesAI]\033[0m ➜ {conversational_response}                    ")
                        else:
                            # Fallback for errors without analysis
                            error_prompt = f"""The user tried to execute: {command}
The command failed with this error: {result.get('error', 'Unknown error')}

Explain this error to the user conversationally like JARVIS would. Be brief (2-3 sentences), explain what went wrong, and suggest how to fix it. Address them as 'sir' if appropriate."""
                            
                            print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Analyzing error...", end='\r')
                            conversational_response = self.generate_response(error_prompt)
                            print(f"\033[1;35m[WavesAI]\033[0m ➜ {conversational_response}                    ")
                    
                    self.save_interaction(user_input, f"Executed: {command}", command)
                    continue
                
                print(f"\033[1;35m[WavesAI]\033[0m ➜ {response}                    ")
                
                # Check if response contains bash code blocks
                if "```bash" in response:
                    cmd_start = response.find("```bash") + 7
                    cmd_end = response.find("```", cmd_start)
                    if cmd_end > cmd_start:
                        command = response[cmd_start:cmd_end].strip()
                        
                        confirm = input(f"\n\033[1;33m[Execute?]\033[0m {command} (y/n): ")
                        if confirm.lower() == 'y':
                            result = self.execute_command(command)
                            if result['success']:
                                if result['output']:
                                    print(f"\n\033[1;32m[Output]\033[0m\n{result['output']}")
                                else:
                                    print(f"\n\033[1;32m[Success]\033[0m Command executed successfully")
                            else:
                                # Pass error through LLM for conversational response
                                if 'error_analysis' in result:
                                    analysis = result['error_analysis']
                                    error_prompt = f"""The user tried to execute: {command}
The command failed with this error:

Error Type: {analysis['summary']}
Error Details: {analysis.get('original_error', result.get('error', 'Unknown error'))}
Recommended Solution: {analysis['solution']}

Explain this error to the user conversationally like JARVIS would. Be brief (2-3 sentences), explain what went wrong, and tell them how to fix it. Address them as 'sir' if appropriate."""
                                    
                                    print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Analyzing error...", end='\r')
                                    conversational_response = self.generate_response(error_prompt)
                                    print(f"\033[1;35m[WavesAI]\033[0m ➜ {conversational_response}                    ")
                                else:
                                    # Fallback for errors without analysis
                                    error_prompt = f"""The user tried to execute: {command}
The command failed with this error: {result.get('error', 'Unknown error')}

Explain this error to the user conversationally like JARVIS would. Be brief (2-3 sentences), explain what went wrong, and suggest how to fix it. Address them as 'sir' if appropriate."""
                                    
                                    print(f"\n\033[1;35m[WavesAI]\033[0m ➜ Analyzing error...", end='\r')
                                    conversational_response = self.generate_response(error_prompt)
                                    print(f"\033[1;35m[WavesAI]\033[0m ➜ {conversational_response}                    ")
                            
                            self.save_interaction(user_input, response, command)
                        else:
                            print("\n\033[1;33m[Skipped]\033[0m Command not executed")
                else:
                    self.save_interaction(user_input, response)
                
            except KeyboardInterrupt:
                print("\n\n\033[1;35m[WavesAI]\033[0m ➜ Interrupted. Type 'exit' to quit.")
                continue
            except Exception as e:
                print(f"\n\033[1;31m[Error]\033[0m {e}")

def main():
    print("""
    ╦ ╦┌─┐┬  ┬┌─┐┌─┐╔═╗╦  
    ║║║├─┤└┐┌┘├┤ └─┐╠═╣║  
    ╚╩╝┴ ┴ └┘ └─┘└─┘╩ ╩╩  
    Advanced AI Assistant System
    """)
    
    ai = WavesAI()
    
    # Check for voice modes
    if any(arg in sys.argv for arg in ["--voice", "voice"]):
        # Use the new sounddevice-based voice mode by default
        ai.voice_mode()
    elif any(arg in sys.argv for arg in ["--voice-old", "voice-pyaudio"]):
        # Old PyAudio-based voice mode (broken)
        ai.voice_mode_old()
    elif any(arg in sys.argv for arg in ["--voice-improved", "voice2"]):
        # Standalone improved voice mode
        try:
            from wavesai_voice_improved import ImprovedVoiceMode
            voice = ImprovedVoiceMode(ai)
            voice.run()
        except ImportError as e:
            print(f"\033[1;31m[Error]\033[0m Improved voice mode not available: {e}")
            print("\033[1;33m[Tip]\033[0m Run: pip install sounddevice faster-whisper")
    else:
        ai.interactive_mode()

if __name__ == "__main__":
    main()
