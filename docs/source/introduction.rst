.. _introduction:

Introduction
=============

Welcome to Forti-DFIR! This documentation provides comprehensive information about using and developing the Fortinet Log Parser for Digital Forensics and Incident Response (DFIR) investigations.

What is Forti-DFIR?
-------------------

Forti-DFIR is a comprehensive solution for analyzing Fortinet VPN and firewall logs. It extracts key data and exports it to CSV format, streamlining security investigations for incident responders.

Key Features
------------

- **VPN Login Parser**: Extracts successful VPN login details including date, time, user, tunnel type, remote IP, and reason
- **Firewall Log Aggregation**: Summarizes traffic by destination IP, filtering out private/local addresses
- **VPN Session Shutdown Analyzer**: Extracts session termination statistics including sent bytes for specific users
- **Interactive CLI Interface**: Guides users through log selection and parsing options
- **Modern Web Application**: Features authentication, file upload, real-time processing, and CSV download
- **Multi-Format Support**: Handles both Fortinet log format and CSV input
- **Docker Support**: Easy deployment with Docker Compose
- **Cloud Ready**: Automatic deployment configurations for Netlify and Vercel

Use Cases
---------

Security Investigations
~~~~~~~~~~~~~~~~~~~~~~~

- Track unauthorized VPN access attempts
- Analyze data exfiltration patterns
- Investigate insider threats
- Correlate network traffic anomalies

Compliance Reporting
~~~~~~~~~~~~~~~~~~~~

- Generate audit trails for regulatory compliance
- Document user access patterns
- Create data transfer reports

Threat Intelligence
~~~~~~~~~~~~~~~~~~~

- Extract IOCs from firewall logs
- Identify C2 communication patterns
- Map external threat actor infrastructure

Architecture Overview
---------------------

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │                        Forti-DFIR                            │
   ├───────────────────────────────────────────────────────────────┤
   │                                                              │
   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
   │   │    CLI      │    │  Web App    │    │    API      │     │
   │   │  Interface  │    │  Interface  │    │  Endpoints  │     │
   │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
   │          │                  │                   │           │
   │          └──────────────────┼───────────────────┘           │
   │                             │                               │
   │                   ┌─────────▼─────────┐                    │
   │                   │  Log Parser Core  │                    │
   │                   │    (log_parser)   │                    │
   │                   └─────────┬─────────┘                    │
   │                             │                               │
   │          ┌──────────────────┼──────────────────┐           │
   │          │                  │                  │           │
   │   ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐    │
   │   │ VPN Parser  │    │ Firewall    │    │ VPN Session │    │
   │   │             │    │ Parser      │    │ Shutdown    │    │
   │   └─────────────┘    └─────────────┘    └─────────────┘    │
   │                                                              │
   └─────────────────────────────────────────────────────────────┘

Technology Stack
----------------

Backend
~~~~~~~

- **Python 3.11+**: Modern Python with type hints
- **Flask 3.0**: Web framework
- **Pandas**: Data processing
- **Celery**: Async task processing
- **Redis**: Message broker and caching
- **JWT**: Authentication

Frontend
~~~~~~~~

- **React 18**: UI framework
- **Modern CSS**: Responsive design

Deployment
~~~~~~~~~~

- **Docker**: Containerization
- **Gunicorn**: WSGI server
- **Nginx**: Reverse proxy (production)

Support
-------

For issues and feature requests, please use the GitHub issue tracker:

- https://github.com/ionsec/Forti-DFIR/issues

License
-------

This project is developed by the IONSec Research Team.
