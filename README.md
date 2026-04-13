# Forti-DFIR - IONSec Fortinet Log Parser Tool

## Overview
**IONSec Forti-DFIR Log Parser Tool** is a comprehensive solution for analyzing Fortinet VPN and firewall logs. Available as both a command-line utility and a modern web application, it extracts key data and exports it to CSV format, streamlining security investigations for incident responders.

Developed by the **IONSec Research Team**.

---

## Features
- 🔍 **VPN Login Parser**: Extracts successful VPN login details.
- 📊 **Firewall Log Aggregation**: Summarizes traffic by destination IP, filtering out private/local addresses.
- 📌 **VPN Session Shutdown Analyzer**: Extracts session termination statistics, including sent bytes, for a specific user.
- 💻 **Interactive CLI Interface**: Guides users through log selection and parsing options.
- 🌐 **Web Application**: Modern web interface with authentication, file upload, and real-time processing.
- 📂 **CSV Export**: Saves parsed data for easy analysis.
- 📁 **Multi-Format Support**: Handles both Fortinet log format and CSV files.
- 🔒 **Security Hardened**: Input validation, rate limiting, secure authentication.
- 🐳 **Docker Support**: Easy deployment with Docker Compose.
- ☁️ **Cloud Ready**: Automatic deployment to Netlify and Vercel.
- 📖 **Full Documentation**: Sphinx-based documentation available.

---

## Quick Start

### Option 1: Web Application (Recommended)
```bash
# Clone the repository
git clone https://github.com/ionsec/Forti-DFIR.git
cd Forti-DFIR

# Copy environment template
cp .env.example .env
# Edit .env with your credentials (IMPORTANT!)

# Start with Docker
cd web_app
docker-compose up
```
Access the application at http://localhost:3000

### Option 2: Command Line Interface
```bash
# Clone the repository
git clone https://github.com/ionsec/Forti-DFIR.git
cd Forti-DFIR

# Install dependencies
pip install pandas

# Run the CLI
python log_parser.py
```

---

## Installation

### Prerequisites
- Python **3.11+** (recommended)
- `pandas` library

### CLI Installation
```bash
git clone https://github.com/ionsec/Forti-DFIR.git
cd Forti-DFIR
pip install pandas
python log_parser.py
```

### Web Application Installation

**Option A - Using Docker (Recommended):**
```bash
cd web_app
docker-compose up
```

**Option B - Manual Installation:**
```bash
# Backend
cd web_app/backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Copy and configure environment
cp ../../.env.example .env
# Edit .env with your settings

# Start Redis (required for Celery)
redis-server

# Start Celery worker (separate terminal)
celery -A app.celery worker --loglevel=info

# Start Flask server
python app.py

# Frontend (separate terminal)
cd ../frontend
npm install
npm start
```

---

## Configuration

### Environment Variables

Create a `.env` file from the template:
```bash
cp .env.example .env
```

**Required for Production:**
| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key (32+ random characters) |
| `JWT_SECRET_KEY` | JWT signing key (32+ random characters) |
| `ADMIN_USER` | Initial admin username |
| `ADMIN_PASSWORD` | Initial admin password (min 12 chars, mixed case, digit, special char) |

**Generate secure keys:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## CLI Usage

Run the CLI tool:
```bash
python log_parser.py
```

### Interactive Menu
```
1. Parse VPN logs
2. Parse and aggregate firewall logs
3. Parse VPN shutdown sessions for a user
4. Exit
```

### CLI Options
| Option | Description |
|--------|-------------|
| `1` | Parse VPN logs - Extracts successful login details |
| `2` | Parse firewall logs - Aggregates traffic by destination IP |
| `3` | Parse VPN shutdown - Extracts session data for a specific user |
| `-help` | Display usage instructions |
| `-v` | Show version |

---

## Web Application

Access the web interface at http://localhost:3000

### Features
- **User Authentication**: Secure login with JWT tokens
- **File Upload**: Drag-and-drop support for .txt, .log, .csv files
- **Real-time Processing**: Async processing with status updates
- **Results Preview**: View parsed data before downloading
- **CSV Download**: Export results for further analysis

### Default Credentials
⚠️ **Change these immediately in production!**
- Username: `admin`
- Password: `admin123`

Set custom credentials via environment variables:
```bash
export ADMIN_USER=your_username
export ADMIN_PASSWORD='YourStrongPassword123!'
```

---

## Output Format

### VPN Logs Output
| Column | Description |
|--------|-------------|
| date | Log entry date |
| time | Log entry time |
| user | VPN username |
| tunneltype | Tunnel type (e.g., ssl-web) |
| remip | Remote IP address |
| reason | Login reason/status |
| msg | Additional message |

### Firewall Logs Output
| Column | Description |
|--------|-------------|
| dstip | Destination IP (public only) |
| total_sentbyte | Total bytes sent |
| size_mb | Size in megabytes |

### VPN Shutdown Output
| Column | Description |
|--------|-------------|
| date | Session end date |
| time | Session end time |
| user | VPN username |
| sentbyte | Bytes sent |
| sent_bytes_in_MB | Size in megabytes |

---

## Security

### Security Features
- ✅ Input validation and sanitization
- ✅ Rate limiting (5/min login, 10/min parse)
- ✅ Secure password hashing (scrypt)
- ✅ JWT authentication
- ✅ Security headers (CSP, HSTS, X-Frame-Options)
- ✅ File type validation
- ✅ Path traversal prevention
- ✅ Audit logging

### Production Checklist
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Change default admin credentials
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Configure HTTPS
- [ ] Set appropriate CORS origins

---

## Documentation

Full documentation is available in the `docs/` directory.

### Build Documentation
```bash
cd docs
pip install sphinx sphinx-rtd-theme myst-parser
make html
# Open docs/build/html/index.html
```

### Documentation Contents
- Installation Guide
- Quick Start
- CLI User Guide
- Web Application Guide
- Security Guide
- API Reference
- Contributing Guide

---

## Testing

Run the test suite:
```bash
pip install -r requirements-dev.txt
pytest
```

Run with coverage:
```bash
pytest --cov=web_app/backend --cov-report=html
```

---

## Development

### Code Quality
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linter
ruff check .

# Format code
black .

# Type check
mypy web_app/backend
```

### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Project Structure
```
Forti-DFIR/
├── log_parser.py           # CLI tool
├── web_app/
│   ├── backend/
│   │   ├── app.py          # Main Flask app
│   │   ├── simple_app.py   # Simplified app
│   │   ├── config.py       # Configuration
│   │   ├── log_parser_service.py
│   │   ├── csv_parser_service.py
│   │   ├── utils/          # Security utilities
│   │   └── requirements.txt
│   └── frontend/
│       └── src/
│           └── SimpleApp.js
├── docs/                   # Sphinx documentation
├── tests/                  # Unit tests
├── pyproject.toml          # Project configuration
└── .env.example            # Environment template
```

---

## Deployment

### Docker Deployment
```bash
cd web_app
docker-compose up -d
```

### Cloud Deployment
- **Netlify**: [![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/ionsec/Forti-DFIR)
- **Vercel**: [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ionsec/Forti-DFIR)

See [web_app/DEPLOYMENT.md](web_app/DEPLOYMENT.md) for detailed instructions.

---

## Contributing
Contributions are welcome! Please read the contributing guidelines in `docs/source/contributing.rst`.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

## License
This project is developed by the IONSec Research Team.

---

## Support
- **Issues**: https://github.com/ionsec/Forti-DFIR/issues
- **Documentation**: See `docs/` directory
