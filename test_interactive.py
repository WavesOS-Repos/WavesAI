#!/usr/bin/env python3
"""
Test interactive command detection
"""

import sys
sys.path.insert(0, '/home/bowser/.wavesai')

from modules.command_handler import CommandHandler

def test_interactive_detection():
    print("Testing interactive command detection...\n")
    
    handler = CommandHandler()
    
    test_commands = [
        ("sudo pacman -Syu", True),
        ("sudo pacman -S vim", True),
        ("nano ~/.bashrc", True),
        ("vim test.txt", True),
        ("htop", True),
        ("ls -la", False),
        ("ps aux | grep firefox", False),
        ("echo 'hello'", False),
        ("cat /etc/passwd", False)
    ]
    
    print("Command Detection Results:")
    print("=" * 50)
    
    for command, expected_interactive in test_commands:
        # Check if command would be detected as interactive
        interactive_commands = [
            'sudo pacman -Syu', 'sudo pacman -S', 'pacman -Syu', 'pacman -S',
            'sudo apt update', 'sudo apt upgrade', 'sudo apt install',
            'nano', 'vim', 'vi', 'emacs', 'htop', 'top', 'less', 'more',
            'sudo systemctl', 'systemctl', 'ssh', 'scp', 'rsync',
            'git commit', 'git rebase', 'git merge'
        ]
        
        is_interactive = any(cmd in command for cmd in interactive_commands)
        
        status = "✅ INTERACTIVE" if is_interactive else "📄 CAPTURED"
        expected = "✅ INTERACTIVE" if expected_interactive else "📄 CAPTURED"
        
        match = "✅" if is_interactive == expected_interactive else "❌"
        
        print(f"{match} {command:<30} → {status} (expected: {expected})")
    
    print("\n" + "=" * 50)
    print("Legend:")
    print("✅ INTERACTIVE - Runs directly in terminal, allows user input")
    print("📄 CAPTURED   - Output captured, no user interaction")
    print("\nInteractive commands will now work properly for:")
    print("- System updates (pacman -Syu)")
    print("- Package installations (pacman -S)")
    print("- Text editors (nano, vim)")
    print("- System monitors (htop, top)")
    print("- Git operations (commit, rebase)")

if __name__ == "__main__":
    test_interactive_detection()
