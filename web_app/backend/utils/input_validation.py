"""
Input validation utilities for Forti-DFIR.

This module provides validation functions for passwords, IP addresses,
and log content.
"""

import re
import ipaddress
from typing import Tuple, Optional


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password meets security requirements.
    
    Requirements:
    - Minimum 12 characters
    - Maximum 128 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    common_patterns = [
        r'password',
        r'123456',
        r'qwerty',
        r'admin',
        r'letmein',
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password, re.IGNORECASE):
            return False, f"Password contains common pattern: {pattern}"
    
    return True, "Password is valid"


def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
    """Validate IP address format.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return True, None
    except ValueError as e:
        return False, str(e)


def is_public_ip(ip: str) -> bool:
    """Check if an IP address is public (not private/local).
    
    Args:
        ip: IP address string
        
    Returns:
        True if IP is public, False otherwise
    """
    try:
        return not ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def validate_log_content(content: str, max_size: int = 100 * 1024 * 1024) -> Tuple[bool, str]:
    """Validate log file content.
    
    Args:
        content: Log file content string
        max_size: Maximum allowed size in bytes (default: 100MB)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content:
        return False, "Log content is empty"
    
    # Check size
    if len(content) > max_size:
        return False, f"Log content exceeds maximum size ({max_size} bytes)"
    
    # Remove null bytes (potential attack)
    if '\x00' in content:
        return False, "Log content contains null bytes (potential attack)"
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'data:text/html',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False, f"Log content contains suspicious pattern: {pattern}"
    
    return True, "Log content is valid"


def sanitize_log_line(line: str, max_length: int = 10000) -> str:
    """Sanitize a single log line.
    
    Args:
        line: Log line string
        max_length: Maximum allowed line length
        
    Returns:
        Sanitized log line
    """
    if not line:
        return ""
    
    # Truncate long lines
    if len(line) > max_length:
        line = line[:max_length] + "...[truncated]"
    
    # Remove control characters except newline and tab
    line = ''.join(char for char in line if ord(char) >= 32 or char in '\n\t')
    
    return line.strip()


def validate_username(username: str, min_length: int = 3, max_length: int = 64) -> Tuple[bool, str]:
    """Validate username format.
    
    Args:
        username: Username to validate
        min_length: Minimum length (default: 3)
        max_length: Maximum length (default: 64)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    username = username.strip()
    
    if len(username) < min_length:
        return False, f"Username must be at least {min_length} characters"
    
    if len(username) > max_length:
        return False, f"Username must be less than {max_length} characters"
    
    # Allow alphanumeric, underscore, hyphen, and dot
    if not re.match(r'^[\w\-\.]+$', username):
        return False, "Username can only contain letters, numbers, underscore, hyphen, and dot"
    
    # Don't allow username to start/end with special characters
    if username[0] in '.-_':
        return False, "Username cannot start with special characters"
    
    if username[-1] in '.-_':
        return False, "Username cannot end with special characters"
    
    return True, "Username is valid"
