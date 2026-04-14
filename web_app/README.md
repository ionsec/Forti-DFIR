# Forti-DFIR Web Application

Forti-DFIR Web is a browser-based Fortinet log parser built with Flask and React. It supports VPN, firewall, and VPN shutdown parsing for both Fortinet key-value logs and CSV inputs.

## Release 1.0.1

This release focuses on making the local Docker workflow reliable and predictable.

- Fixed backend container startup by aligning the Docker image with the backend Python requirements
- Fixed the backend build context so `requirements.txt` is included during Docker builds
- Documented the active local Docker ports and default login flow
- Kept the Docker stack self-contained for local use through the simplified backend entrypoint

## Features

- Web interface for Fortinet log parsing
- Support for VPN, firewall, and VPN shutdown workflows
- CSV export for parsed results
- File upload validation and secure filename handling
- History and downloadable result artifacts
- Docker-first local startup path

## Architecture

### Docker Release Path

The default Docker release path is optimized for local use:

- `frontend` serves the built React app through nginx
- nginx proxies `/api` traffic to the backend container
- `backend/simple_app.py` runs the API used by the Docker stack
- Uploaded files are stored in `backend/uploads`
- Parsed CSV output is stored in `backend/results`

### Full Backend Path

The repository also includes `backend/app.py`, which contains the larger JWT/Celery-oriented application flow for more advanced deployments. The Docker compose files in this directory currently ship the simpler local stack.

## Quick Start

### Docker

Start the main local stack:

```bash
docker compose up --build -d
```

Access:

- Web UI: `http://localhost:8080`
- Backend health endpoint: `http://localhost:8000/api/health`
- Default login: `admin / admin123`

Stop the stack:

```bash
docker compose down
```

Use the alternate port mapping if `8080` or `8000` is already in use:

```bash
docker compose -f docker-compose-alt.yml up --build -d
```

Alternate ports:

- Web UI: `http://localhost:3001`
- Backend health endpoint: `http://localhost:5001/api/health`

### Manual Run

Backend:

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python simple_app.py
```

Frontend:

```bash
cd frontend
npm install
npm start
```

If you want the larger production-oriented backend path, use `backend/app.py` and configure Redis, Celery, secrets, and admin credentials before starting it.

## Usage

1. Sign in with the configured credentials. The Docker release defaults to `admin / admin123`.
2. Choose `VPN`, `Firewall`, or `VPN Shutdown`.
3. Upload a `.txt`, `.log`, or `.csv` file.
4. Review the preview table and record counts.
5. Download the generated CSV output.

## API Endpoints In Docker Release

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/verify`
- `POST /api/parse/vpn`
- `POST /api/parse/firewall`
- `POST /api/parse/vpn-shutdown`
- `GET /api/download/{filename}`
- `GET /api/history`

Additional endpoints such as registration, password changes, and task polling are available in the full `backend/app.py` path rather than the simplified Docker release path.

## Configuration Notes

### Local Docker Defaults

- `docker-compose.yml` exposes `8080 -> frontend` and `8000 -> backend`
- `docker-compose-alt.yml` exposes `3001 -> frontend` and `5001 -> backend`
- The local compose files run with `FLASK_ENV=development`
- The backend image installs from `backend/requirements.txt`

### Production Deployment

Before using the full backend in production:

- Set `SECRET_KEY`
- Set `JWT_SECRET_KEY`
- Set `ADMIN_USER`
- Set `ADMIN_PASSWORD`
- Configure Redis and Celery broker URLs
- Run behind HTTPS
- Restrict `CORS_ORIGINS`

See [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment notes.

## Troubleshooting

1. Rebuild after backend dependency changes:

```bash
docker compose up --build -d
```

2. Check container status:

```bash
docker compose ps
```

3. Review logs:

```bash
docker compose logs --tail=200 backend frontend
```

4. Verify the backend directly:

```bash
curl http://localhost:8000/api/health
```

## Development

Run backend tests:

```bash
cd backend
python -m pytest
```

Run frontend tests:

```bash
cd frontend
npm test
```

## License

Developed by IONSec Research Team.
