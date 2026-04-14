"""
Forti-DFIR Web Application - Simplified Flask Application

This is a simplified version of the application for development and testing.
For production, use app.py which includes full security hardening.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from flask_talisman import Talisman
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Import utilities
from config import Config
from utils.security import (
    sanitize_filename,
    sanitize_username,
    secure_save_file,
    get_secure_headers,
    ALLOWED_EXTENSIONS,
)
from utils.input_validation import validate_password
from utils.logging_config import setup_logger, SecurityLogger
from csv_parser_service import CSVParserService

# Setup logging
logger = setup_logger(__name__, level='DEBUG', log_file='simple_app.log')
security_logger = SecurityLogger()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

# Security warning for development
if not Config.is_production():
    logger.warning("=" * 60)
    logger.warning("RUNNING IN DEVELOPMENT MODE")
    logger.warning("Do NOT use this configuration in production!")
    logger.warning("Set FLASK_ENV=production and configure secrets.")
    logger.warning("=" * 60)

# Enable CORS for development
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=cors_origins)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get('REDIS_URL', 'memory://'),
)

# Security headers (less strict for development)
if Config.is_production():
    Talisman(app, force_https=True)

# Create necessary directories
Path('uploads').mkdir(parents=True, exist_ok=True)
Path('results').mkdir(parents=True, exist_ok=True)

# User store - Initialize from environment or use placeholder
users: Dict[str, Dict[str, Any]] = {}

def init_users():
    """Initialize users from environment variables."""
    admin_user = os.environ.get('ADMIN_USER', 'admin')
    admin_pass = os.environ.get('ADMIN_PASSWORD')
    
    if admin_pass:
        # Validate password if provided
        is_valid, msg = validate_password(admin_pass)
        if not is_valid:
            logger.warning(f"Admin password validation failed: {msg}")
            logger.warning("Using default for development only!")
            admin_pass = 'admin123'  # Fallback for development
    else:
        if Config.is_production():
            raise ValueError("ADMIN_PASSWORD environment variable required in production")
        admin_pass = 'admin123'
        logger.warning("Using default admin password - NOT SAFE FOR PRODUCTION!")
    
    users[admin_user] = {
        'password_hash': generate_password_hash(admin_pass),
        'created_at': datetime.utcnow().isoformat(),
        'is_admin': True
    }
    logger.info(f"Initialized user: {admin_user}")

init_users()

# Initialize CSV parser
csv_parser = CSVParserService()


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.1',
        'mode': 'development' if Config.is_development() else 'production'
    })


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    
    if not data:
        security_logger.log_login_attempt('unknown', get_remote_address(), False, 'No data provided')
        return jsonify({'error': 'No data provided'}), 400
    
    username = sanitize_username(data.get('username', ''))
    password = data.get('password', '')
    
    if not username:
        return jsonify({'error': 'Valid username required'}), 400
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    # Check credentials
    user = users.get(username)
    
    if user and check_password_hash(user['password_hash'], password):
        security_logger.log_login_attempt(username, get_remote_address(), True)
        return jsonify({
            'access_token': 'dev-token',  # In production, use real JWT
            'username': username
        }), 200
    
    security_logger.log_login_attempt(username, get_remote_address(), False, 'Invalid credentials')
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Verify token validity."""
    # Simple verification for development
    return jsonify({'valid': True, 'username': 'admin'}), 200


