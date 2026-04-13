"""
Unit tests for security utilities.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'web_app' / 'backend'))

from utils.input_validation import (
    validate_password,
    validate_ip_address,
    is_public_ip,
    validate_log_content,
    sanitize_log_line,
    validate_username,
)


class TestPasswordValidation:
    """Tests for password validation."""
    
    def test_valid_password(self):
        """Test valid password."""
        is_valid, msg = validate_password('SecurePass123!')
        assert is_valid == True
        assert msg == "Password is valid"
    
    def test_password_too_short(self):
        """Test password too short."""
        is_valid, msg = validate_password('Short1!')
        assert is_valid == False
        assert "12 characters" in msg
    
    def test_password_too_long(self):
        """Test password too long."""
        is_valid, msg = validate_password('A' * 150 + '1!')
        assert is_valid == False
        assert "128 characters" in msg
    
    def test_password_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, msg = validate_password('lowercase123!')
        assert is_valid == False
        assert "uppercase" in msg
    
    def test_password_no_lowercase(self):
        """Test password without lowercase."""
        is_valid, msg = validate_password('UPPERCASE123!')
        assert is_valid == False
        assert "lowercase" in msg
    
    def test_password_no_digit(self):
        """Test password without digit."""
        is_valid, msg = validate_password('NoDigits!')
        assert is_valid == False
        assert "digit" in msg
    
    def test_password_no_special(self):
        """Test password without special character."""
        is_valid, msg = validate_password('NoSpecial123')
        assert is_valid == False
        assert "special" in msg
    
    def test_password_empty(self):
        """Test empty password."""
        is_valid, msg = validate_password('')
        assert is_valid == False
        assert "empty" in msg
    
    def test_password_common_pattern(self):
        """Test password with common pattern."""
        is_valid, msg = validate_password('Password123!')
        assert is_valid == False
        assert "common pattern" in msg.lower()


class TestIPAddressValidation:
    """Tests for IP address validation."""
    
    def test_valid_ipv4(self):
        """Test valid IPv4 address."""
        is_valid, msg = validate_ip_address('8.8.8.8')
        assert is_valid == True
    
    def test_valid_ipv6(self):
        """Test valid IPv6 address."""
        is_valid, msg = validate_ip_address('2001:4860:4860::8888')
        assert is_valid == True
    
    def test_invalid_ip(self):
        """Test invalid IP address."""
        is_valid, msg = validate_ip_address('invalid')
        assert is_valid == False
    
    def test_is_public_ip(self):
        """Test public IP detection."""
        # Public IPs
        assert is_public_ip('8.8.8.8') == True
        assert is_public_ip('1.1.1.1') == True
        
        # Private IPs
        assert is_public_ip('192.168.1.1') == False
        assert is_public_ip('10.0.0.1') == False
        assert is_public_ip('172.16.0.1') == False
        
        # Localhost
        assert is_public_ip('127.0.0.1') == False
        
        # Invalid
        assert is_public_ip('invalid') == False


class TestLogContentValidation:
    """Tests for log content validation."""
    
    def test_valid_content(self):
        """Test valid log content."""
        content = "date=2024-01-15 time=10:30:00 user=test"
        is_valid, msg = validate_log_content(content)
        assert is_valid == True
    
    def test_empty_content(self):
        """Test empty log content."""
        is_valid, msg = validate_log_content('')
        assert is_valid == False
        assert "empty" in msg.lower()
    
    def test_null_bytes(self):
        """Test content with null bytes."""
        content = "date=2024-01-15\x00time=10:30:00"
        is_valid, msg = validate_log_content(content)
        assert is_valid == False
        assert "null" in msg.lower()
    
    def test_suspicious_patterns(self):
        """Test content with suspicious patterns."""
        content = '<script>alert("xss")</script>'
        is_valid, msg = validate_log_content(content)
        assert is_valid == False
        assert "suspicious" in msg.lower()
    
    def test_sanitize_log_line(self):
        """Test log line sanitization."""
        # Normal line
        line = "date=2024-01-15 time=10:30:00"
        assert sanitize_log_line(line) == line
        
        # Long line
        long_line = "a" * 20000
        sanitized = sanitize_log_line(long_line)
        assert len(sanitized) < len(long_line)
        assert "truncated" in sanitized.lower()


class TestUsernameValidation:
    """Tests for username validation."""
    
    def test_valid_username(self):
        """Test valid username."""
        is_valid, msg = validate_username('john.doe')
        assert is_valid == True
    
    def test_valid_username_with_underscore(self):
        """Test valid username with underscore."""
        is_valid, msg = validate_username('john_doe')
        assert is_valid == True
    
    def test_valid_username_with_hyphen(self):
        """Test valid username with hyphen."""
        is_valid, msg = validate_username('john-doe')
        assert is_valid == True
    
    def test_username_too_short(self):
        """Test username too short."""
        is_valid, msg = validate_username('ab')
        assert is_valid == False
        assert "3 characters" in msg
    
    def test_username_too_long(self):
        """Test username too long."""
        is_valid, msg = validate_username('a' * 100)
        assert is_valid == False
        assert "64 characters" in msg
    
    def test_username_empty(self):
        """Test empty username."""
        is_valid, msg = validate_username('')
        assert is_valid == False
        assert "empty" in msg.lower()
    
    def test_username_special_start(self):
        """Test username starting with special character."""
        is_valid, msg = validate_username('.john')
        assert is_valid == False
        assert "special" in msg.lower()
    
    def test_username_invalid_chars(self):
        """Test username with invalid characters."""
        is_valid, msg = validate_username('john@doe')
        assert is_valid == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
