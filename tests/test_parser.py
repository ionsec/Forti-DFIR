"""
Unit tests for Log Parser Service and CSV Parser Service.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'web_app' / 'backend'))

from log_parser_service import LogParserService
from csv_parser_service import CSVParserService


class TestLogParserService:
    """Tests for LogParserService."""
    
    @pytest.fixture
    def parser(self):
        """Create a LogParserService instance."""
        return LogParserService()
    
    @pytest.fixture
    def sample_vpn_log(self, tmp_path):
        """Create a sample VPN log file."""
        log_content = '''date=2024-01-15 time=10:30:00 user="john.doe" tunneltype="ssl-web" remip=203.0.113.1 reason="login successfully" msg="SSL tunnel established"
date=2024-01-15 time=10:35:00 user="jane.smith" tunneltype="ssl-web" remip=198.51.100.1 reason="login successfully" msg="SSL tunnel established"
date=2024-01-15 time=10:40:00 user="john.doe" tunneltype="ssl-web" remip=203.0.113.5 reason="login failed" msg="Authentication error"
'''
        log_file = tmp_path / "vpn.log"
        log_file.write_text(log_content)
        return str(log_file)
    
    @pytest.fixture
    def sample_firewall_log(self, tmp_path):
        """Create a sample firewall log file."""
        log_content = '''date=2024-01-15 time=10:30:00 srcip=192.168.1.100 dstip=8.8.8.8 sentbyte=1500 action=accept
date=2024-01-15 time=10:31:00 srcip=192.168.1.101 dstip=1.1.1.1 sentbyte=2500 action=accept
date=2024-01-15 time=10:32:00 srcip=192.168.1.100 dstip=192.168.1.1 sentbyte=500 action=accept
date=2024-01-15 time=10:33:00 srcip=192.168.1.102 dstip=8.8.8.8 sentbyte=3000 action=accept
'''
        log_file = tmp_path / "firewall.log"
        log_file.write_text(log_content)
        return str(log_file)
    
    @pytest.fixture
    def sample_shutdown_log(self, tmp_path):
        """Create a sample VPN shutdown log file."""
        log_content = '''date=2024-01-15 time=11:00:00 user="john.doe" sentbyte=600000000 msg="SSL tunnel shutdown"
date=2024-01-15 time=12:00:00 user="jane.smith" sentbyte=450000000 msg="SSL tunnel shutdown"
date=2024-01-15 time=13:00:00 user="john.doe" sentbyte=300000000 msg="SSL tunnel shutdown"
'''
        log_file = tmp_path / "shutdown.log"
        log_file.write_text(log_content)
        return str(log_file)
    
    def test_parse_vpn_logs_success(self, parser, sample_vpn_log):
        """Test successful VPN log parsing."""
        df = parser.parse_vpn_logs(sample_vpn_log)
        
        assert len(df) == 2  # Only successful logins
        assert 'user' in df.columns
        assert 'remip' in df.columns
        assert df.iloc[0]['user'] == 'john.doe'
        assert df.iloc[1]['user'] == 'jane.smith'
    
    def test_parse_vpn_logs_empty_file(self, parser, tmp_path):
        """Test parsing empty VPN log file."""
        log_file = tmp_path / "empty.log"
        log_file.write_text('')
        
        df = parser.parse_vpn_logs(str(log_file))
        assert df.empty
    
    def test_parse_vpn_logs_file_not_found(self, parser):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError):
            parser.parse_vpn_logs('/nonexistent/file.log')
    
    def test_is_public_ip(self, parser):
        """Test public IP detection."""
        # Public IPs
        assert parser.is_public_ip('8.8.8.8') == True
        assert parser.is_public_ip('1.1.1.1') == True
        assert parser.is_public_ip('203.0.113.1') == True
        
        # Private IPs
        assert parser.is_public_ip('192.168.1.1') == False
        assert parser.is_public_ip('10.0.0.1') == False
        assert parser.is_public_ip('172.16.0.1') == False
        
        # Localhost
        assert parser.is_public_ip('127.0.0.1') == False
        
        # Invalid
        assert parser.is_public_ip('invalid') == False
    
    def test_parse_firewall_logs_success(self, parser, sample_firewall_log):
        """Test successful firewall log parsing."""
        df = parser.parse_firewall_logs(sample_firewall_log)
        
        assert len(df) == 2  # Only public IPs (8.8.8.8 and 1.1.1.1)
        assert 'dstip' in df.columns
        assert 'total_sentbyte' in df.columns
        assert 'size_mb' in df.columns
        
        # Check aggregation - 8.8.8.8 should have 4500 bytes total
        eight_eight = df[df['dstip'] == '8.8.8.8']
        assert len(eight_eight) == 1
        assert eight_eight.iloc[0]['total_sentbyte'] == 4500
    
    def test_parse_firewall_logs_sorting(self, parser, sample_firewall_log):
        """Test firewall logs are sorted by bytes descending."""
        df = parser.parse_firewall_logs(sample_firewall_log)
        
        # Should be sorted descending by total_sentbyte
        assert df.iloc[0]['total_sentbyte'] >= df.iloc[1]['total_sentbyte']
    
    def test_parse_vpn_shutdown_success(self, parser, sample_shutdown_log):
        """Test successful VPN shutdown parsing."""
        df = parser.parse_vpn_shutdown_sentbytes(sample_shutdown_log, 'john.doe')
        
        assert len(df) == 2  # Two shutdown sessions for john.doe
        assert 'sent_bytes_in_MB' in df.columns
        assert df.iloc[0]['user'] == 'john.doe'
    
    def test_parse_vpn_shutdown_case_insensitive(self, parser, sample_shutdown_log):
        """Test VPN shutdown parsing is case-insensitive."""
        df = parser.parse_vpn_shutdown_sentbytes(sample_shutdown_log, 'JOHN.DOE')
        
        assert len(df) == 2
        assert df.iloc[0]['user'].lower() == 'john.doe'
    
    def test_parse_vpn_shutdown_empty_user(self, parser, sample_shutdown_log):
        """Test VPN shutdown parsing with empty username."""
        with pytest.raises(ValueError):
            parser.parse_vpn_shutdown_sentbytes(sample_shutdown_log, '')
    
    def test_get_statistics_vpn(self, parser, sample_vpn_log):
        """Test statistics generation for VPN logs."""
        df = parser.parse_vpn_logs(sample_vpn_log)
        stats = parser.get_statistics(df, 'vpn')
        
        assert 'total_records' in stats
        assert stats['total_records'] == 2
        assert 'unique_users' in stats
        assert stats['unique_users'] == 2
    
    def test_get_statistics_firewall(self, parser, sample_firewall_log):
        """Test statistics generation for firewall logs."""
        df = parser.parse_firewall_logs(sample_firewall_log)
        stats = parser.get_statistics(df, 'firewall')
        
        assert 'total_records' in stats
        assert 'total_bytes' in stats
        assert 'total_mb' in stats


class TestCSVParserService:
    """Tests for CSVParserService."""
    
    @pytest.fixture
    def parser(self):
        """Create a CSVParserService instance."""
        return CSVParserService()
    
    @pytest.fixture
    def sample_csv_vpn(self, tmp_path):
        """Create a sample VPN CSV file."""
        csv_content = '''date,time,user,tunneltype,remip,reason,msg
2024-01-15,10:30:00,john.doe,ssl-web,203.0.113.1,login successfully,SSL tunnel established
2024-01-15,10:35:00,jane.smith,ssl-web,198.51.100.1,login successfully,SSL tunnel established
2024-01-15,10:40:00,test.user,ssl-web,203.0.113.5,login failed,Auth error
'''
        csv_file = tmp_path / "vpn.csv"
        csv_file.write_text(csv_content)
        return str(csv_file)
    
    @pytest.fixture
    def sample_csv_firewall(self, tmp_path):
        """Create a sample firewall CSV file."""
        csv_content = '''dstip,sentbyte
8.8.8.8,1500
1.1.1.1,2500
192.168.1.1,500
8.8.8.8,3000
'''
        csv_file = tmp_path / "firewall.csv"
        csv_file.write_text(csv_content)
        return str(csv_file)
    
    def test_detect_format_csv(self, parser, sample_csv_vpn):
        """Test format detection for CSV."""
        format_type = parser.detect_format(sample_csv_vpn)
        assert format_type == 'csv'
    
    def test_detect_format_fortinet(self, parser, tmp_path):
        """Test format detection for Fortinet."""
        log_content = 'date=2024-01-15 time=10:30:00 user="test"'
        log_file = tmp_path / "fortinet.log"
        log_file.write_text(log_content)
        
        format_type = parser.detect_format(str(log_file))
        assert format_type == 'fortinet'
    
    def test_detect_format_file_not_found(self, parser):
        """Test format detection for non-existent file."""
        with pytest.raises(FileNotFoundError):
            parser.detect_format('/nonexistent/file.log')
    
    def test_parse_csv_vpn_logs_success(self, parser, sample_csv_vpn):
        """Test successful CSV VPN parsing."""
        df = parser.parse_csv_vpn_logs(sample_csv_vpn)
        
        assert len(df) == 2  # Only successful logins
        assert 'user' in df.columns
        assert df.iloc[0]['user'] == 'john.doe'
    
    def test_parse_csv_vpn_logs_with_aliases(self, parser, tmp_path):
        """Test CSV VPN parsing with column aliases."""
        csv_content = '''login_date,login_time,username,tunnel_type,remote_ip,status
2024-01-15,10:30:00,john.doe,ssl-web,203.0.113.1,success
'''
        csv_file = tmp_path / "vpn_aliases.csv"
        csv_file.write_text(csv_content)
        
        df = parser.parse_csv_vpn_logs(str(csv_file))
        assert len(df) == 1
        assert 'user' in df.columns
    
    def test_parse_csv_firewall_logs_success(self, parser, sample_csv_firewall):
        """Test successful CSV firewall parsing."""
        df = parser.parse_csv_firewall_logs(sample_csv_firewall)
        
        # Should only have public IPs (8.8.8.8 and 1.1.1.1)
        assert len(df) == 2
        
        # Check aggregation - 8.8.8.8 should have 4500 bytes
        eight_eight = df[df['dstip'] == '8.8.8.8']
        assert eight_eight.iloc[0]['total_sentbyte'] == 4500
    
    def test_parse_csv_vpn_shutdown_logs_success(self, parser, tmp_path):
        """Test successful CSV VPN shutdown parsing."""
        csv_content = '''date,time,user,sentbyte,msg
2024-01-15,11:00:00,john.doe,600000000,SSL tunnel shutdown
2024-01-15,12:00:00,jane.smith,450000000,SSL tunnel shutdown
2024-01-15,13:00:00,john.doe,300000000,SSL tunnel shutdown
'''
        csv_file = tmp_path / "shutdown.csv"
        csv_file.write_text(csv_content)
        
        df = parser.parse_csv_vpn_shutdown_logs(str(csv_file), 'john.doe')
        
        assert len(df) == 2
        assert 'sent_bytes_in_MB' in df.columns
        assert all(df['user'].str.lower() == 'john.doe')
    
    def test_parse_csv_empty_file(self, parser, tmp_path):
        """Test parsing empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text('')
        
        df = parser.parse_csv_vpn_logs(str(csv_file))
        assert df.empty
    
    def test_is_public_ip(self, parser):
        """Test public IP detection."""
        assert parser.is_public_ip('8.8.8.8') == True
        assert parser.is_public_ip('192.168.1.1') == False
        assert parser.is_public_ip('invalid') == False


class TestSecurity:
    """Tests for security utilities."""
    
    def test_sanitize_username(self):
        """Test username sanitization."""
        from utils.security import sanitize_username
        
        # Valid usernames
        assert sanitize_username('john.doe') == 'john.doe'
        assert sanitize_username('user123') == 'user123'
        assert sanitize_username('test_user') == 'test_user'
        
        # Invalid usernames
        assert sanitize_username('') is None
        assert sanitize_username('a' * 100) is None  # Too long
        assert sanitize_username('<script>') is None  # Dangerous chars
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from utils.security import sanitize_filename
        
        # Valid filenames
        assert sanitize_filename('log.txt') == 'log.txt'
        assert sanitize_filename('data.csv') == 'data.csv'
        
        # Invalid filenames should raise
        with pytest.raises(ValueError):
            sanitize_filename('')
        
        with pytest.raises(ValueError):
            sanitize_filename('../../../etc/passwd')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