@app.route('/api/parse/vpn', methods=['POST'])
@limiter.limit("10 per minute")
def parse_vpn():
    """Parse VPN logs."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filepath, original_name = secure_save_file(file, 'uploads')
            
            security_logger.log_file_upload(
                'anonymous',
                original_name,
                os.path.getsize(filepath),
                get_remote_address()
            )
            
            # Detect format and parse
            file_format = csv_parser.detect_format(filepath)
            
            if file_format == 'csv':
                df = csv_parser.parse_csv_vpn_logs(filepath)
            else:
                # Use smart parser for Fortinet format
                df = smart_parse_logs(filepath, 'vpn')
            
            # Validate results
            if df.empty:
                os.remove(filepath)
                return jsonify({
                    'status': 'completed',
                    'records': 0,
                    'filename': None,
                    'preview': [],
                    'format_detected': file_format,
                    'message': 'No valid records found'
                }), 200
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_filename = f'vpn_parsed_{timestamp}.csv'
            result_path = Path('results') / result_filename
            df.to_csv(result_path, index=False)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            logger.info(f"VPN logs parsed: {len(df)} records")
            
            return jsonify({
                'status': 'completed',
                'records': len(df),
                'filename': result_filename,
                'preview': df.head(10).to_dict('records') if len(df) > 0 else [],
                'format_detected': file_format
            }), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"VPN parse error: {e}")
            return jsonify({'error': 'Failed to process file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/parse/firewall', methods=['POST'])
@limiter.limit("10 per minute")
def parse_firewall():
    """Parse firewall logs."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filepath, original_name = secure_save_file(file, 'uploads')
            
            security_logger.log_file_upload(
                'anonymous',
                original_name,
                os.path.getsize(filepath),
                get_remote_address()
            )
            
            # Detect format and parse
            file_format = csv_parser.detect_format(filepath)
            
            if file_format == 'csv':
                df = csv_parser.parse_csv_firewall_logs(filepath)
            else:
                df = smart_parse_logs(filepath, 'firewall')
            
            # Validate results
            if df.empty:
                os.remove(filepath)
                return jsonify({
                    'status': 'completed',
                    'records': 0,
                    'filename': None,
                    'preview': [],
                    'format_detected': file_format,
                    'message': 'No valid records found'
                }), 200
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_filename = f'firewall_parsed_{timestamp}.csv'
            result_path = Path('results') / result_filename
            df.to_csv(result_path, index=False)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            logger.info(f"Firewall logs parsed: {len(df)} records")
            
            return jsonify({
                'status': 'completed',
                'records': len(df),
                'filename': result_filename,
                'preview': df.head(10).to_dict('records') if len(df) > 0 else [],
                'format_detected': file_format
            }), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Firewall parse error: {e}")
            return jsonify({'error': 'Failed to process file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/parse/vpn-shutdown', methods=['POST'])
@limiter.limit("10 per minute")
def parse_vpn_shutdown():
    """Parse VPN shutdown sessions."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    username_filter = sanitize_username(request.form.get('username', ''))
    
    if not username_filter:
        return jsonify({'error': 'Valid username filter is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filepath, original_name = secure_save_file(file, 'uploads')
            
            security_logger.log_file_upload(
                'anonymous',
                original_name,
                os.path.getsize(filepath),
                get_remote_address()
            )
            
            # Detect format and parse
            file_format = csv_parser.detect_format(filepath)
            
            if file_format == 'csv':
                df = csv_parser.parse_csv_vpn_shutdown_logs(filepath, username_filter)
            else:
                df = smart_parse_logs(filepath, 'vpn-shutdown', username_filter)
            
            # Validate results
            if df.empty:
                os.remove(filepath)
                return jsonify({
                    'status': 'completed',
                    'records': 0,
                    'filename': None,
                    'preview': [],
                    'format_detected': file_format,
                    'total_mb': 0,
                    'message': f'No records found for user {username_filter}'
                }), 200
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_filename = f'vpn_shutdown_{username_filter}_{timestamp}.csv'
            result_path = Path('results') / result_filename
            df.to_csv(result_path, index=False)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            total_mb = df['sent_bytes_in_MB'].sum() if 'sent_bytes_in_MB' in df.columns else 0
            
            logger.info(f"VPN shutdown parsed: {len(df)} records, filter: {username_filter}")
            
            return jsonify({
                'status': 'completed',
                'records': len(df),
                'filename': result_filename,
                'preview': df.head(10).to_dict('records') if len(df) > 0 else [],
                'format_detected': file_format,
                'total_mb': round(total_mb, 2)
            }), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"VPN shutdown parse error: {e}")
            return jsonify({'error': 'Failed to process file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename: str):
    """Download processed CSV file."""
    try:
        safe_filename = sanitize_filename(filename)
        filepath = Path('results') / safe_filename
        
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Prevent path traversal
        if not filepath.resolve().is_relative_to(Path('results').resolve()):
            security_logger.log_security_violation(
                'path_traversal',
                'anonymous',
                get_remote_address(),
                f'Attempted to access: {filename}'
            )
            return jsonify({'error': 'Invalid file path'}), 403
        
        security_logger.log_download('anonymous', safe_filename, get_remote_address())
        
        return send_file(filepath, as_attachment=True, download_name=safe_filename)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': 'Failed to download file'}), 500


@app.route('/api/history', methods=['GET'])
def get_parse_history():
    """Get parsing history."""
    # Return empty history for simple app
    return jsonify([])


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    headers = get_secure_headers()
    for header, value in headers.items():
        response.headers[header] = value
    return response


# ========================
# Core Parsing Functions (Fortinet Format)
# ========================

import re
import pandas as pd
import ipaddress


def parse_vpn_logs(file_path: str):
    """Parse VPN logs in Fortinet format."""
    date_pattern = re.compile(r'date=(\S+)')
    time_pattern = re.compile(r'time=(\S+)')
    user_pattern = re.compile(r'user="([^"]+)"')
    tunneltype_pattern = re.compile(r'tunneltype="([^"]+)"')
    remip_pattern = re.compile(r'remip=([\d\.]+)')
    reason_pattern = re.compile(r'reason="([^"]+)"')
    msg_pattern = re.compile(r'msg="([^"]+)"')

    extracted_data = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                date_match = date_pattern.search(line)
                time_match = time_pattern.search(line)
                user_match = user_pattern.search(line)
                tunneltype_match = tunneltype_pattern.search(line)
                remip_match = remip_pattern.search(line)
                reason_match = reason_pattern.search(line)
                msg_match = msg_pattern.search(line)

                if all([date_match, time_match, user_match, tunneltype_match, 
                        remip_match, reason_match, msg_match]):
                    reason = reason_match.group(1)
                    if reason.lower() == "login successfully":
                        extracted_data.append([
                            date_match.group(1),
                            time_match.group(1),
                            user_match.group(1),
                            tunneltype_match.group(1),
                            remip_match.group(1),
                            reason,
                            msg_match.group(1)
                        ])
            except Exception as e:
                logger.debug(f"Skipping malformed line: {e}")
                continue

    return pd.DataFrame(extracted_data, 
                       columns=['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg'])


def is_public_ip(ip: str) -> bool:
    """Check if IP address is public."""
    try:
        return not ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def parse_firewall_logs(file_path: str):
    """Parse firewall logs in Fortinet format."""
    dstip_pattern = re.compile(r'dstip=([\d\.]+)')
    sentbyte_pattern = re.compile(r'sentbyte=(\d+)')
    
    data = {}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                dstip_match = dstip_pattern.search(line)
                sentbyte_match = sentbyte_pattern.search(line)
                
                if dstip_match and sentbyte_match:
                    dstip = dstip_match.group(1)
                    sentbyte = int(sentbyte_match.group(1))
                    
                    if is_public_ip(dstip):
                        data[dstip] = data.get(dstip, 0) + sentbyte
            except Exception as e:
                logger.debug(f"Skipping malformed line: {e}")
                continue
    
    df = pd.DataFrame(list(data.items()), columns=['dstip', 'total_sentbyte'])
    df['size_mb'] = df['total_sentbyte'] / (1024 * 1024)
    return df.sort_values(by='total_sentbyte', ascending=False)


def parse_vpn_shutdown_sentbytes(file_path: str, target_user: str):
    """Parse VPN shutdown sessions for a specific user."""
    date_pattern = re.compile(r'date=(\S+)')
    time_pattern = re.compile(r'time=(\S+)')
    user_pattern = re.compile(r'user="([^"]+)"', flags=re.IGNORECASE)
    sentbyte_pattern = re.compile(r'sentbyte=(\d+)')
    msg_pattern = re.compile(r'msg="([^"]+)"')

    extracted_data = []
    target_user_lower = target_user.lower()

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                msg_match = msg_pattern.search(line)
                if msg_match and msg_match.group(1) == "SSL tunnel shutdown":
                    user_match = user_pattern.search(line)
                    if user_match and user_match.group(1).lower() == target_user_lower:
                        date_match = date_pattern.search(line)
                        time_match = time_pattern.search(line)
                        sentbyte_match = sentbyte_pattern.search(line)
                        
                        if all([date_match, time_match, sentbyte_match]):
                            sentbyte = int(sentbyte_match.group(1))
                            extracted_data.append([
                                date_match.group(1),
                                time_match.group(1),
                                user_match.group(1),
                                sentbyte,
                                sentbyte / (1024 * 1024)
                            ])
            except Exception as e:
                logger.debug(f"Skipping malformed line: {e}")
                continue
    
    return pd.DataFrame(extracted_data, 
                       columns=['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB'])


def smart_parse_logs(file_path: str, log_type: str, username_filter: str = None):
    """Smart log parser that handles multiple formats."""
    # First detect format
    file_format = csv_parser.detect_format(file_path)
    
    logger.info(f"Detected format: {file_format} for {log_type}")
    
    # Route to appropriate parser
    if file_format == 'csv':
        if log_type == 'vpn':
            return csv_parser.parse_csv_vpn_logs(file_path)
        elif log_type == 'firewall':
            return csv_parser.parse_csv_firewall_logs(file_path)
        elif log_type == 'vpn-shutdown':
            return csv_parser.parse_csv_vpn_shutdown_logs(file_path, username_filter)
    else:
        # Fortinet format
        if log_type == 'vpn':
            return parse_vpn_logs(file_path)
        elif log_type == 'firewall':
            return parse_firewall_logs(file_path)
        elif log_type == 'vpn-shutdown':
            return parse_vpn_shutdown_sentbytes(file_path, username_filter)
    
    return pd.DataFrame()


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    if Config.is_production() and debug_mode:
        logger.error("DEBUG mode should NOT be enabled in production!")
        exit(1)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
