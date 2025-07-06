from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
import pandas as pd
from datetime import datetime
import re
import ipaddress
from csv_parser_service import CSVParserService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max file size

CORS(app, origins=['http://localhost:3000'])

# Create necessary directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

# Simple user store
users = {
    "admin": generate_password_hash("admin123")
}

ALLOWED_EXTENSIONS = {'txt', 'log', 'csv'}

# Initialize CSV parser
csv_parser = CSVParserService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Core parsing functions (original Fortinet log format)
def parse_vpn_logs(file_path):
    """Parses VPN logs and extracts date, time, user, tunneltype, remip, reason, and msg only for successful logins."""
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
            date_match = date_pattern.search(line)
            time_match = time_pattern.search(line)
            user_match = user_pattern.search(line)
            tunneltype_match = tunneltype_pattern.search(line)
            remip_match = remip_pattern.search(line)
            reason_match = reason_pattern.search(line)
            msg_match = msg_pattern.search(line)

            # Ensure all required fields exist in the log
            if date_match and time_match and user_match and tunneltype_match and remip_match and reason_match and msg_match:
                date = date_match.group(1)
                time = time_match.group(1)
                user = user_match.group(1)
                tunneltype = tunneltype_match.group(1)
                remip = remip_match.group(1)
                reason = reason_match.group(1)
                msg = msg_match.group(1)

                # Only keep logs where login was successful based on reason
                if reason.lower() == "login successfully":
                    extracted_data.append([date, time, user, tunneltype, remip, reason, msg])

    df = pd.DataFrame(extracted_data, columns=['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg'])
    return df

def is_public_ip(ip):
    """Returns True if the IP is public, False if it is private/local."""
    try:
        return not ipaddress.ip_address(ip).is_private
    except:
        return False

def parse_firewall_logs(file_path):
    """Parses firewall logs, aggregates data by destination IP (excluding local IPs), sorts in descending order, and adds size in MB."""
    dstip_pattern = re.compile(r'dstip=([\d\.]+)')
    sentbyte_pattern = re.compile(r'sentbyte=(\d+)')
    
    data = {}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            dstip_match = dstip_pattern.search(line)
            sentbyte_match = sentbyte_pattern.search(line)
            
            if dstip_match and sentbyte_match:
                dstip = dstip_match.group(1)
                sentbyte = int(sentbyte_match.group(1))
                
                # Exclude private/local IPs
                if is_public_ip(dstip):
                    if dstip in data:
                        data[dstip] += sentbyte
                    else:
                        data[dstip] = sentbyte
    
    df = pd.DataFrame(list(data.items()), columns=['dstip', 'total_sentbyte'])
    
    # Convert bytes to megabytes
    df['size_mb'] = df['total_sentbyte'] / (1024 * 1024)

    # Sort data in descending order based on total sent bytes
    df = df.sort_values(by='total_sentbyte', ascending=False)
    
    return df

def parse_vpn_shutdown_sentbytes_csv(file_path, target_user):
    """
    Parses VPN logs to extract date, time, user, and sentbyte information for sessions 
    where the msg field equals "SSL tunnel shutdown". It then calculates the sent bytes in MB.
    
    Returns a DataFrame with the following columns:
    - date
    - time
    - user
    - sentbyte
    - sent_bytes_in_MB
    """
    # Define regex patterns for the fields of interest.
    date_pattern = re.compile(r'date=(\S+)')
    time_pattern = re.compile(r'time=(\S+)')
    user_pattern = re.compile(r'user="([^"]+)"', flags=re.IGNORECASE)
    sentbyte_pattern = re.compile(r'sentbyte=(\d+)')
    msg_pattern = re.compile(r'msg="([^"]+)"')

    extracted_data = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Check if the message indicates a shutdown.
            msg_match = msg_pattern.search(line)
            if msg_match and msg_match.group(1) == "SSL tunnel shutdown":
                # Filter by user (case-insensitive).
                user_match = user_pattern.search(line)
                if user_match and user_match.group(1).lower() == target_user.lower():
                    date_match = date_pattern.search(line)
                    time_match = time_pattern.search(line)
                    sentbyte_match = sentbyte_pattern.search(line)
                    if date_match and time_match and sentbyte_match:
                        date_val = date_match.group(1)
                        time_val = time_match.group(1)
                        user_val = user_match.group(1)
                        sentbyte = int(sentbyte_match.group(1))
                        sent_bytes_in_mb = sentbyte / (1024 * 1024)
                        extracted_data.append([date_val, time_val, user_val, sentbyte, sent_bytes_in_mb])
    
    df = pd.DataFrame(extracted_data, columns=['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB'])
    return df

