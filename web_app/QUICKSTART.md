# Quick Start Guide - Forti-DFIR Web Application

## Prerequisites
- Python 3.6 or higher
- Node.js 14 or higher

## Option 1: Automatic Start (Recommended)

### On macOS/Linux:
```bash
cd web_app
./run.sh
```

### On Windows:
```cmd
cd web_app
run.bat
```

## Option 2: Manual Start

### Terminal 1 - Backend:
```bash
cd web_app/backend
pip install flask flask-cors pandas werkzeug
python simple_app.py
```

### Terminal 2 - Frontend:
```bash
cd web_app/frontend
npm install
npm start
```

## Usage

1. Open http://localhost:3000 in your browser
2. Login with: **admin** / **admin123**
3. Select parser type:
   - VPN Logs - Extract successful login details
   - Firewall Logs - Aggregate traffic by destination IP
   - VPN Shutdown - Analyze session termination data
4. Upload your log file
5. View results and download CSV

## Troubleshooting

### Backend not starting:
- Make sure port 5000 is not in use
- Check Python dependencies: `pip install flask flask-cors pandas werkzeug`

### Frontend not starting:
- Make sure port 3000 is not in use
- Delete `node_modules` folder and run `npm install` again

### CORS errors:
- Make sure backend is running on http://localhost:5000
- Check that you're accessing frontend via http://localhost:3000

### File upload fails:
- Check file format (.txt, .log, .csv)
- Ensure file size is under 100MB

## Sample Log Format

The parser expects Fortinet log format with fields like:
```
date=2024-01-15 time=10:30:45 user="john.doe" tunneltype="SSL-VPN" remip=192.168.1.100 reason="login successfully" msg="SSL tunnel established"
```

## Support

For issues, check the original CLI tool documentation in the parent directory.