.. _cli_guide:

CLI User Guide
==============

The command-line interface provides direct access to Forti-DFIR's parsing capabilities.

Basic Usage
-----------

.. code-block:: bash

   python log_parser.py

This starts an interactive session with three options:

.. code-block:: text

   Forti-DFIR - Fortinet Log Parser CLI Tool
   1. Parse VPN logs
   2. Parse and aggregate firewall logs
   3. Parse VPN shutdown sessions and extract sent bytes for a given user
   
   Enter your choice (1, 2, or 3):

Help Command
------------

Display usage information:

.. code-block:: bash

   python log_parser.py -help

VPN Log Parsing
---------------

Option 1 extracts successful VPN login details.

Input Requirements
~~~~~~~~~~~~~~~~~~

- Fortinet VPN log file (text format)
- Output file path for CSV

Example Session
~~~~~~~~~~~~~~~

.. code-block:: text

   Enter your choice (1, 2, or 3): 1
   Enter the path to the log file: vpn_logs.txt
   Enter the path to save the parsed logs: parsed_vpn.csv
   Data saved at parsed_vpn.csv

Output Format
~~~~~~~~~~~~~

.. list-table:: VPN Log CSV Output
   :widths: 20 80
   :header-rows: 1

   * - Column
     - Description
   * - date
     - Log entry date
   * - time
     - Log entry time
   * - user
     - VPN username
   * - tunneltype
     - Type of VPN tunnel
   * - remip
     - Remote IP address
   * - reason
     - Login reason/status
   * - msg
     - Additional message

Firewall Log Aggregation
-------------------------

Option 2 aggregates firewall traffic by destination IP.

Input Requirements
~~~~~~~~~~~~~~~~~~

- Fortinet firewall log file (text format)
- Output file path for CSV

Example Session
~~~~~~~~~~~~~~~

.. code-block:: text

   Enter your choice (1, 2, or 3): 2
   Enter the path to the log file: firewall_logs.txt
   Enter the path to save the parsed logs: parsed_firewall.csv
   Data saved at parsed_firewall.csv

Output Format
~~~~~~~~~~~~~

.. list-table:: Firewall Log CSV Output
   :widths: 20 80
   :header-rows: 1

   * - Column
     - Description
   * - dstip
     - Destination IP address (public IPs only)
   * - total_sentbyte
     - Total bytes sent to this IP
   * - size_mb
     - Total size in megabytes

VPN Shutdown Analysis
---------------------

Option 3 analyzes VPN session termination data for a specific user.

Input Requirements
~~~~~~~~~~~~~~~~~~

- Fortinet VPN log file (text format)
- Target username (case-insensitive)
- Output file path for CSV

Example Session
~~~~~~~~~~~~~~~

.. code-block:: text

   Enter your choice (1, 2, or 3): 3
   Enter the path to the log file: vpn_logs.txt
   Enter the user name to filter by: john.doe
   Enter the path to save the parsed logs: shutdown_john.csv
   Data saved at shutdown_john.csv

Output Format
~~~~~~~~~~~~~

.. list-table:: VPN Shutdown CSV Output
   :widths: 20 80
   :header-rows: 1

   * - Column
     - Description
   * - date
     - Session end date
   * - time
     - Session end time
   * - user
     - VPN username
   * - sentbyte
     - Bytes sent during session
   * - sent_bytes_in_MB
     - Size in megabytes

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**File Not Found Error**

.. code-block:: text

   FileNotFoundError: [Errno 2] No such file or directory: 'logs.txt'

Solution: Verify the file path is correct and the file exists.

**Invalid File Format**

.. code-block:: text

   No valid log entries found

Solution: Ensure the log file contains Fortinet-formatted entries with the required fields.

**Permission Denied**

.. code-block:: text

   PermissionError: [Errno 13] Permission denied: 'output.csv'

Solution: Check write permissions for the output directory.

Performance Tips
~~~~~~~~~~~~~~~~

For large log files:

1. Process files in batches
2. Use SSD storage for faster I/O
3. Consider using the web interface for async processing
4. Ensure sufficient RAM (8GB+ recommended)
