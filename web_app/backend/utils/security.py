"""
Security utilities for Forti-DFIR web application.

This module provides security-related functions for input validation,
file handling, and protection against common web vulnerabilities.
"""

import os
import re
import uuid
import magic
from pathlib import Path
from typing import Optional, Tuple, Set
from werkzeug.utils import secure_filename as werkzeug_secure_filename


# Allowed file extensions
ALLOWED_EXTENSIONS: Set[str] = {'txt', 'log', 'csv'}
# Allowed MIME types
ALLOWED_MIME_TYPES: Set[str] = {
    'text/plain',
    'text/csv',
    'application/octet-stream',
    'text/x-log',
}
# Maximum file size (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent directory traversal attacks.
    
    This function uses werkzeug's secure_filename and adds additional
    safety measures.
    
    Args:
        filename: The original filename to sanitize
        
    Returns:
        Sanitized filename safe for filesystem use
        
    Raises:
        ValueError: If filename is empty or contains invalid characters
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Use werkzeug's secure_filename as base
    safe = werkzeug_secure_filename(filename)
    
    if not safe:
        raise ValueError("Invalid filename after sanitization")
    
    # Additional safety: remove any remaining dangerous characters
    safe = re.sub(r'[<>"\'\`\|\?\*\{\}\[\]\(\)\$;!]', '', safe)
    
    # Ensure filename doesn't start with a dot (hidden files)
    while safe.startswith('.'):
        safe = safe[1:]
    
    if not safe:
        raise ValueError("Filename became empty after sanitization")
    
    return safe


def sanitize_username(username: str, max_length: int = 64) -> Optional[str]:
    """Sanitize and validate a username input.
    
    Removes dangerous characters and validates format.
    
    Args:
        username: Raw username string
        max_length: Maximum allowed length (default: 64)
        
    Returns:
        Sanitized username or None if invalid
    """
    if not username:
        return None
    
    # Strip whitespace
    username = username.strip()
    
    # Check length
    if len(username) > max_length:
        return None
    
    # Remove dangerous characters
    username = re.sub(r'[<>"\'\`\[\]{}()$;]', '', username)
    
    # Validate alphanumeric with limited special chars
    if not re.match(r'^[\w\-\.]+$', username):
        return None
    
    return username


def validate_file_type(file_path: str, filename: str) -> Tuple[bool, str]:
    """Validate file type by extension and MIME type.
    
    Args:
        file_path: Path to the file to validate
        filename: Original filename for extension check
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check extension
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type .{ext} is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check MIME type using python-magic
    try:
        mime = magic.Magic(mime=True)
        detected_type = mime.from_file(file_path)
        
        # Some systems report CSV as text/plain
        if detected_type not in ALLOWED_MIME_TYPES:
            return False, f"Detected file type '{detected_type}' is not allowed"
    except Exception as e:
        # If magic is not available, fall back to extension only
        pass
    
    return True, ""


def secure_save_file(file, upload_dir: str, prefix: str = '') -> Tuple[str, str]:
    """Securely save an uploaded file.
    
    This function:
    1. Generates a unique filename using UUID
    2. Validates the file type
    3. Ensures the upload directory exists
    4. Saves the file with size validation
    
    Args:
        file: Flask FileStorage object
        upload_dir: Directory to save the file
        prefix: Optional prefix for the filename
        
    Returns:
        Tuple of (filepath, original_filename)
        
    Raises:
        ValueError: If file validation fails
        IOError: If file cannot be saved
    """
    # Get original filename and sanitize
    original_filename = file.filename
    safe_name = sanitize_filename(original_filename)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    ext = original_filename.rsplit('.', 1)[-1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type .{ext} not allowed")
    
    # Create filename with optional prefix
    if prefix:
        new_filename = f"{prefix}_{file_id}.{ext}"
    else:
        new_filename = f"{file_id}.{ext}"
    
    # Ensure upload directory exists
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    
    # Build full path
    filepath = upload_path / new_filename
    
    # Save file
    file.save(str(filepath))
    
    # Validate file size
    file_size = filepath.stat().st_size
    if file_size > MAX_FILE_SIZE:
        filepath.unlink()
        raise ValueError(f"File size ({file_size} bytes) exceeds maximum ({MAX_FILE_SIZE} bytes)")
    
    # Validate file type
    is_valid, error = validate_file_type(str(filepath), original_filename)
    if not is_valid:
        filepath.unlink()
        raise ValueError(error)
    
    return str(filepath), original_filename


def get_secure_headers() -> dict:
    """Get security headers for HTTP responses.
    
    Returns:
        Dictionary of security headers
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Check if a path is safe (within base directory).
    
    Prevents directory traversal attacks.
    
    Args:
        base_dir: Base directory that should contain the target
        target_path: Path to check
        
    Returns:
        True if path is within base_dir, False otherwise
    """
    try:
        target_path.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass
