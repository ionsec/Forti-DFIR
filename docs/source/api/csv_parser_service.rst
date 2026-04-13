csv\_parser\_service Module
===========================

Service class for CSV format log parsing.

Class Reference
---------------

.. autoclass:: CSVParserService
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
-------------

.. code-block:: python

   from csv_parser_service import CSVParserService
   
   parser = CSVParserService()
   
   # Detect format
   format_type = parser.detect_format('logs.txt')
   print(f"Detected format: {format_type}")
   
   # Parse CSV VPN logs
   if format_type == 'csv':
       df = parser.parse_csv_vpn_logs('logs.csv')
