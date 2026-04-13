"""
CSV Parser Service for Log Files

This module provides a service class for parsing log files in CSV format,
with smart format detection and validation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import ipaddress

try:
    import pandas as pd
except ImportError:
    raise ImportError("pandas is required. Install with: pip install pandas")


class CSVParserService:
    """
    Service class for parsing CSV formatted log files.
    
    This class handles CSV files with various column naming conventions
    and provides automatic format detection.
    
    Example:
        >>> parser = CSVParserService()
        >>> format_type = parser.detect_format('logs.csv')
        >>> if format_type == 'csv':
        ...     df = parser.parse_csv_vpn_logs('logs.csv')
    """
    
    # CSV column aliases
    VPN_COLUMN_ALIASES = {
        'user': ['user', 'username', 'login', 'login_user', 'user_name'],
        'date': ['date', 'login_date', 'login_date', 'date_time'],
        'time': ['time', 'login_time', 'login_time', 'timestamp'],
        'tunneltype': ['tunneltype', 'tunnel_type', 'tunnel', 'vpn_type'],
        'remip': ['remip', 'remote_ip', 'srcip', 'source_ip', 'client_ip'],
        'reason': ['reason', 'status', 'result', 'login_status', 'auth_result'],
        'msg': ['msg', 'message', 'description', 'log_message'],
    }
    
    FIREWALL_COLUMN_ALIASES = {
        'dstip': ['dstip', 'destination_ip', 'dest_ip', 'dst_ip', 'dest'],
        'sentbyte': ['sentbyte', 'sent_bytes', 'bytes_sent', 'sentbytes', 'bytes'],
    }
    
    SHUTDOWN_COLUMN_ALIASES = {
        'user': ['user', 'username', 'login', 'login_user'],
        'date': ['date', 'shutdown_date', 'end_date'],
        'time': ['time', 'shutdown_time', 'end_time'],
        'sentbyte': ['sentbyte', 'sent_bytes', 'bytes_sent', 'sentbytes'],
        'msg': ['msg', 'message', 'description'],
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the CSV parser service.
        
        Args:
            logger: Optional logger instance for debug output
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def detect_format(self, file_path: str) -> str:
        """
        Detect if the file is CSV format or Fortinet log format.
        
        Args:
            file_path: Path to the file to detect
            
        Returns:
            'csv' for CSV format, 'fortinet' for Fortinet format, 'unknown' if unclear
            
        Example:
            >>> parser = CSVParserService()
            >>> format_type = parser.detect_format('logs.csv')
            >>> print(format_type)
            'csv'
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as file:
                first_line = file.readline().strip()
                
                # Check for extension
                if path.suffix.lower() == '.csv':
                    # Additional validation for CSV format
                    if ',' in first_line or '\t' in first_line:
                        self.logger.debug(f"Detected CSV format: {file_path}")
                        return 'csv'
                
                # Check if it looks like CSV with common headers
                csv_indicators = [
                    'date,time,user',
                    'username,password',
                    'srcip,dstip',
                    'source,destination',
                    'timestamp',
                ]
                
                first_lower = first_line.lower()
                for indicator in csv_indicators:
                    if indicator in first_lower:
                        self.logger.debug(f"Detected CSV format by header: {file_path}")
                        return 'csv'
                
                # Check if it looks like Fortinet log format
                if 'date=' in first_line and 'time=' in first_line:
                    self.logger.debug(f"Detected Fortinet format: {file_path}")
                    return 'fortinet'
                
                # Try to parse as CSV and check structure
                try:
                    import pandas as pd
                    df = pd.read_csv(path, nrows=1)
                    if len(df.columns) > 1:
                        self.logger.debug(f"Detected CSV format by parsing: {file_path}")
                        return 'csv'
                except Exception:
                    pass
                
                self.logger.warning(f"Unknown format: {file_path}")
                return 'unknown'
                
        except Exception as e:
            self.logger.error(f"Error detecting format: {e}")
            return 'unknown'
    
    def _normalize_columns(self, df: pd.DataFrame, column_aliases: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Normalize column names using aliases.
        
        Args:
            df: DataFrame with potentially aliased column names
            column_aliases: Dictionary mapping standard names to aliases
            
        Returns:
            DataFrame with normalized column names
        """
        df.columns = df.columns.str.strip().str.lower()
        
        for standard_name, aliases in column_aliases.items():
            for alias in aliases:
                if alias in df.columns and standard_name not in df.columns:
                    df = df.rename(columns={alias: standard_name})
                    break
        
        return df
    
    def is_public_ip(self, ip: str) -> bool:
        """
        Check if an IP address is public (not private/local).
        
        Args:
            ip: IP address string
            
        Returns:
            True if IP is public, False otherwise
        """
        try:
            ip_obj = ipaddress.ip_address(str(ip))
            return not (
                ip_obj.is_private or
                ip_obj.is_loopback or
                ip_obj.is_link_local or
                ip_obj.is_multicast or
                ip_obj.is_reserved
            )
        except (ValueError, TypeError):
            return False
    
    def parse_csv_vpn_logs(self, file_path: str) -> pd.DataFrame:
        """
        Parse VPN logs from CSV format.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame with normalized VPN log data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Parsing CSV VPN logs from: {file_path}")
        
        try:
            df = pd.read_csv(path, on_bad_lines='warn')
            
            if df.empty:
                self.logger.warning("CSV file is empty")
                return pd.DataFrame(columns=['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg'])
            
            # Normalize column names
            df = self._normalize_columns(df, self.VPN_COLUMN_ALIASES)
            
            # Check for required columns
            required_columns = ['date', 'time', 'user']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Required columns missing: {missing_columns}")
            
            # Filter for successful logins if reason/status exists
            if 'reason' in df.columns:
                df = df[df['reason'].str.contains('success', case=False, na=False)]
            
            # Add missing columns with defaults
            defaults = {
                'tunneltype': 'ssl-web',
                'remip': 'unknown',
                'reason': 'login successfully',
                'msg': 'SSL tunnel established'
            }
            
            for col, default in defaults.items():
                if col not in df.columns:
                    df[col] = default
            
            # Select and order columns
            columns = ['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg']
            df = df[[col for col in columns if col in df.columns]]
            
            self.logger.info(f"Parsed {len(df)} VPN records from CSV")
            
            return df.reset_index(drop=True)
            
        except pd.errors.EmptyDataError:
            self.logger.error("CSV file is empty")
            return pd.DataFrame(columns=['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg'])
        except Exception as e:
            self.logger.error(f"Error parsing CSV VPN logs: {e}")
            raise
    
    def parse_csv_firewall_logs(self, file_path: str) -> pd.DataFrame:
        """
        Parse firewall logs from CSV format.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame with aggregated firewall data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Parsing CSV firewall logs from: {file_path}")
        
        try:
            df = pd.read_csv(path, on_bad_lines='warn')
            
            if df.empty:
                self.logger.warning("CSV file is empty")
                return pd.DataFrame(columns=['dstip', 'total_sentbyte', 'size_mb'])
            
            # Normalize column names
            df = self._normalize_columns(df, self.FIREWALL_COLUMN_ALIASES)
            
            # Check for required columns
            if 'dstip' not in df.columns or 'sentbyte' not in df.columns:
                raise ValueError("Required columns (dstip, sentbyte) not found in CSV")
            
            # Convert sentbyte to numeric
            df['sentbyte'] = pd.to_numeric(df['sentbyte'], errors='coerce')
            df = df.dropna(subset=['sentbyte'])
            
            # Filter for public IPs and aggregate
            public_ips_data: Dict[str, int] = {}
            
            for _, row in df.iterrows():
                dstip = str(row['dstip']).strip()
                
                if self.is_public_ip(dstip):
                    try:
                        sentbyte = int(row['sentbyte'])
                        public_ips_data[dstip] = public_ips_data.get(dstip, 0) + sentbyte
                    except (ValueError, TypeError):
                        continue
            
            # Create result DataFrame
            result_df = pd.DataFrame(
                list(public_ips_data.items()),
                columns=['dstip', 'total_sentbyte']
            )
            
            result_df['size_mb'] = result_df['total_sentbyte'] / (1024 * 1024)
            result_df = result_df.sort_values(by='total_sentbyte', ascending=False)
            
            self.logger.info(f"Parsed {len(result_df)} unique public IPs from CSV")
            
            return result_df.reset_index(drop=True)
            
        except pd.errors.EmptyDataError:
            self.logger.error("CSV file is empty")
            return pd.DataFrame(columns=['dstip', 'total_sentbyte', 'size_mb'])
        except Exception as e:
            self.logger.error(f"Error parsing CSV firewall logs: {e}")
            raise
    
    def parse_csv_vpn_shutdown_logs(
        self, 
        file_path: str, 
        target_user: str
    ) -> pd.DataFrame:
        """
        Parse VPN shutdown logs from CSV format for a specific user.
        
        Args:
            file_path: Path to the CSV file
            target_user: Username to filter (case-insensitive)
            
        Returns:
            DataFrame with shutdown session data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing or username is empty
        """
        path = Path(file_path)
        target_user_clean = target_user.strip().lower()
        
        if not target_user_clean:
            raise ValueError("Target username cannot be empty")
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Parsing CSV VPN shutdown logs from: {file_path}")
        self.logger.info(f"Filtering for user: {target_user}")
        
        try:
            df = pd.read_csv(path, on_bad_lines='warn')
            
            if df.empty:
                self.logger.warning("CSV file is empty")
                return pd.DataFrame(columns=['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB'])
            
            # Normalize column names
            df = self._normalize_columns(df, self.SHUTDOWN_COLUMN_ALIASES)
            
            # Check for required columns
            required_columns = ['date', 'time', 'user', 'sentbyte']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Required columns missing: {missing_columns}")
            
            # Filter by user (case-insensitive)
            df['user'] = df['user'].astype(str)
            df = df[df['user'].str.lower() == target_user_clean]
            
            # Filter for shutdown sessions if msg column exists
            if 'msg' in df.columns:
                df = df[df['msg'].str.contains('shutdown', case=False, na=False)]
            
            # Convert sentbyte to numeric
            df['sentbyte'] = pd.to_numeric(df['sentbyte'], errors='coerce')
            df = df.dropna(subset=['sentbyte'])
            
            # Calculate MB
            df['sent_bytes_in_MB'] = df['sentbyte'] / (1024 * 1024)
            
            # Select relevant columns
            result_columns = ['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB']
            df = df[[col for col in result_columns if col in df.columns]]
            
            self.logger.info(f"Parsed {len(df)} shutdown sessions for user '{target_user}' from CSV")
            
            return df.reset_index(drop=True)
            
        except pd.errors.EmptyDataError:
            self.logger.error("CSV file is empty")
            return pd.DataFrame(columns=['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB'])
        except Exception as e:
            self.logger.error(f"Error parsing CSV VPN shutdown logs: {e}")
            raise
