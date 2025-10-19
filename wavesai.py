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
from typing import Dict, List, Optional
import threading
import time

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
        "model_path": str(Path.home() / ".wavesai/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"),
        "database": str(Path.home() / ".wavesai/config/memory.db"),
        "log_file": str(Path.home() / ".wavesai/config/logs/wavesai.log"),
        "context_length": 4096,
        "gpu_layers": 35,
        "threads": 8,
        "temperature": 0.7,
        "max_tokens": 512
    }

CONFIG = load_config()

class WavesAI:
    def __init__(self):
        self.setup_directories()
        self.init_database()
        self.llm = None
        self.conversation_history = []
        
        # Initialize modules
        self.search_engine = SearchEngine()
        self.system_monitor = SystemMonitor()
        self.command_handler = CommandHandler()
        
        self.system_context = self.system_monitor.get_system_context()
        self.system_prompt_template = self.load_system_prompt()
    
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
        
        # Check if this is a search query and get search results
        search_context = ""
        search_keywords = ['search', 'what is', 'who is', 'how to', 'explain', 'tell me about', 'biography', 'about']
        if any(keyword in user_input.lower() for keyword in search_keywords):
            try:
                # First try Wikipedia for comprehensive information
                wiki_results = self.search_wikipedia(user_input)
                
                # Also get web search results for current/recent information
                web_results = self.search_web(user_input)
                
                # Combine results intelligently
                combined_results = []
                if wiki_results and not ("failed" in wiki_results.lower() or "not found" in wiki_results.lower()):
                    combined_results.append("WIKIPEDIA KNOWLEDGE:\n" + wiki_results)
                
                if web_results and not ("couldn't find" in web_results.lower() or "no results" in web_results.lower()):
                    combined_results.append("WEB SEARCH RESULTS:\n" + web_results)
                
                if combined_results:
                    search_context = f"\n\nSEARCH RESULTS FOR CONTEXT:\n" + "\n\n---\n\n".join(combined_results) + "\n\nUse this comprehensive information to provide a conversational response. Synthesize Wikipedia knowledge with current information. Don't just repeat the search results - explain them naturally and conversationally."
            except:
                pass
        
        # Format system status for the prompt
        system_status = f"""- User: {system_info['username']}@{system_info['hostname']}
- CPU: {system_info['cpu_usage']} | Temp: {system_info['cpu_temp']}
- RAM: {system_info['ram_usage']}
- {system_info['gpu_info']}
- Uptime: {system_info['uptime']}
- Time: {system_info['current_time']}"""
        
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
    
    def execute_command(self, command: str, sudo: bool = False, timeout: int = 30) -> Dict:
        """Execute shell command with safety checks"""
        dangerous_commands = ['rm -rf /', 'mkfs', 'dd if=', ':(){:|:&};:', 'chmod -R 777 /', '> /dev/sda']
        
        for dangerous in dangerous_commands:
            if dangerous in command:
                return {"success": False, "error": "Dangerous command blocked for safety"}
        
        try:
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
    
    def interactive_mode(self):
        """Main interactive loop"""
        if not self.load_llm():
            return
        
        # Start background monitoring
        self.start_monitoring_thread()
        self.startup_briefing()
        
        while True:
            try:
                user_input = input("\n\033[1;36m[You]\033[0m ➜ ").strip()
                
                if not user_input:
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
                
                # Try smart_execute first for direct commands
                smart_response = self.smart_execute(user_input)
                if smart_response:
                    print(f"\n\033[1;35m[WavesAI]\033[0m ➜ {smart_response}")
                    continue
                
                # Generate AI response
                print("\n\033[1;35m[WavesAI]\033[0m ➜ Processing...", end='\r')
                response = self.generate_response(user_input)
                # Validate response to prevent hallucinations
                response = self.validate_response(user_input, response)
                
                # Check if AI wants to execute a command
                if "EXECUTE_COMMAND:" in response:
                    command = response.split("EXECUTE_COMMAND:")[1].strip().split()[0] if " " in response.split("EXECUTE_COMMAND:")[1] else response.split("EXECUTE_COMMAND:")[1].strip()
                    # Extract full command line
                    cmd_start = response.find("EXECUTE_COMMAND:") + 16
                    cmd_end = response.find("\n", cmd_start) if "\n" in response[cmd_start:] else len(response)
                    command = response[cmd_start:cmd_end].strip()
                    
                    print(f"\033[1;35m[WavesAI]\033[0m ➜ Executing: {command}                    ")
                    
                    # Ask for confirmation for dangerous commands
                    dangerous_keywords = ['reboot', 'shutdown', 'poweroff', 'halt', 'rm -rf', 'mkfs', 'dd']
                    if any(keyword in command.lower() for keyword in dangerous_keywords):
                        confirm = input(f"\n\033[1;33m[Confirm?]\033[0m This command will affect the system. Continue? (y/n): ")
                        if confirm.lower() != 'y':
                            print("\n\033[1;33m[Cancelled]\033[0m Command not executed.")
                            continue
                    
                    # Execute the command
                    result = self.execute_command(command)
                    if result['success']:
                        if result['output']:
                            print(f"\n\033[1;32m[Output]\033[0m\n{result['output']}")
                        else:
                            print(f"\n\033[1;32m[Success]\033[0m Done, sir.")
                    else:
                        print(f"\n\033[1;31m[Error]\033[0m {result['error']}")
                    
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
                                print(f"\n\033[1;31m[Error]\033[0m {result['error']}")
                            
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
    ai.interactive_mode()

if __name__ == "__main__":
    main()