def smart_parse_logs(file_path, parse_type, username_filter=None):
    """Smart parser that detects format and uses appropriate parser"""
    try:
        file_format = csv_parser.detect_format(file_path)
        
        if file_format == 'csv':
            if parse_type == 'vpn':
                return csv_parser.parse_csv_vpn_logs(file_path)
            elif parse_type == 'firewall':
                return csv_parser.parse_csv_firewall_logs(file_path)
            elif parse_type == 'vpn-shutdown':
                return csv_parser.parse_csv_vpn_shutdown_logs(file_path, username_filter)
        else:
            # Use original Fortinet log parsers
            if parse_type == 'vpn':
                return parse_vpn_logs(file_path)
            elif parse_type == 'firewall':
                return parse_firewall_logs(file_path)
            elif parse_type == 'vpn-shutdown':
                return parse_vpn_shutdown_sentbytes_csv(file_path, username_filter)
        
        return pd.DataFrame()  # Return empty DataFrame if no parser matches
        
    except Exception as e:
        raise Exception(f"Parsing failed: {str(e)}")

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username in users and check_password_hash(users[username], password):
        return jsonify({
            'access_token': 'dummy-token',  # Simple token for testing
            'username': username
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    # Simple verification for testing
    return jsonify({'valid': True, 'username': 'admin'}), 200

@app.route('/api/parse/vpn', methods=['POST'])
def parse_vpn():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join('uploads', f'{timestamp}_{filename}')
        file.save(filepath)
        
        try:
            # Use smart parser
            df = smart_parse_logs(filepath, 'vpn')
            
            # Save results
            result_filename = f'vpn_parsed_{timestamp}.csv'
            result_path = os.path.join('results', result_filename)
            df.to_csv(result_path, index=False)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'status': 'completed',
                'records': len(df),
                'filename': result_filename,
                'preview': df.head(10).to_dict('records') if len(df) > 0 else [],
                'format_detected': csv_parser.detect_format(filepath) if os.path.exists(filepath) else 'unknown'
            }), 200
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/parse/firewall', methods=['POST'])
def parse_firewall():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join('uploads', f'{timestamp}_{filename}')
        file.save(filepath)
        
        try:
            # Use smart parser
            df = smart_parse_logs(filepath, 'firewall')
            
            # Save results
            result_filename = f'firewall_parsed_{timestamp}.csv'
            result_path = os.path.join('results', result_filename)
            df.to_csv(result_path, index=False)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'status': 'completed',
                'records': len(df),
                'filename': result_filename,
                'preview': df.head(10).to_dict('records') if len(df) > 0 else []
            }), 200
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/parse/vpn-shutdown', methods=['POST'])
def parse_vpn_shutdown():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    username_filter = request.form.get('username', '')
    
    if not username_filter:
        return jsonify({'error': 'Username filter is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join('uploads', f'{timestamp}_{filename}')
        file.save(filepath)
        
        try:
            # Use smart parser
            df = smart_parse_logs(filepath, 'vpn-shutdown', username_filter)
            
            # Save results
            result_filename = f'vpn_shutdown_{username_filter}_{timestamp}.csv'
            result_path = os.path.join('results', result_filename)
            df.to_csv(result_path, index=False)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'status': 'completed',
                'records': len(df),
                'filename': result_filename,
                'preview': df.head(10).to_dict('records') if len(df) > 0 else [],
                'total_mb': df['sent_bytes_in_MB'].sum() if len(df) > 0 and 'sent_bytes_in_MB' in df.columns else 0
            }), 200
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join('results', safe_filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=safe_filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_parse_history():
    # Return empty history for now
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)