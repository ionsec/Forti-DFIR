.. _features:

Features Roadmap
================

This document outlines current features and planned enhancements for Forti-DFIR.

Current Features (v1.0)
----------------------

VPN Log Parsing
~~~~~~~~~~~~~~~

- Extract successful VPN login details
- Parse date, time, user, tunnel type, remote IP, reason, and message
- Support for Fortinet log format
- CSV export with structured data

Firewall Log Aggregation
~~~~~~~~~~~~~~~~~~~~~~~~~

- Aggregate traffic by destination IP
- Filter out private/local IP addresses
- Calculate total bytes transferred
- Sort by volume (descending)
- Export to CSV format

VPN Session Shutdown Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Extract session termination logs
- Filter by username (case-insensitive)
- Calculate data transfer volumes
- Generate user-specific reports

User Interface
~~~~~~~~~~~~~~

- Command-line interface (CLI)
- Modern web application
- User authentication
- File upload and download
- Real-time processing status

Planned Features
----------------

High Priority (v1.1)
~~~~~~~~~~~~~~~~~~~

Multi-Format Support
"""""""""""""""""""""

- Auto-detect log format (Fortinet, Syslog, CSV, JSON)
- Support for compressed files (gzip, zip, tar.gz)
- Binary log format parsing
- Custom format definitions via configuration

Enhanced Security
"""""""""""""""""""

- Two-factor authentication (TOTP)
- Session management dashboard
- Password reset flow
- API key management
- Audit logging

Database Backend
"""""""""""""""""

- SQLite for development
- PostgreSQL for production
- Query history and saved searches
- Data retention policies

Medium Priority (v1.2)
~~~~~~~~~~~~~~~~~~~~~

Advanced Analytics
"""""""""""""""""""

- Statistical analysis dashboard
- Anomaly detection algorithms
- Timeline visualization
- Trend analysis

Export Formats
""""""""""""""

- JSON export
- Excel export with formatting
- PDF report generation
- STIX/TAXII format for threat intelligence
- Markdown reports

Integration Features
""""""""""""""""""""

- SIEM integration (Splunk, ELK, QRadar)
- Threat intelligence feed correlation
- IP geolocation enrichment
- WHOIS lookup integration
- VirusTotal API integration

Lower Priority (v2.0)
~~~~~~~~~~~~~~~~~~~~

Real-Time Processing
"""""""""""""""""""""

- Live log tailing
- WebSocket streaming
- Real-time alerts
- Dashboard updates

Machine Learning
""""""""""""""""

- Anomaly detection models
- Pattern recognition
- Predictive analysis
- Threat classification

Collaboration
"""""""""""""

- Team workspaces
- Comment system
- Case management
- Report sharing

Enterprise Features
"""""""""""""""""""

- Role-based access control (RBAC)
- LDAP/Active Directory integration
- Single Sign-On (SSO)
- Multi-tenancy support

Feature Requests
----------------

To request a new feature:

1. Check existing issues on GitHub
2. Create a new issue with the "enhancement" label
3. Include: use case, expected behavior, priority

Contribution guidelines are in the :ref:`contributing` section.
