.. _security:

Security Guide
==============

This document outlines security best practices and considerations for Forti-DFIR.

Authentication Security
----------------------

JWT Token Management
~~~~~~~~~~~~~~~~~~~~

Forti-DFIR uses JSON Web Tokens (JWT) for authentication. Follow these practices:

.. code-block:: python

   # Production configuration
   app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']  # REQUIRED
   app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Short expiry
   app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)  # Refresh token

Token Storage
~~~~~~~~~~~~~

.. danger::

   Never store JWT tokens in ``localStorage`` as it's vulnerable to XSS attacks.

Recommended approach using httpOnly cookies:

.. code-block:: python

   from flask import make_response
   
   @app.route('/api/auth/login', methods=['POST'])
   def login():
       # ... authentication logic ...
       access_token = create_access_token(identity=username)
       
       response = make_response(jsonify({'status': 'success'}))
       response.set_cookie(
           'access_token',
           access_token,
           httponly=True,
           secure=True,  # HTTPS only
           samesite='Strict',
           max_age=3600  # 1 hour
       )
       return response

Password Security
-----------------

Password Hashing
~~~~~~~~~~~~~~~~

Forti-DFIR uses Werkzeug's password hashing:

.. code-block:: python

   from werkzeug.security import generate_password_hash, check_password_hash
   import secrets
   
   # Generate secure password hash
   hashed = generate_password_hash(
       password,
       method='scrypt',  # Use scrypt for better security
       salt_length=16
   )

Password Policy Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import re
   from typing import Tuple
   
   def validate_password(password: str) -> Tuple[bool, str]:
       """Validate password meets security requirements."""
       if len(password) < 12:
           return False, "Password must be at least 12 characters"
       if len(password) > 128:
           return False, "Password must be less than 128 characters"
       if not re.search(r'[A-Z]', password):
           return False, "Password must contain uppercase letters"
       if not re.search(r'[a-z]', password):
           return False, "Password must contain lowercase letters"
       if not re.search(r'\d', password):
           return False, "Password must contain digits"
       if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
           return False, "Password must contain special characters"
       return True, "Password valid"

File Upload Security
--------------------

Validation Checklist
~~~~~~~~~~~~~~~~~~~~

1. **File Type Validation**

   .. code-block:: python

      ALLOWED_EXTENSIONS = {'txt', 'log', 'csv'}
      ALLOWED_MIME_TYPES = {'text/plain', 'text/csv', 'application/octet-stream'}
      
      def validate_file(file) -> Tuple[bool, str]:
          ext = file.filename.rsplit('.', 1)[1].lower()
          if ext not in ALLOWED_EXTENSIONS:
              return False, f"File type .{ext} not allowed"
          return True, "Valid"

2. **File Size Limits**

   .. code-block:: python

      MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
      
      # In Flask config
      app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

3. **Filename Sanitization**

   .. code-block:: python

      from werkzeug.utils import secure_filename
      import uuid
      
      def safe_filename(filename: str) -> str:
          """Generate safe, unique filename."""
          safe = secure_filename(filename)
          ext = safe.rsplit('.', 1)[1].lower()
          return f"{uuid.uuid4()}.{ext}"

4. **Path Traversal Prevention**

   .. code-block:: python

      import os
      from pathlib import Path
      
      UPLOAD_FOLDER = Path('uploads').resolve()
      
      def safe_path(filename: str) -> Path:
          """Ensure file path is within allowed directory."""
          filepath = UPLOAD_FOLDER / filename
          try:
              filepath.resolve().relative_to(UPLOAD_FOLDER)
          except ValueError:
              raise SecurityError("Path traversal attempt detected")
          return filepath

Rate Limiting
-------------

Forti-DFIR implements rate limiting using flask-limiter:

.. code-block:: python

   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address
   
   limiter = Limiter(
       app=app,
       key_func=get_remote_address,
       default_limits=["200 per day", "50 per hour"],
       storage_uri="redis://localhost:6379"
   )
   
   # Stricter limits for authentication
   @app.route('/api/auth/login', methods=['POST'])
   @limiter.limit("5 per minute")
   def login():
       ...

Input Validation
----------------

All user input must be validated and sanitized:

.. code-block:: python

   import re
   from typing import Optional
   
   def sanitize_username(username: str) -> Optional[str]:
       """Sanitize username input."""
       if not username or len(username) > 64:
           return None
       
       # Allow alphanumeric, underscore, hyphen, dot
       if not re.match(r'^[\w\-\.]+$', username):
           return None
       
       return username.strip().lower()
   
   def sanitize_log_content(content: str) -> str:
       """Sanitize log file content."""
       # Remove null bytes
       content = content.replace('\x00', '')
       
       # Limit length
       if len(content) > 100 * 1024 * 1024:  # 100MB
           raise ValueError("Content exceeds maximum size")
       
       return content

CORS Configuration
------------------

Configure CORS properly for production:

.. code-block:: python

   from flask_cors import CORS
   
   # Development
   CORS(app, origins=['http://localhost:3000'])
   
   # Production
   allowed_origins = os.environ.get('CORS_ORIGINS', '').split(',')
   CORS(app, origins=allowed_origins, supports_credentials=True)

Security Headers
----------------

Use flask-talisman for security headers:

.. code-block:: python

   from flask_talisman import Talisman
   
   # Production configuration
   csp = {
       'default-src': "'self'",
       'script-src': "'self'",
       'style-src': "'self' 'unsafe-inline'",
       'img-src': "'self' data:",
       'font-src': "'self'",
   }
   
   Talisman(app,
       content_security_policy=csp,
       force_https=True,
       strict_transport_security=True,
       session_cookie_secure=True,
       session_cookie_http_only=True
   )

Environment Variables
---------------------

Required environment variables for production:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Variable
     - Description
   * - SECRET_KEY
     - Flask secret key (32+ random characters)
   * - JWT_SECRET_KEY
     - JWT signing key (32+ random characters)
   * - DATABASE_URL
     - Database connection string
   * - REDIS_URL
     - Redis connection string
   * - FLASK_ENV
     - Set to 'production'
   * - CORS_ORIGINS
     - Comma-separated allowed origins

Generating Secure Keys
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import secrets
   
   # Generate secure random keys
   secret_key = secrets.token_hex(32)
   jwt_secret = secrets.token_hex(32)
   
   print(f"SECRET_KEY={secret_key}")
   print(f"JWT_SECRET_KEY={jwt_secret}")

Security Audit Checklist
------------------------

Before deploying to production:

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - ☐
     - All default credentials removed
   * - ☐
     - Strong SECRET_KEY set via environment variable
   * - ☐
     - Strong JWT_SECRET_KEY set via environment variable
   * - ☐
     - Debug mode disabled (FLASK_DEBUG=False)
   * - ☐
     - HTTPS enforced
   * - ☐
     - CORS configured for production origins only
   * - ☐
     - Rate limiting enabled
   * - ☐
     - File upload limits configured
   * - ☐
     - Input validation on all endpoints
   * - ☐
     - Security headers configured
   * - ☐
     - Authentication logging enabled
   * - ☐
     - No sensitive data in logs
   * - ☐
     - Dependencies updated (no known vulnerabilities)
   * - ☐
     - Container security configured (if using Docker)
   * - ☐
     - Network segmentation in place

Reporting Security Issues
-------------------------

If you discover a security vulnerability, please report it responsibly:

1. Email: security@ionsec.com
2. Include: Description, steps to reproduce, potential impact
3. Allow: 90 days for fix before disclosure
