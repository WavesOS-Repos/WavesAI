#!/usr/bin/env python3
"""
Quick setup verification for WavesAI with Llama 3
"""

import os
from pathlib import Path
import json

def check_setup():
    print("🔍 WavesAI Setup Verification\n")
    
    issues = []
    warnings = []
    
    # 1. Check model file
    print("1. Checking model file...")
    model_path = Path.home() / ".wavesai/models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
    if model_path.exists():
        size_gb = model_path.stat().st_size / (1024**3)
        print(f"   ✅ Model found: {size_gb:.2f} GB")
    else:
        print(f"   ❌ Model NOT found at: {model_path}")
        issues.append("Model file missing")
        print("\n   Download with:")
        print("   cd ~/.wavesai/models")
        print("   wget https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")
    
    # 2. Check config
    print("\n2. Checking configuration...")
    config_path = Path.home() / ".wavesai/config/config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            model_in_config = config['model']['path']
            if 'Meta-Llama-3' in model_in_config:
                print(f"   ✅ Config updated for Llama 3")
            else:
                print(f"   ⚠️  Config still points to: {model_in_config}")
                warnings.append("Config may need update")
    else:
        print("   ❌ Config file not found")
        issues.append("Config missing")
    
    # 3. Check system prompt
    print("\n3. Checking system prompt...")
    prompt_path = Path.home() / ".wavesai/system_prompt.txt"
    if prompt_path.exists():
        with open(prompt_path, 'r') as f:
            content = f.read()
            if 'EXECUTE_COMMAND' in content:
                print("   ✅ System prompt configured")
            else:
                print("   ⚠️  System prompt may need update")
                warnings.append("System prompt incomplete")
    else:
        print("   ❌ System prompt not found")
        issues.append("System prompt missing")
    
    # 4. Check dependencies
    print("\n4. Checking dependencies...")
    try:
        import llama_cpp
        print("   ✅ llama-cpp-python installed")
    except ImportError:
        print("   ❌ llama-cpp-python NOT installed")
        issues.append("llama-cpp-python missing")
        print("\n   Install with:")
        print("   CMAKE_ARGS='-DLLAMA_CUBLAS=on' pip install llama-cpp-python")
    
    try:
        import psutil
        print("   ✅ psutil installed")
    except ImportError:
        print("   ⚠️  psutil NOT installed")
        warnings.append("psutil missing")
    
    try:
        import requests
        print("   ✅ requests installed")
    except ImportError:
        print("   ⚠️  requests NOT installed")
        warnings.append("requests missing")
    
    # 5. Check GPU
    print("\n5. Checking GPU...")
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ NVIDIA GPU detected")
        else:
            print("   ⚠️  nvidia-smi failed")
            warnings.append("GPU may not be available")
    except FileNotFoundError:
        print("   ⚠️  nvidia-smi not found")
        warnings.append("NVIDIA drivers may not be installed")
    
    # Summary
    print("\n" + "="*50)
    if not issues:
        print("✅ Setup looks good!")
        if warnings:
            print(f"\n⚠️  {len(warnings)} warnings:")
            for w in warnings:
                print(f"   - {w}")
        print("\nYou can start WavesAI with:")
        print("   cd ~/.wavesai")
        print("   python wavesai.py")
    else:
        print(f"❌ {len(issues)} critical issues found:")
        for i in issues:
            print(f"   - {i}")
        print("\nPlease fix these issues before running WavesAI")
    print("="*50)

if __name__ == "__main__":
    check_setup()
