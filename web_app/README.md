# Forti-DFIR Web Application

A powerful web-based version of the Forti-DFIR log parser tool, built with Flask (backend) and React (frontend).

## Features

- **Modern Web Interface**: Clean, responsive UI built with React and Material-UI
- **Authentication**: Secure JWT-based authentication system
- **Asynchronous Processing**: Background job processing with Celery and Redis
- **Real-time Updates**: Live progress tracking for log parsing operations
- **File Management**: Drag-and-drop file upload with progress indication
- **Data Visualization**: Interactive data grids with sorting and filtering
- **Export Functionality**: Download parsed results as CSV files
- **Dark Theme**: Modern dark theme for comfortable viewing

## Architecture

### Backend (Flask)
- RESTful API endpoints
- JWT authentication
- Celery for background tasks
- Redis for task queue and caching
- Rate limiting for API protection

### Frontend (React)
- Material-UI components
- React Router for navigation
- Axios for API communication
- Real-time task status polling
- Responsive design

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
cd web_app
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
# Edit .env with your secure keys
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

### Manual Installation

#### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Install and run Redis:
```bash
# On macOS
brew install redis
brew services start redis

# On Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

4. Run the Flask application:
```bash
python app.py
```

5. In a separate terminal, run Celery worker:
```bash
celery -A app.celery worker --loglevel=info
```

#### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

## Usage

1. **Login**: Use default credentials (admin/admin123) or configure your own
2. **Select Parser Type**: Choose from VPN, Firewall, or VPN Shutdown parser
3. **Upload Log File**: Drag and drop or click to upload your log file
4. **View Results**: Interactive data grid with preview
5. **Export**: Download parsed results as CSV

## API Endpoints

- `POST /api/auth/login` - User authentication
- `GET /api/auth/verify` - Verify JWT token
- `POST /api/parse/vpn` - Parse VPN logs
- `POST /api/parse/firewall` - Parse firewall logs
- `POST /api/parse/vpn-shutdown` - Parse VPN shutdown sessions
- `GET /api/task/{task_id}` - Check task status
- `GET /api/download/{filename}` - Download result file
- `GET /api/history` - Get parsing history

## Security Features

- JWT-based authentication
- Rate limiting on API endpoints
- Secure file upload with validation
- CORS protection
- Input sanitization
- Secure password hashing

## Configuration

### Backend Configuration (.env)
```
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
```

### Frontend Configuration
- API URL configuration in package.json proxy
- Environment-specific builds supported

## Development

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Code Structure
```
web_app/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── log_parser_service.py # Core parsing logic
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts
│   │   └── App.js         # Main React app
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Production Deployment

1. Update environment variables with secure values
2. Enable HTTPS with SSL certificates
3. Configure proper CORS origins
4. Set up monitoring and logging
5. Use production-grade database for user management
6. Configure backup strategies

### Cloud Deployment

The web application can be deployed to various platforms:

- **Frontend**: Netlify, Vercel, GitHub Pages
- **Backend**: Heroku, Railway, Render, Vercel

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

#### Quick Deploy to Netlify

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/ionsec/Forti-DFIR)

#### Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ionsec/Forti-DFIR)

## Troubleshooting

### Common Issues

1. **Redis Connection Error**: Ensure Redis is running
2. **CORS Issues**: Check CORS configuration in app.py
3. **File Upload Fails**: Check file size limits and permissions
4. **Authentication Fails**: Verify JWT secret keys match

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Developed by IONSec Research Team