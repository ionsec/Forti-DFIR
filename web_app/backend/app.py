"""
Forti-DFIR Web Application - Main Flask Application

This is the production-ready Flask application with security hardening,
proper configuration, and async processing support.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_talisman import Talisman
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Import configuration and utilities
from config import Config, get_config, get_security_config
from utils.security import (
    sanitize_filename,
    sanitize_username,
    secure_save_file,
    get_secure_headers,
    ALLOWED_EXTENSIONS,
)
from utils.input_validation import validate_password
from utils.logging_config import setup_logger, SecurityLogger
from log_parser_service import LogParserService
from csv_parser_service import CSVParserService
from celery import Celery

# Setup logging
logger = setup_logger(__name__, level='INFO', log_file='app.log')
security_logger = SecurityLogger()

# Initialize configuration
config = get_config()
security_config = get_security_config()

# Create Flask app
app = Flask(__name__)
app.config.update(config.to_flask_config())

# Security headers with Talisman
if Config.is_production():
    csp = {
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'",
        'connect-src': "'self'",
    }
    Talisman(app,
        content_security_policy=csp,
        force_https=True,
        strict_transport_security=True,
        session_cookie_secure=True,
        session_cookie_http_only=True)

# CORS configuration
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=cors_origins, supports_credentials=True)

# JWT setup
jwt = JWTManager(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[security_config.RATELIMIT_DEFAULT],
    storage_uri=security_config.RATELIMIT_STORAGE_URL,
)

# Celery setup
celery = Celery(app.name, broker=config.CELERY_BROKER_URL)
celery.conf.update(app.config)

# Create necessary directories
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path('results').mkdir(parents=True, exist_ok=True)

# User store - In production, use a database with proper password hashing
# This is a placeholder that should be replaced with a database
users_db: Dict[str, Dict[str, Any]] = {}

# Check for initial admin user from environment
def init_admin_user() -> None:
    """Initialize admin user from environment variables if provided."""
    admin_user = os.environ.get('ADMIN_USER')
    admin_pass = os.environ.get('ADMIN_PASSWORD')
    
    if admin_user and admin_pass:
        # Validate password strength
        is_valid, msg = validate_password(admin_pass)
        if is_valid:
            users_db[admin_user] = {
                'password_hash': generate_password_hash(admin_pass),
                'created_at': datetime.utcnow().isoformat(),
                'is_admin': True
            }
            logger.info(f"Admin user '{admin_user}' initialized from environment")
        else:
            logger.warning(f"Admin password validation failed: {msg}")
            logger.warning("Admin user not created. Please set a stronger password.")
    else:
        logger.warning(
            "No admin credentials provided via environment variables. "
            "Set ADMIN_USER and ADMIN_PASSWORD for production."
        )

init_admin_user()

# Initialize services
log_parser = LogParserService()
csv_parser = CSVParserService()


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check() -> tuple:
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit(security_config.RATELIMIT_LOGIN)
def login() -> tuple:
    """Authenticate user and return JWT token."""
    data = request.get_json()
    
    if not data:
        security_logger.log_login_attempt('unknown', get_remote_address(), False, 'No data provided')
        return jsonify({'error': 'No data provided'}), 400
    
    username = sanitize_username(data.get('username', ''))
    password = data.get('password', '')
    
    if not username:
        security_logger.log_login_attempt('invalid', get_remote_address(), False, 'Invalid username format')
        return jsonify({'error': 'Invalid username format'}), 400
    
    if not password:
        security_logger.log_login_attempt(username, get_remote_address(), False, 'No password provided')
        return jsonify({'error': 'Password required'}), 400
    
    # Check credentials
    user = users_db.get(username)
    
    if user and check_password_hash(user['password_hash'], password):
        access_token = create_access_token(
            identity=username,
            expires_delta=timedelta(hours=config.JWT_ACCESS_TOKEN_EXPIRES)
        )
        security_logger.log_login_attempt(username, get_remote_address(), True)
        
        return jsonify({
            'access_token': access_token,
            'username': username,
            'expires_in': config.JWT_ACCESS_TOKEN_EXPIRES * 3600
        }), 200
    
    security_logger.log_login_attempt(username, get_remote_address(), False, 'Invalid credentials')
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("3 per hour")
@jwt_required()
def register() -> tuple:
    """Register a new user (admin only)."""
    current_user = get_jwt_identity()
    
    # Check if current user is admin
    if not users_db.get(current_user, {}).get('is_admin', False):
        security_logger.log_security_violation(
            'unauthorized_registration',
            current_user,
            get_remote_address(),
            'Non-admin attempted to register user'
        )
        return jsonify({'error': 'Admin privileges required'}), 403
    
    data = request.get_json()
    username = sanitize_username(data.get('username', ''))
    password = data.get('password', '')
    
    if not username:
        return jsonify({'error': 'Valid username required'}), 400
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    # Validate password
    is_valid, msg = validate_password(password)
    if not is_valid:
        return jsonify({'error': msg}), 400
    
    # Check if user exists
    if username in users_db:
        return jsonify({'error': 'User already exists'}), 409
    
    # Create user
    users_db[username] = {
        'password_hash': generate_password_hash(password),
        'created_at': datetime.utcnow().isoformat(),
        'is_admin': False
    }
    
    logger.info(f"User '{username}' registered by '{current_user}'")
    return jsonify({'message': f'User {username} created successfully'}), 201


@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token() -> tuple:
    """Verify JWT token validity."""
    current_user = get_jwt_identity()
    return jsonify({'valid': True, 'username': current_user}), 200


@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def change_password() -> tuple:
    """Change user password."""
    current_user = get_jwt_identity()
    data = request.get_json()
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Both old and new passwords required'}), 400
    
    # Verify old password
    user = users_db.get(current_user)
    if not user or not check_password_hash(user['password_hash'], old_password):
        return jsonify({'error': 'Invalid old password'}), 401
    
    # Validate new password
    is_valid, msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': msg}), 400
    
    # Update password
    users_db[current_user]['password_hash'] = generate_password_hash(new_password)
    users_db[current_user]['password_changed_at'] = datetime.utcnow().isoformat()
    
    logger.info(f"Password changed for user '{current_user}'")
    return jsonify({'message': 'Password changed successfully'}), 200


@app.route('/api/parse/vpn', methods=['POST'])
@jwt_required()
@limiter.limit(security_config.RATELIMIT_PARSE)
def parse_vpn() -> tuple:
    """Parse VPN logs with async processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filepath, original_name = secure_save_file(file, app.config['UPLOAD_FOLDER'])
            current_user = get_jwt_identity()
            
            security_logger.log_file_upload(
                current_user,
                original_name,
                os.path.getsize(filepath),
                get_remote_address()
            )
            
            task = process_vpn_logs.delay(filepath, current_user, original_name)
            
            return jsonify({
                'task_id': task.id,
                'status': 'processing',
                'message': 'VPN log parsing started'
            }), 202
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"VPN parse error: {e}")
            return jsonify({'error': 'Failed to process file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/parse/firewall', methods=['POST'])
@jwt_required()
@limiter.limit(security_config.RATELIMIT_PARSE)
def parse_firewall() -> tuple:
    """Parse firewall logs with async processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filepath, original_name = secure_save_file(file, app.config['UPLOAD_FOLDER'])
            current_user = get_jwt_identity()
            
            security_logger.log_file_upload(
                current_user,
                original_name,
                os.path.getsize(filepath),
                get_remote_address()
            )
            
            task = process_firewall_logs.delay(filepath, current_user, original_name)
            
            return jsonify({
                'task_id': task.id,
                'status': 'processing',
                'message': 'Firewall log parsing started'
            }), 202
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Firewall parse error: {e}")
            return jsonify({'error': 'Failed to process file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/parse/vpn-shutdown', methods=['POST'])
@jwt_required()
@limiter.limit(security_config.RATELIMIT_PARSE)
def parse_vpn_shutdown() -> tuple:
    """Parse VPN shutdown sessions with async processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    username_filter = request.form.get('username', '')
    
    # Sanitize username filter
    username_filter = sanitize_username(username_filter)
    if not username_filter:
        return jsonify({'error': 'Valid username filter is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filepath, original_name = secure_save_file(file, app.config['UPLOAD_FOLDER'])
            current_user = get_jwt_identity()
            
            security_logger.log_file_upload(
                current_user,
                original_name,
                os.path.getsize(filepath),
                get_remote_address()
            )
            
            task = process_vpn_shutdown_logs.delay(filepath, username_filter, current_user, original_name)
            
            return jsonify({
                'task_id': task.id,
                'status': 'processing',
                'message': 'VPN shutdown session parsing started'
            }), 202
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"VPN shutdown parse error: {e}")
            return jsonify({'error': 'Failed to process file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/task/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id: str) -> tuple:
    """Get status of async task."""
    task = celery.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed...'
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'error': str(task.info)
        }
    else:
        response = {
            'state': task.state,
            'status': task.info
        }
    
    return jsonify(response)


@app.route('/api/download/<filename>', methods=['GET'])
@jwt_required()
def download_file(filename: str) -> tuple:
    """Download processed CSV file."""
    try:
        safe_filename = sanitize_filename(filename)
        filepath = Path('results') / safe_filename
        
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Verify file is within results directory (prevent path traversal)
        if not filepath.resolve().is_relative_to(Path('results').resolve()):
            security_logger.log_security_violation(
                'path_traversal',
                get_jwt_identity(),
                get_remote_address(),
                f'Attempted to access: {filename}'
            )
            return jsonify({'error': 'Invalid file path'}), 403
        
        security_logger.log_download(get_jwt_identity(), safe_filename, get_remote_address())
        
        return send_file(filepath, as_attachment=True, download_name=safe_filename)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': 'Failed to download file'}), 500


@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_parse_history() -> tuple:
    """Get parsing history for current user."""
    current_user = get_jwt_identity()
    # In production, this would query a database
    # For now, return empty history
    return jsonify([])


# Celery tasks
@celery.task(bind=True)
def process_vpn_logs(self, filepath: str, user: str, original_name: str) -> Dict[str, Any]:
    """Process VPN logs asynchronously."""
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Parsing VPN logs...'})
        
        # Detect format and parse
        file_format = csv_parser.detect_format(filepath)
        
        if file_format == 'csv':
            df = csv_parser.parse_csv_vpn_logs(filepath)
        else:
            df = log_parser.parse_vpn_logs(filepath)
        
        if df.empty:
            os.remove(filepath)
            return {
                'status': 'completed',
                'records': 0,
                'filename': None,
                'preview': [],
                'format_detected': file_format,
                'message': 'No valid records found in file'
            }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f'vpn_parsed_{user}_{timestamp}.csv'
        result_path = Path('results') / result_filename
        
        df.to_csv(result_path, index=False)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        logger.info(f"VPN logs processed: {len(df)} records for user {user}")
        
        return {
            'status': 'completed',
            'records': len(df),
            'filename': result_filename,
            'preview': df.head(10).to_dict('records'),
            'format_detected': file_format
        }
    except Exception as e:
        logger.error(f"VPN processing error: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery.task(bind=True)
def process_firewall_logs(self, filepath: str, user: str, original_name: str) -> Dict[str, Any]:
    """Process firewall logs asynchronously."""
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Parsing firewall logs...'})
        
        # Detect format and parse
        file_format = csv_parser.detect_format(filepath)
        
        if file_format == 'csv':
            df = csv_parser.parse_csv_firewall_logs(filepath)
        else:
            df = log_parser.parse_firewall_logs(filepath)
        
        if df.empty:
            os.remove(filepath)
            return {
                'status': 'completed',
                'records': 0,
                'filename': None,
                'preview': [],
                'format_detected': file_format,
                'message': 'No valid records found in file'
            }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f'firewall_parsed_{user}_{timestamp}.csv'
        result_path = Path('results') / result_filename
        
        df.to_csv(result_path, index=False)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        logger.info(f"Firewall logs processed: {len(df)} records for user {user}")
        
        return {
            'status': 'completed',
            'records': len(df),
            'filename': result_filename,
            'preview': df.head(10).to_dict('records'),
            'format_detected': file_format
        }
    except Exception as e:
        logger.error(f"Firewall processing error: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery.task(bind=True)
def process_vpn_shutdown_logs(self, filepath: str, username_filter: str, user: str, original_name: str) -> Dict[str, Any]:
    """Process VPN shutdown sessions asynchronously."""
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Parsing VPN shutdown sessions...'})
        
        # Detect format and parse
        file_format = csv_parser.detect_format(filepath)
        
        if file_format == 'csv':
            df = csv_parser.parse_csv_vpn_shutdown_logs(filepath, username_filter)
        else:
            df = log_parser.parse_vpn_shutdown_sentbytes(filepath, username_filter)
        
        if df.empty:
            os.remove(filepath)
            return {
                'status': 'completed',
                'records': 0,
                'filename': None,
                'preview': [],
                'format_detected': file_format,
                'total_mb': 0,
                'message': f'No records found for user {username_filter}'
            }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f'vpn_shutdown_{username_filter}_{user}_{timestamp}.csv'
        result_path = Path('results') / result_filename
        
        df.to_csv(result_path, index=False)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        total_mb = df['sent_bytes_in_MB'].sum() if 'sent_bytes_in_MB' in df.columns else 0
        
        logger.info(f"VPN shutdown processed: {len(df)} records for user {user}, filter: {username_filter}")
        
        return {
            'status': 'completed',
            'records': len(df),
            'filename': result_filename,
            'preview': df.head(10).to_dict('records'),
            'format_detected': file_format,
            'total_mb': round(total_mb, 2)
        }
    except Exception as e:
        logger.error(f"VPN shutdown processing error: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    headers = get_secure_headers()
    for header, value in headers.items():
        response.headers[header] = value
    return response


if __name__ == '__main__':
    # Use environment variable for debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    if Config.is_production():
        logger.warning("Running in production mode")
        if debug_mode:
            logger.error("DEBUG mode should NOT be enabled in production!")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=debug_mode
    )
