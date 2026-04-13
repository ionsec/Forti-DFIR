"""
Log Parser Service for Fortinet Logs

This module provides a service class for parsing Fortinet VPN and firewall logs
with type hints, error handling, and logging support.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import ipaddress

try:
    import pandas as pd
except ImportError:
    raise ImportError("pandas is required. Install with: pip install pandas")


class LogParserService:
    """
    Service class for parsing Fortinet log files.
    
    This class provides methods to parse:
    - VPN login logs (successful logins)
    - Firewall traffic logs (aggregated by destination IP)
    - VPN shutdown sessions (filtered by user)
    
    Example:
        >>> parser = LogParserService()
        >>> df = parser.parse_vpn_logs('vpn_logs.txt')
        >>> print(f"Found {len(df)} successful logins")
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the log parser service.
        
        Args:
            logger: Optional logger instance for debug output
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Pre-compile regex patterns for better performance
        self._vpn_patterns = {
            'date': re.compile(r'date=(\S+)'),
            'time': re.compile(r'time=(\S+)'),
            'user': re.compile(r'user="([^"]+)"'),
            'tunneltype': re.compile(r'tunneltype="([^"]+)"'),
            'remip': re.compile(r'remip=([\d\.]+)'),
            'reason': re.compile(r'reason="([^"]+)"'),
            'msg': re.compile(r'msg="([^"]+)"')
        }
        
        self._firewall_patterns = {
            'dstip': re.compile(r'dstip=([\d\.]+)'),
            'sentbyte': re.compile(r'sentbyte=(\d+)')
        }
        
        self._shutdown_patterns = {
            'date': re.compile(r'date=(\S+)'),
            'time': re.compile(r'time=(\S+)'),
            'user': re.compile(r'user="([^"]+)"', flags=re.IGNORECASE),
            'sentbyte': re.compile(r'sentbyte=(\d+)'),
            'msg': re.compile(r'msg="([^"]+)"')
        }
    
    def parse_vpn_logs(self, file_path: str) -> pd.DataFrame:
        """
        Parse VPN logs and extract successful login details.
        
        Args:
            file_path: Path to the VPN log file
            
        Returns:
            DataFrame with columns: date, time, user, tunneltype, remip, reason, msg
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If file format is invalid
            
        Example:
            >>> parser = LogParserService()
            >>> df = parser.parse_vpn_logs('vpn_logs.txt')
            >>> print(df.columns.tolist())
            ['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg']
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        self.logger.info(f"Parsing VPN logs from: {file_path}")
        
        extracted_data: List[List[str]] = []
        lines_processed = 0
        lines_matched = 0
        
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as file:
                for line in file:
                    lines_processed += 1
                    
                    # Extract all fields using pre-compiled patterns
                    matches = {}
                    for key, pattern in self._vpn_patterns.items():
                        match = pattern.search(line)
                        matches[key] = match.group(1) if match else None
                    
                    # Check if all required fields exist
                    if all(matches.values()):
                        reason = matches['reason']
                        
                        # Only keep successful logins
                        if reason.lower() == "login successfully":
                            extracted_data.append([
                                matches['date'],
                                matches['time'],
                                matches['user'],
                                matches['tunneltype'],
                                matches['remip'],
                                reason,
                                matches['msg']
                            ])
                            lines_matched += 1
                            
                            if lines_processed % 50000 == 0:
                                self.logger.debug(f"Processed {lines_processed:,} lines...")
        
        except Exception as e:
            self.logger.error(f"Error parsing VPN logs: {e}")
            raise
        
        self.logger.info(
            f"VPN parsing complete: {lines_processed:,} lines processed, "
            f"{lines_matched:,} successful logins found"
        )
        
        df = pd.DataFrame(
            extracted_data,
            columns=['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg']
        )
        
        return df
    
    def is_public_ip(self, ip: str) -> bool:
        """
        Check if an IP address is public (not private/local).
        
        Args:
            ip: IP address string
            
        Returns:
            True if IP is public, False otherwise
            
        Example:
            >>> parser = LogParserService()
            >>> parser.is_public_ip('8.8.8.8')
            True
            >>> parser.is_public_ip('192.168.1.1')
            False
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            # Check if it's private (includes local, link-local, etc.)
            return not (
                ip_obj.is_private or
                ip_obj.is_loopback or
                ip_obj.is_link_local or
                ip_obj.is_multicast or
                ip_obj.is_reserved
            )
        except ValueError:
            self.logger.debug(f"Invalid IP address: {ip}")
            return False
    
    def parse_firewall_logs(self, file_path: str) -> pd.DataFrame:
        """
        Parse firewall logs and aggregate traffic by destination IP.
        
        This method filters out private/local IP addresses and calculates
        total bytes transferred to each public destination IP.
        
        Args:
            file_path: Path to the firewall log file
            
        Returns:
            DataFrame with columns: dstip, total_sentbyte, size_mb
            Sorted by total_sentbyte in descending order
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If file format is invalid
            
        Example:
            >>> parser = LogParserService()
            >>> df = parser.parse_firewall_logs('firewall_logs.txt')
            >>> print(df.head())
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        self.logger.info(f"Parsing firewall logs from: {file_path}")
        
        data: Dict[str, int] = {}
        lines_processed = 0
        lines_matched = 0
        private_ips_skipped = 0
        
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as file:
                for line in file:
                    lines_processed += 1
                    
                    dstip_match = self._firewall_patterns['dstip'].search(line)
                    sentbyte_match = self._firewall_patterns['sentbyte'].search(line)
                    
                    if dstip_match and sentbyte_match:
                        dstip = dstip_match.group(1)
                        
                        # Validate IP format
                        if not dstip.replace('.', '').isdigit():
                            continue
                        
                        # Only include public IPs
                        if self.is_public_ip(dstip):
                            try:
                                sentbyte = int(sentbyte_match.group(1))
                                data[dstip] = data.get(dstip, 0) + sentbyte
                                lines_matched += 1
                            except ValueError:
                                self.logger.debug(f"Invalid sentbyte value in line {lines_processed}")
                                continue
                        else:
                            private_ips_skipped += 1
                    
                    if lines_processed % 50000 == 0:
                        self.logger.debug(f"Processed {lines_processed:,} lines...")
        
        except Exception as e:
            self.logger.error(f"Error parsing firewall logs: {e}")
            raise
        
        self.logger.info(
            f"Firewall parsing complete: {lines_processed:,} lines processed, "
            f"{lines_matched:,} public IP entries found, "
            f"{private_ips_skipped:,} private IPs skipped"
        )
        
        df = pd.DataFrame(list(data.items()), columns=['dstip', 'total_sentbyte'])
        
        # Convert bytes to megabytes
        df['size_mb'] = df['total_sentbyte'] / (1024 * 1024)
        
        # Sort by total bytes in descending order
        df = df.sort_values(by='total_sentbyte', ascending=False)
        
        return df.reset_index(drop=True)
    
    def parse_vpn_shutdown_sentbytes(
        self, 
        file_path: str, 
        target_user: str
    ) -> pd.DataFrame:
        """
        Parse VPN shutdown sessions for a specific user.
        
        This method filters VPN logs for "SSL tunnel shutdown" messages
        and extracts session data for the specified user.
        
        Args:
            file_path: Path to the VPN log file
            target_user: Username to filter (case-insensitive)
            
        Returns:
            DataFrame with columns: date, time, user, sentbyte, sent_bytes_in_MB
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If target_user is empty
            
        Example:
            >>> parser = LogParserService()
            >>> df = parser.parse_vpn_shutdown_sentbytes('vpn_logs.txt', 'john.doe')
            >>> print(f"Total data: {df['sent_bytes_in_MB'].sum():.2f} MB")
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        target_user_clean = target_user.strip().lower()
        
        if not target_user_clean:
            raise ValueError("Target username cannot be empty")
        
        self.logger.info(f"Parsing VPN shutdown sessions from: {file_path}")
        self.logger.info(f"Filtering for user: {target_user}")
        
        extracted_data: List[List[Any]] = []
        lines_processed = 0
        lines_matched = 0
        
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as file:
                for line in file:
                    lines_processed += 1
                    
                    # Check for shutdown message
                    msg_match = self._shutdown_patterns['msg'].search(line)
                    
                    if msg_match and msg_match.group(1) == "SSL tunnel shutdown":
                        # Filter by user
                        user_match = self._shutdown_patterns['user'].search(line)
                        
                        if user_match and user_match.group(1).lower() == target_user_clean:
                            date_match = self._shutdown_patterns['date'].search(line)
                            time_match = self._shutdown_patterns['time'].search(line)
                            sentbyte_match = self._shutdown_patterns['sentbyte'].search(line)
                            
                            if all([date_match, time_match, sentbyte_match]):
                                try:
                                    sentbyte = int(sentbyte_match.group(1))
                                    extracted_data.append([
                                        date_match.group(1),
                                        time_match.group(1),
                                        user_match.group(1),
                                        sentbyte,
                                        sentbyte / (1024 * 1024)
                                    ])
                                    lines_matched += 1
                                except ValueError:
                                    self.logger.debug(f"Invalid sentbyte value in line {lines_processed}")
                                    continue
                    
                    if lines_processed % 50000 == 0:
                        self.logger.debug(f"Processed {lines_processed:,} lines...")
        
        except Exception as e:
            self.logger.error(f"Error parsing VPN shutdown logs: {e}")
            raise
        
        self.logger.info(
            f"VPN shutdown parsing complete: {lines_processed:,} lines processed, "
            f"{lines_matched:,} sessions found for user '{target_user}'"
        )
        
        df = pd.DataFrame(
            extracted_data,
            columns=['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB']
        )
        
        return df.reset_index(drop=True)
    
    def get_statistics(self, df: pd.DataFrame, log_type: str) -> Dict[str, Any]:
        """
        Get statistics from parsed log data.
        
        Args:
            df: Parsed DataFrame
            log_type: Type of log ('vpn', 'firewall', 'vpn_shutdown')
            
        Returns:
            Dictionary of statistics
            
        Example:
            >>> parser = LogParserService()
            >>> df = parser.parse_vpn_logs('vpn_logs.txt')
            >>> stats = parser.get_statistics(df, 'vpn')
            >>> print(stats)
        """
        stats: Dict[str, Any] = {
            'total_records': len(df),
            'log_type': log_type
        }
        
        if df.empty:
            return stats
        
        if log_type == 'vpn':
            if 'user' in df.columns:
                stats['unique_users'] = df['user'].nunique()
                stats['top_users'] = df['user'].value_counts().head(5).to_dict()
            
            if 'remip' in df.columns:
                stats['unique_ips'] = df['remip'].nunique()
            
        elif log_type == 'firewall':
            if 'total_sentbyte' in df.columns:
                stats['total_bytes'] = df['total_sentbyte'].sum()
                stats['total_mb'] = df['size_mb'].sum()
                stats['avg_bytes_per_ip'] = df['total_sentbyte'].mean()
                stats['top_destinations'] = df.head(5)[['dstip', 'size_mb']].to_dict('records')
            
        elif log_type == 'vpn_shutdown':
            if 'sent_bytes_in_MB' in df.columns:
                stats['total_mb'] = df['sent_bytes_in_MB'].sum()
                stats['avg_session_mb'] = df['sent_bytes_in_MB'].mean()
                stats['total_sessions'] = len(df)
        
        return stats
