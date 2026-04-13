"""
Configuration module for Forti-DFIR web application.

This module provides secure configuration management with environment
variable validation and production defaults.
"""

import os
import secrets
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """Application configuration with secure defaults.
    
    Attributes:
        SECRET_KEY: Flask secret key for session management
        JWT_SECRET_KEY: JWT signing key
        JWT_ACCESS_TOKEN_EXPIRES: Token expiration time in hours
        MAX_CONTENT_LENGTH: Maximum file upload size in bytes
        UPLOAD_FOLDER: Directory for uploaded files
        CORS_ORIGINS: Allowed CORS origins
        REDIS_URL: Redis connection URL
        CELERY_BROKER_URL: Celery broker URL
        DEBUG: Debug mode flag
        TESTING: Testing mode flag
    """
    
    SECRET_KEY: str = field(default_factory=lambda: os.environ.get('SECRET_KEY', ''))
    JWT_SECRET_KEY: str = field(default_factory=lambda: os.environ.get('JWT_SECRET_KEY', ''))
    JWT_ACCESS_TOKEN_EXPIRES: int = 24  # hours
    MAX_CONTENT_LENGTH: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER: str = 'uploads'
    CORS_ORIGINS: list = field(default_factory=lambda: os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(','))
    REDIS_URL: str = field(default_factory=lambda: os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    CELERY_BROKER_URL: str = field(default_factory=lambda: os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
    DEBUG: bool = field(default_factory=lambda: os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
    TESTING: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.SECRET_KEY:
            if self.is_production():
                raise ValueError("SECRET_KEY environment variable is required in production")
            # Generate a temporary key for development only
            self.SECRET_KEY = 'dev-secret-key-change-in-production'
            print("WARNING: Using development SECRET_KEY. Set SECRET_KEY environment variable for production!")
        
        if not self.JWT_SECRET_KEY:
            if self.is_production():
                raise ValueError("JWT_SECRET_KEY environment variable is required in production")
            # Generate a temporary key for development only
            self.JWT_SECRET_KEY = 'dev-jwt-secret-change-in-production'
            print("WARNING: Using development JWT_SECRET_KEY. Set JWT_SECRET_KEY environment variable for production!")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode.
        
        Returns:
            True if FLASK_ENV is 'production', False otherwise.
        """
        return os.environ.get('FLASK_ENV', 'development').lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode.
        
        Returns:
            True if FLASK_ENV is 'development' or not set, False otherwise.
        """
        return not cls.is_production()
    
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a secure random secret key.
        
        Args:
            length: Number of bytes for the key (default: 32)
            
        Returns:
            Hexadecimal string representation of the key
        """
        return secrets.token_hex(length)
    
    def to_flask_config(self) -> dict:
        """Convert to Flask configuration dictionary.
        
        Returns:
            Dictionary of Flask configuration values
        """
        return {
            'SECRET_KEY': self.SECRET_KEY,
            'JWT_SECRET_KEY': self.JWT_SECRET_KEY,
            'JWT_ACCESS_TOKEN_EXPIRES': self.JWT_ACCESS_TOKEN_EXPIRES,
            'MAX_CONTENT_LENGTH': self.MAX_CONTENT_LENGTH,
            'UPLOAD_FOLDER': self.UPLOAD_FOLDER,
            'DEBUG': self.DEBUG,
            'TESTING': self.TESTING,
        }
    
    def to_celery_config(self) -> dict:
        """Convert to Celery configuration dictionary.
        
        Returns:
            Dictionary of Celery configuration values
        """
        return {
            'CELERY_BROKER_URL': self.CELERY_BROKER_URL,
            'CELERY_RESULT_BACKEND': self.REDIS_URL,
        }


@dataclass
class SecurityConfig:
    """Security-related configuration.
    
    Attributes:
        SESSION_COOKIE_SECURE: Whether to use secure cookies
        SESSION_COOKIE_HTTPONLY: Whether to set httpOnly flag
        SESSION_COOKIE_SAMESITE: SameSite policy for cookies
        RATELIMIT_STORAGE_URL: Storage URL for rate limiting
        RATELIMIT_DEFAULT: Default rate limit
        RATELIMIT_LOGIN: Rate limit for login endpoint
    """
    
    SESSION_COOKIE_SECURE: bool = field(default_factory=lambda: Config.is_production())
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Strict'
    
    RATELIMIT_STORAGE_URL: str = field(default_factory=lambda: os.environ.get('REDIS_URL', 'redis://localhost:6379/1'))
    RATELIMIT_DEFAULT: str = "200 per day;50 per hour"
    RATELIMIT_LOGIN: str = "5 per minute"
    RATELIMIT_PARSE: str = "10 per minute"


def get_config() -> Config:
    """Get the application configuration.
    
    Returns:
        Config instance with validated settings
    """
    return Config()


def get_security_config() -> SecurityConfig:
    """Get the security configuration.
    
    Returns:
        SecurityConfig instance
    """
    return SecurityConfig()


# Example usage and key generation
if __name__ == '__main__':
    print("Forti-DFIR Configuration Generator")
    print("=" * 40)
    print("\nGenerate secure keys for production:")
    print(f"SECRET_KEY={Config.generate_secret_key()}")
    print(f"JWT_SECRET_KEY={Config.generate_secret_key()}")
    print("\nConfiguration validation:")
    config = get_config()
    print(f"Production mode: {config.is_production()}")
    print(f"Development mode: {config.is_development()}")
