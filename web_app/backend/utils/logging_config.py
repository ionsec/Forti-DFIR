"""
Logging configuration for Forti-DFIR.

This module provides structured logging setup with support for
console and file output.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str,
    level: str = 'INFO',
    log_file: Optional[str] = None,
    log_dir: str = 'logs'
) -> logging.Logger:
    """Configure and return a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_dir: Directory for log files (default: 'logs')
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create formatter with structured output
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"module": "%(module)s", "function": "%(funcName)s", '
        '"line": %(lineno)d, "message": "%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        file_path = log_path / log_file
        file_handler = logging.FileHandler(str(file_path))
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class SecurityLogger:
    """Logger specifically for security events.
    
    Provides methods for logging authentication attempts,
    access control, and security violations.
    """
    
    def __init__(self, name: str = 'security'):
        """Initialize security logger.
        
        Args:
            name: Logger name
        """
        self.logger = setup_logger(name, level='INFO', log_file='security.log')
    
    def log_login_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool,
        reason: str = None
    ) -> None:
        """Log a login attempt.
        
        Args:
            username: Attempted username
            ip_address: Client IP address
            success: Whether login was successful
            reason: Failure reason (if applicable)
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Login {status} - User: {username}, IP: {ip_address}"
        if reason:
            message += f", Reason: {reason}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.warning(message)
    
    def log_file_upload(
        self,
        username: str,
        filename: str,
        size: int,
        ip_address: str
    ) -> None:
        """Log a file upload event.
        
        Args:
            username: User who uploaded the file
            filename: Name of uploaded file
            size: File size in bytes
            ip_address: Client IP address
        """
        self.logger.info(
            f"File upload - User: {username}, File: {filename}, "
            f"Size: {size} bytes, IP: {ip_address}"
        )
    
    def log_download(
        self,
        username: str,
        filename: str,
        ip_address: str
    ) -> None:
        """Log a file download event.
        
        Args:
            username: User who downloaded the file
            filename: Name of downloaded file
            ip_address: Client IP address
        """
        self.logger.info(
            f"File download - User: {username}, File: {filename}, IP: {ip_address}"
        )
    
    def log_security_violation(
        self,
        violation_type: str,
        username: str,
        ip_address: str,
        details: str = None
    ) -> None:
        """Log a security violation.
        
        Args:
            violation_type: Type of violation
            username: User involved (if applicable)
            ip_address: Client IP address
            details: Additional details
        """
        message = f"Security violation - Type: {violation_type}, User: {username}, IP: {ip_address}"
        if details:
            message += f", Details: {details}"
        self.logger.error(message)
    
    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        endpoint: str,
        limit: str
    ) -> None:
        """Log rate limit exceeded event.
        
        Args:
            ip_address: Client IP address
            endpoint: Endpoint that was rate limited
            limit: Rate limit that was exceeded
        """
        self.logger.warning(
            f"Rate limit exceeded - IP: {ip_address}, Endpoint: {endpoint}, Limit: {limit}"
        )


# Convenience function to get security logger
def get_security_logger() -> SecurityLogger:
    """Get a security logger instance.
    
    Returns:
        SecurityLogger instance
    """
    return SecurityLogger()
