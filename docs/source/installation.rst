.. _installation:

Installation
============

This section covers installation methods for Forti-DFIR.

Prerequisites
-------------

- Python 3.11 or higher
- Node.js 18+ (for web frontend)
- Redis server (for async processing)
- Docker (optional, for containerized deployment)

CLI Installation
----------------

For command-line only usage:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/ionsec/Forti-DFIR.git
   cd Forti-DFIR

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or: venv\Scripts\activate  # Windows

   # Install dependencies
   pip install pandas

   # Run the CLI
   python log_parser.py

Web Application Installation
-----------------------------

Manual Setup
~~~~~~~~~~~~

.. code-block:: bash

   cd Forti-DFIR/web_app

   # Backend setup
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Start Redis (required for Celery)
   redis-server

   # Start Celery worker (in separate terminal)
   celery -A app.celery worker --loglevel=info

   # Start Flask server
   python app.py

   # Frontend setup (in separate terminal)
   cd ../frontend
   npm install
   npm start

Docker Setup
~~~~~~~~~~~~

.. code-block:: bash

   cd Forti-DFIR/web_app
   docker-compose up -d

   # Access the application
   # Frontend: http://localhost:3000
   # Backend: http://localhost:5000

Quick Start Scripts
~~~~~~~~~~~~~~~~~~~

For macOS/Linux:

.. code-block:: bash

   cd Forti-DFIR/web_app
   ./run.sh

For Windows:

.. code-block:: batch

   cd Forti-DFIR\web_app
   run.bat

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~

Create a ``.env`` file in the backend directory:

.. code-block:: bash

   # Security (REQUIRED in production)
   SECRET_KEY=your-very-secure-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   
   # Database
   DATABASE_URL=sqlite:///forti_dfir.db
   
   # Redis
   REDIS_URL=redis://localhost:6379/0
   
   # Flask
   FLASK_ENV=production
   DEBUG=False
   
   # CORS
   CORS_ORIGINS=https://your-domain.com

Default Credentials
~~~~~~~~~~~~~~~~~~~

.. warning::

   Default credentials should be changed immediately in production!

- Username: ``admin``
- Password: ``admin123``

Production Deployment
---------------------

See :ref:`deployment_guide` for detailed production deployment instructions.
