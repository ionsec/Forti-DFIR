.. _quickstart:

Quick Start Guide
=================

Get up and running with Forti-DFIR in minutes.

Prerequisites
-------------

Ensure you have:

- Python 3.11+ installed
- (Optional) Docker and Docker Compose
- (Optional) Node.js 18+ for web frontend

CLI Quick Start
---------------

.. code-block:: bash

   # 1. Clone the repository
   git clone https://github.com/ionsec/Forti-DFIR.git
   cd Forti-DFIR

   # 2. Install dependencies
   pip install pandas

   # 3. Run the CLI tool
   python log_parser.py

   # 4. Follow the interactive prompts
   # Choose option 1, 2, or 3
   # Provide file paths when prompted

Web App Quick Start (Docker)
----------------------------

.. code-block:: bash

   # 1. Navigate to web app directory
   cd Forti-DFIR/web_app

   # 2. Start with Docker Compose
   docker-compose up -d

   # 3. Access the application
   # Open http://localhost:3000 in your browser

   # 4. Login with default credentials
   # Username: admin
   # Password: admin123

Web App Quick Start (Manual)
-----------------------------

.. code-block:: bash

   # 1. Backend setup
   cd Forti-DFIR/web_app/backend
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or: venv\Scripts\activate  # Windows
   pip install -r requirements.txt

   # 2. Start Redis (required for Celery)
   redis-server

   # 3. Start Celery worker (new terminal)
   cd Forti-DFIR/web_app/backend
   source venv/bin/activate
   celery -A app.celery worker --loglevel=info

   # 4. Start Flask backend (new terminal)
   cd Forti-DFIR/web_app/backend
   source venv/bin/activate
   python app.py

   # 5. Start React frontend (new terminal)
   cd Forti-DFIR/web_app/frontend
   npm install
   npm start

   # 6. Access the application
   # Open http://localhost:3000 in your browser

Sample Log Files
----------------

VPN Log Format
~~~~~~~~~~~~~~

.. code-block:: text

   date=2024-01-15 time=10:30:00 user="john.doe" tunneltype="ssl-web" remip=203.0.113.1 reason="login successfully" msg="SSL tunnel established"
   date=2024-01-15 time=10:35:00 user="jane.smith" tunneltype="ssl-web" remip=198.51.100.1 reason="login successfully" msg="SSL tunnel established"

Firewall Log Format
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   date=2024-01-15 time=10:30:00 srcip=192.168.1.100 dstip=8.8.8.8 sentbyte=1500 action=accept
   date=2024-01-15 time=10:31:00 srcip=192.168.1.101 dstip=1.1.1.1 sentbyte=2500 action=accept

VPN Shutdown Log Format
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   date=2024-01-15 time=11:00:00 user="john.doe" sentbyte=600000000 msg="SSL tunnel shutdown"
   date=2024-01-15 time=12:00:00 user="jane.smith" sentbyte=450000000 msg="SSL tunnel shutdown"

Expected Output
---------------

VPN Parsed Output
~~~~~~~~~~~~~~~~~

.. csv-table:: VPN Log Output
   :header: date,time,user,tunneltype,remip,reason,msg
   :widths: 12,10,15,12,15,20,30

   2024-01-15,10:30:00,john.doe,ssl-web,203.0.113.1,login successfully,SSL tunnel established
   2024-01-15,10:35:00,jane.smith,ssl-web,198.51.100.1,login successfully,SSL tunnel established

Firewall Parsed Output
~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: Firewall Log Output
   :header: dstip,total_sentbyte,size_mb
   :widths: 15,20,10

   8.8.8.8,1500,0.00143
   1.1.1.1,2500,0.00238

VPN Shutdown Parsed Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: VPN Shutdown Output
   :header: date,time,user,sentbyte,sent_bytes_in_MB
   :widths: 12,10,15,15,18

   2024-01-15,11:00:00,john.doe,600000000,572.2
   2024-01-15,12:00:00,jane.smith,450000000,429.15

Next Steps
----------

- Read the :ref:`cli_guide` for detailed CLI usage
- Read the :ref:`web_app_guide` for web application features
- Review :ref:`security` guidelines before production deployment
- Explore :ref:`features` roadmap for upcoming capabilities
