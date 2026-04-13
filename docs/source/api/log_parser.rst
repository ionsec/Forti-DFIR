log\_parser Module
==================

Core CLI parser module for Fortinet logs.

Module Contents
---------------

.. autofunction:: print_help

.. autofunction:: parse_vpn_logs

.. autofunction:: is_public_ip

.. autofunction:: parse_firewall_logs

.. autofunction:: parse_vpn_shutdown_sentbytes_csv

.. autofunction:: main

Usage Example
-------------

.. code-block:: python

   from log_parser import parse_vpn_logs, parse_firewall_logs
   
   # Parse VPN logs
   vpn_df = parse_vpn_logs('vpn_logs.txt')
   print(f"Found {len(vpn_df)} successful logins")
   
   # Parse firewall logs
   fw_df = parse_firewall_logs('firewall_logs.txt')
   print(f"Aggregated {len(fw_df)} unique destination IPs")
