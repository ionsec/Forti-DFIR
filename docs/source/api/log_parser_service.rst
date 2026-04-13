log\_parser\_service Module
===========================

Service class for log parsing operations.

Class Reference
---------------

.. autoclass:: LogParserService
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
-------------

.. code-block:: python

   from log_parser_service import LogParserService
   
   parser = LogParserService()
   
   # Parse VPN logs
   vpn_df = parser.parse_vpn_logs('vpn_logs.txt')
   
   # Parse firewall logs
   fw_df = parser.parse_firewall_logs('firewall_logs.txt')
   
   # Parse VPN shutdown sessions for specific user
   shutdown_df = parser.parse_vpn_shutdown_sentbytes('vpn_logs.txt', 'john.doe')
