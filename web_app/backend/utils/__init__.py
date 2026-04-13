"""
Utils package for Forti-DFIR.

This package provides security utilities, input validation, and logging.
"""

from .security import (
    sanitize_filename,
    sanitize_username,
    validate_file_type,
    secure_save_file,
    get_secure_headers,
    is_safe_path,
    SecurityError,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
)

from .input_validation import (
    validate_password,
    validate_ip_address,
    is_public_ip,
    validate_log_content,
    sanitize_log_line,
    validate_username,
)

from .logging_config import (
    setup_logger,
    SecurityLogger,
    get_security_logger,
)

__all__ = [
    # Security
    'sanitize_filename',
    'sanitize_username',
    'validate_file_type',
    'secure_save_file',
    'get_secure_headers',
    'is_safe_path',
    'SecurityError',
    'ALLOWED_EXTENSIONS',
    'ALLOWED_MIME_TYPES',
    'MAX_FILE_SIZE',
    # Input validation
    'validate_password',
    'validate_ip_address',
    'is_public_ip',
    'validate_log_content',
    'sanitize_log_line',
    'validate_username',
    # Logging
    'setup_logger',
    'SecurityLogger',
    'get_security_logger',
]
