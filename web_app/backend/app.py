from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import json
from log_parser_service import LogParserService
from celery import Celery
import redis

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CELERY_BROKER_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CORS(app, origins=['http://localhost:3000'])
jwt = JWTManager(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('results', exist_ok=True)

# Simple user store (in production, use a database)
users = {
    "admin": generate_password_hash("admin123")
}

log_parser = LogParserService()

ALLOWED_EXTENSIONS = {'txt', 'log', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username in users and check_password_hash(users[username], password):
        access_token = create_access_token(identity=username)
        return jsonify({
            'access_token': access_token,
            'username': username
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    current_user = get_jwt_identity()
    return jsonify({'valid': True, 'username': current_user}), 200

@app.route('/api/parse/vpn', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def parse_vpn():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}_{filename}')
        file.save(filepath)
        
        task = process_vpn_logs.delay(filepath, get_jwt_identity())
        
        return jsonify({
            'task_id': task.id,
            'status': 'processing',
            'message': 'VPN log parsing started'
        }), 202
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/parse/firewall', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def parse_firewall():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}_{filename}')
        file.save(filepath)
        
        task = process_firewall_logs.delay(filepath, get_jwt_identity())
        
        return jsonify({
            'task_id': task.id,
            'status': 'processing',
            'message': 'Firewall log parsing started'
        }), 202
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/parse/vpn-shutdown', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}_{filename}')
        file.save(filepath)
        
        task = process_vpn_shutdown_logs.delay(filepath, username_filter, get_jwt_identity())
        
        return jsonify({
            'task_id': task.id,
            'status': 'processing',
            'message': 'VPN shutdown session parsing started'
        }), 202
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/task/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
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
@jwt_required()
def get_parse_history():
    current_user = get_jwt_identity()
    # In production, this would query a database
    # For now, return mock data
    history = [
        {
            'id': 1,
            'type': 'VPN Logs',
            'filename': 'vpn_logs_20240115.txt',
            'timestamp': '2024-01-15T10:30:00',
            'status': 'completed',
            'records': 1523,
            'result_file': 'vpn_parsed_20240115_103000.csv'
        },
        {
            'id': 2,
            'type': 'Firewall Logs',
            'filename': 'firewall_logs_20240114.txt',
            'timestamp': '2024-01-14T15:45:00',
            'status': 'completed',
            'records': 3421,
            'result_file': 'firewall_parsed_20240114_154500.csv'
        }
    ]
    return jsonify(history)

# Celery tasks
@celery.task(bind=True)
def process_vpn_logs(self, filepath, user):
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Parsing VPN logs...'})
        
        df = log_parser.parse_vpn_logs(filepath)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f'vpn_parsed_{user}_{timestamp}.csv'
        result_path = os.path.join('results', result_filename)
        
        df.to_csv(result_path, index=False)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return {
            'status': 'completed',
            'records': len(df),
            'filename': result_filename,
            'preview': df.head(10).to_dict('records') if len(df) > 0 else []
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery.task(bind=True)
def process_firewall_logs(self, filepath, user):
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Parsing firewall logs...'})
        
        df = log_parser.parse_firewall_logs(filepath)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f'firewall_parsed_{user}_{timestamp}.csv'
        result_path = os.path.join('results', result_filename)
        
        df.to_csv(result_path, index=False)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return {
            'status': 'completed',
            'records': len(df),
            'filename': result_filename,
            'preview': df.head(10).to_dict('records') if len(df) > 0 else []
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery.task(bind=True)
def process_vpn_shutdown_logs(self, filepath, username_filter, user):
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Parsing VPN shutdown sessions...'})
        
        df = log_parser.parse_vpn_shutdown_sentbytes(filepath, username_filter)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f'vpn_shutdown_{username_filter}_{user}_{timestamp}.csv'
        result_path = os.path.join('results', result_filename)
        
        df.to_csv(result_path, index=False)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return {
            'status': 'completed',
            'records': len(df),
            'filename': result_filename,
            'preview': df.head(10).to_dict('records') if len(df) > 0 else [],
            'total_mb': df['sent_bytes_in_MB'].sum() if len(df) > 0 else 0
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

if __name__ == '__main__':
    app.run(debug=True, port=5000)