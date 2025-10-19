#!/usr/bin/env python3
"""
Test smart process detection
"""

import sys
sys.path.insert(0, '/home/bowser/.wavesai')

from modules.process_detector import ProcessDetector

def test_process_detection():
    print("Testing Smart Process Detection...")
    print("=" * 50)
    
    detector = ProcessDetector()
    
    # Test apps that might be running
    test_apps = [
        'windsurf',
        'cursor', 
        'chrome',
        'firefox',
        'vscode',
        'discord',
        'terminal',
        'obsidian',
        'spotify'
    ]
    
    for app in test_apps:
        print(f"\nSearching for '{app}':")
        matches = detector.find_process_by_name(app)
        
        if matches:
            print(f"  ✅ Found {len(matches)} processes:")
            for match in matches[:3]:  # Show first 3
                print(f"    • {match['name']} (PID: {match['pid']}, CPU: {match['cpu']}%, RAM: {match['mem']}%)")
                print(f"      Command: {match['command'][:80]}...")
        else:
            print(f"  ❌ No processes found")
    
    print("\n" + "=" * 50)
    print("Testing kill functionality (dry run):")
    
    # Test kill functionality (without actually killing)
    for app in ['windsurf', 'nonexistent']:
        print(f"\nTesting kill for '{app}':")
        matches = detector.find_process_by_name(app)
        if matches:
            print(f"  Would kill {len(matches)} processes:")
            for match in matches:
                print(f"    • PID {match['pid']}: {match['name']}")
        else:
            print(f"  No processes to kill for '{app}'")
    
    print("\n" + "=" * 50)
    print("App Aliases Available:")
    for app, aliases in list(detector.app_aliases.items())[:10]:
        print(f"  {app}: {', '.join(aliases[:3])}{'...' if len(aliases) > 3 else ''}")

if __name__ == "__main__":
    test_process_detection()
