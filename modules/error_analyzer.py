#!/usr/bin/env python3
"""
WavesAI Error Analyzer Module
Analyzes command errors and provides intelligent solutions
"""

import re
from typing import Dict, Optional


class ErrorAnalyzer:
    """Analyzes errors and provides solutions"""
    
    def __init__(self):
        self.error_patterns = self._build_error_patterns()
    
    def _build_error_patterns(self) -> Dict:
        """Build comprehensive error pattern database"""
        return {
            # Permission errors
            'permission_denied': {
                'patterns': [
                    r'permission denied',
                    r'operation not permitted',
                    r'access denied',
                    r'cannot access',
                    r'you do not have permission'
                ],
                'summary': 'Permission denied',
                'solution': 'You need elevated privileges. Try running with sudo: sudo [command]',
                'category': 'permission'
            },
            
            # File not found errors
            'file_not_found': {
                'patterns': [
                    r'no such file or directory',
                    r'cannot find',
                    r'does not exist',
                    r'file not found',
                    r'not found'
                ],
                'summary': 'File or directory not found',
                'solution': 'Check if the path is correct and the file exists. Use ls to list files.',
                'category': 'file'
            },
            
            # Command not found
            'command_not_found': {
                'patterns': [
                    r'command not found',
                    r'not found in path',
                    r'no such command',
                    r'unknown command'
                ],
                'summary': 'Command not found',
                'solution': 'The command is not installed. Install it with: sudo pacman -S [package]',
                'category': 'command'
            },
            
            # Package errors
            'package_not_found': {
                'patterns': [
                    r'target not found',
                    r'package .* was not found',
                    r'unable to locate package',
                    r'no package found'
                ],
                'summary': 'Package not found',
                'solution': 'The package name might be incorrect. Search with: pacman -Ss [keyword]',
                'category': 'package'
            },
            
            # Disk space errors
            'disk_full': {
                'patterns': [
                    r'no space left on device',
                    r'disk full',
                    r'not enough space',
                    r'insufficient space'
                ],
                'summary': 'Insufficient disk space',
                'solution': 'Free up disk space. Check usage with: df -h. Clean cache: sudo pacman -Sc',
                'category': 'disk'
            },
            
            # Network errors
            'network_error': {
                'patterns': [
                    r'connection refused',
                    r'network unreachable',
                    r'could not resolve host',
                    r'no route to host',
                    r'connection timed out',
                    r'failed to fetch'
                ],
                'summary': 'Network connection error',
                'solution': 'Check your internet connection. Verify with: ping 8.8.8.8',
                'category': 'network'
            },
            
            # Process errors
            'process_not_found': {
                'patterns': [
                    r'no process found',
                    r'no matching process',
                    r'process does not exist'
                ],
                'summary': 'Process not found',
                'solution': 'The process is not running. Check running processes with: ps aux | grep [name]',
                'category': 'process'
            },
            
            # Already running
            'already_running': {
                'patterns': [
                    r'already running',
                    r'address already in use',
                    r'port already in use',
                    r'resource busy'
                ],
                'summary': 'Resource already in use',
                'solution': 'The application or port is already in use. Kill the process first.',
                'category': 'resource'
            },
            
            # Syntax errors
            'syntax_error': {
                'patterns': [
                    r'syntax error',
                    r'invalid syntax',
                    r'unexpected token',
                    r'parse error'
                ],
                'summary': 'Command syntax error',
                'solution': 'Check the command syntax. Use --help flag for usage information.',
                'category': 'syntax'
            },
            
            # Missing dependency
            'missing_dependency': {
                'patterns': [
                    r'missing dependency',
                    r'requires .* but',
                    r'dependency not satisfied',
                    r'unmet dependencies'
                ],
                'summary': 'Missing dependencies',
                'solution': 'Install missing dependencies. Try: sudo pacman -S [dependency]',
                'category': 'dependency'
            },
            
            # Timeout errors
            'timeout': {
                'patterns': [
                    r'timeout',
                    r'timed out',
                    r'operation timed out'
                ],
                'summary': 'Operation timed out',
                'solution': 'The operation took too long. Check your connection or try again.',
                'category': 'timeout'
            },
            
            # Lock errors
            'lock_error': {
                'patterns': [
                    r'unable to lock database',
                    r'database is locked',
                    r'could not get lock',
                    r'lock file exists'
                ],
                'summary': 'Database locked',
                'solution': 'Another package manager is running. Wait or kill it: sudo killall pacman',
                'category': 'lock'
            },
            
            # Invalid argument
            'invalid_argument': {
                'patterns': [
                    r'invalid argument',
                    r'invalid option',
                    r'unrecognized option',
                    r'illegal option'
                ],
                'summary': 'Invalid command argument',
                'solution': 'Check the command syntax. Use --help to see available options.',
                'category': 'argument'
            },
            
            # Directory not empty
            'directory_not_empty': {
                'patterns': [
                    r'directory not empty',
                    r'cannot remove.*directory not empty'
                ],
                'summary': 'Directory not empty',
                'solution': 'Use rm -r to remove non-empty directories, or empty it first.',
                'category': 'file'
            },
            
            # Read-only filesystem
            'readonly_filesystem': {
                'patterns': [
                    r'read-only file system',
                    r'readonly filesystem'
                ],
                'summary': 'Read-only filesystem',
                'solution': 'The filesystem is mounted as read-only. Remount with: sudo mount -o remount,rw /',
                'category': 'filesystem'
            },
            
            # GPU errors
            'gpu_error': {
                'patterns': [
                    r'cuda error',
                    r'gpu not found',
                    r'nvidia driver',
                    r'opencl error'
                ],
                'summary': 'GPU/Driver error',
                'solution': 'Check GPU drivers. For NVIDIA: nvidia-smi. Reinstall drivers if needed.',
                'category': 'gpu'
            },
            
            # Memory errors
            'memory_error': {
                'patterns': [
                    r'out of memory',
                    r'cannot allocate memory',
                    r'memory exhausted'
                ],
                'summary': 'Insufficient memory',
                'solution': 'Not enough RAM. Close some applications or increase swap space.',
                'category': 'memory'
            }
        }
    
    def analyze_error(self, error_output: str, command: str = "") -> Dict:
        """
        Analyze error output and provide intelligent solution
        
        Args:
            error_output: The error message from command execution
            command: The command that failed (optional)
        
        Returns:
            Dict with summary, solution, and category
        """
        if not error_output:
            return {
                'summary': 'Command failed',
                'solution': 'No error details available. Try running with verbose flag.',
                'category': 'unknown',
                'original_error': ''
            }
        
        error_lower = error_output.lower()
        
        # Check each error pattern
        for error_type, error_info in self.error_patterns.items():
            for pattern in error_info['patterns']:
                if re.search(pattern, error_lower):
                    return {
                        'summary': error_info['summary'],
                        'solution': error_info['solution'],
                        'category': error_info['category'],
                        'original_error': error_output.strip()[:200]  # First 200 chars
                    }
        
        # If no pattern matched, provide generic response
        return {
            'summary': 'Command execution failed',
            'solution': self._generate_generic_solution(command, error_output),
            'category': 'unknown',
            'original_error': error_output.strip()[:200]
        }
    
    def _generate_generic_solution(self, command: str, error: str) -> str:
        """Generate generic solution based on command and error"""
        solutions = []
        
        # Check command type
        if command:
            if command.startswith('sudo'):
                solutions.append('Verify you have sudo privileges.')
            if 'pacman' in command:
                solutions.append('Try updating package database: sudo pacman -Sy')
            if 'systemctl' in command:
                solutions.append('Check service status: systemctl status [service]')
            if any(cmd in command for cmd in ['rm', 'mv', 'cp']):
                solutions.append('Verify file paths and permissions.')
        
        # Check error content
        if 'failed' in error.lower():
            solutions.append('Check the command syntax and try again.')
        if 'error' in error.lower():
            solutions.append('Review the error message for specific details.')
        
        if solutions:
            return ' '.join(solutions)
        
        return 'Check the command syntax and error details. Use --help for usage information.'
    
    def format_error_message(self, analysis: Dict, command: str = "") -> str:
        """
        Format error analysis into user-friendly message
        
        Args:
            analysis: Error analysis dict
            command: The failed command
        
        Returns:
            Formatted error message
        """
        message_parts = []
        
        # Add summary
        message_parts.append(f"❌ {analysis['summary']}")
        
        # Add command if provided
        if command:
            message_parts.append(f"\n📝 Command: {command}")
        
        # Add original error (truncated)
        if analysis.get('original_error'):
            error_preview = analysis['original_error'][:150]
            if len(analysis['original_error']) > 150:
                error_preview += "..."
            message_parts.append(f"\n⚠️  Error: {error_preview}")
        
        # Add solution
        message_parts.append(f"\n💡 Solution: {analysis['solution']}")
        
        return '\n'.join(message_parts)
    
    def get_quick_fix(self, error_category: str, command: str = "") -> Optional[str]:
        """
        Get a quick fix command for common errors
        
        Args:
            error_category: Category of error
            command: Original command
        
        Returns:
            Quick fix command or None
        """
        quick_fixes = {
            'permission': f'sudo {command}' if command else None,
            'package': 'pacman -Ss [package_name]',
            'lock': 'sudo rm /var/lib/pacman/db.lck',
            'network': 'ping -c 3 8.8.8.8',
            'disk': 'df -h && sudo pacman -Sc',
            'process': 'ps aux | grep [process_name]'
        }
        
        return quick_fixes.get(error_category)


# Singleton instance
_error_analyzer = None

def get_error_analyzer() -> ErrorAnalyzer:
    """Get singleton ErrorAnalyzer instance"""
    global _error_analyzer
    if _error_analyzer is None:
        _error_analyzer = ErrorAnalyzer()
    return _error_analyzer
