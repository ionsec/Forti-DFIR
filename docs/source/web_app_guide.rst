.. _web_app_guide:

Web Application Guide
=====================

The web application provides a modern interface for Forti-DFIR's parsing capabilities.

Getting Started
---------------

Starting the Application
~~~~~~~~~~~~~~~~~~~~~~~~~

Using Docker (Recommended):

.. code-block:: bash

   cd web_app
   docker-compose up -d

Manual Setup:

.. code-block:: bash

   # Terminal 1: Backend
   cd web_app/backend
   source venv/bin/activate
   pip install -r requirements.txt
   python app.py
   
   # Terminal 2: Celery Worker
   cd web_app/backend
   celery -A app.celery worker --loglevel=info
   
   # Terminal 3: Frontend
   cd web_app/frontend
   npm install
   npm start

Accessing the Application
~~~~~~~~~~~~~~~~~~~~~~~~~

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

Default Credentials
~~~~~~~~~~~~~~~~~~~

.. warning::

   Change these credentials in production!

- Username: ``admin``
- Password: ``admin123``

User Interface
--------------

Login Screen
~~~~~~~~~~~~

The login screen provides:

- Username/password authentication
- Remember me functionality
- Secure session management

Dashboard
~~~~~~~~~

After login, the dashboard shows:

- Parser type selection (VPN, Firewall, VPN Shutdown)
- File upload area
- Processing status
- Results preview

Parser Types
~~~~~~~~~~~~

**VPN Logs Parser**

Extracts successful VPN login details from log files.

1. Select "VPN Logs" parser type
2. Upload your log file (.txt, .log, or .csv)
3. Click "Parse File"
4. View results and download CSV

**Firewall Logs Parser**

Aggregates firewall traffic by destination IP.

1. Select "Firewall Logs" parser type
2. Upload your log file
3. Click "Parse File"
4. View aggregated results

**VPN Shutdown Parser**

Analyzes VPN session termination data for specific users.

1. Select "VPN Shutdown" parser type
2. Enter the username to filter
3. Upload your log file
4. Click "Parse File"

API Endpoints
-------------

Authentication
~~~~~~~~~~~~~~

**POST /api/auth/login**

Request:

.. code-block:: json

   {
     "username": "admin",
     "password": "admin123"
   }

Response:

.. code-block:: json

   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "username": "admin"
   }

**GET /api/auth/verify**

Headers:

.. code-block:: text

   Authorization: Bearer <token>

Response:

.. code-block:: json

   {
     "valid": true,
     "username": "admin"
   }

Parsing
~~~~~~~

**POST /api/parse/vpn**

Headers:

.. code-block:: text

   Authorization: Bearer <token>
   Content-Type: multipart/form-data

Request: File upload with key "file"

Response:

.. code-block:: json

   {
     "task_id": "abc123",
     "status": "processing",
     "message": "VPN log parsing started"
   }

**POST /api/parse/firewall**

Similar to VPN endpoint.

**POST /api/parse/vpn-shutdown**

Additional form field: ``username`` for user filtering.

**GET /api/task/<task_id>**

Check processing status:

.. code-block:: json

   {
     "state": "SUCCESS",
     "result": {
       "status": "completed",
       "records": 1523,
       "filename": "vpn_parsed_20240115.csv"
     }
   }

Downloads
~~~~~~~~~

**GET /api/download/<filename>**

Download processed CSV file.

Headers:

.. code-block:: text

   Authorization: Bearer <token>

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~

Create ``.env`` file in backend directory:

.. code-block:: bash

   # Security
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   
   # Redis
   REDIS_URL=redis://localhost:6379/0
   
   # Flask
   FLASK_ENV=development
   DEBUG=True
   
   # CORS
   CORS_ORIGINS=http://localhost:3000

Rate Limiting
~~~~~~~~~~~~~

Default limits:

- General: 200 requests/day, 50 requests/hour
- Login: 5 requests/minute
- Parsing: 10 requests/minute

Deployment
----------

Production Checklist
~~~~~~~~~~~~~~~~~~~

- [ ] Change default credentials
- [ ] Set secure SECRET_KEY and JWT_SECRET_KEY
- [ ] Set FLASK_ENV=production
- [ ] Set DEBUG=False
- [ ] Configure HTTPS
- [ ] Set appropriate CORS origins
- [ ] Configure Redis persistence
- [ ] Set up log rotation
- [ ] Configure backup for results directory

Docker Deployment
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   version: '3.8'
   services:
     frontend:
       build: ./frontend
       ports:
         - "3000:80"
       depends_on:
         - backend
     
     backend:
       build: ./backend
       ports:
         - "5000:5000"
       environment:
         - SECRET_KEY=${SECRET_KEY}
         - JWT_SECRET_KEY=${JWT_SECRET_KEY}
       depends_on:
         - redis
     
     redis:
       image: redis:7-alpine
       volumes:
         - redis_data:/data

   volumes:
     redis_data:
