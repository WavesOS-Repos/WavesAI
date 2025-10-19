#!/usr/bin/env python3
"""
Test background process execution
"""

import sys
sys.path.insert(0, '/home/bowser/.wavesai')

from modules.command_handler import CommandHandler

def test_background_execution():
    print("Testing background process execution...\n")
    
    handler = CommandHandler()
    
    # Test 1: Background process with &
    print("1. Testing: gedit &")
    result = handler.execute_command("gedit &")
    print(f"   Success: {result['success']}")
    print(f"   Output: {result['output']}")
    print(f"   Terminal should be responsive immediately!\n")
    
    # Test 2: Another background process
    print("2. Testing: chromium &")
    result = handler.execute_command("chromium &")
    print(f"   Success: {result['success']}")
    print(f"   Output: {result['output']}")
    print(f"   Terminal should still be responsive!\n")
    
    # Test 3: Foreground command (should wait)
    print("3. Testing: echo 'Hello World'")
    result = handler.execute_command("echo 'Hello World'")
    print(f"   Success: {result['success']}")
    print(f"   Output: {result['output'].strip()}")
    print(f"   This should have waited for completion.\n")
    
    print("✅ All tests completed!")
    print("If terminal is responsive and apps launched, the fix works!")

if __name__ == "__main__":
    test_background_execution()
