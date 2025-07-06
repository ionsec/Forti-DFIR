import pandas as pd
import ipaddress

class CSVParserService:
    def __init__(self):
        pass
    
    def detect_format(self, file_path):
        """Detect if the file is CSV format or Fortinet log format"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()
                
            # Check if it looks like CSV header
            csv_indicators = ['date,time,user', 'dstip,sentbyte', 'user,sentbyte']
            if any(indicator in first_line.lower() for indicator in csv_indicators):
                return 'csv'
            
            # Check if it looks like Fortinet log format
            if 'date=' in first_line and 'time=' in first_line:
                return 'fortinet'
                
            return 'unknown'
        except:
            return 'unknown'
    
    def parse_csv_vpn_logs(self, file_path):
        """Parse VPN logs from CSV format"""
        try:
            df = pd.read_csv(file_path)
            
            # Normalize column names (remove spaces, lowercase)
            df.columns = df.columns.str.strip().str.lower()
            
            # Check if required columns exist
            required_columns = ['date', 'time', 'user', 'reason']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # Try alternative column names
                column_mapping = {
                    'username': 'user',
                    'login_time': 'time',
                    'login_date': 'date',
                    'status': 'reason',
                    'result': 'reason'
                }
                
                for old_name, new_name in column_mapping.items():
                    if old_name in df.columns and new_name in missing_columns:
                        df = df.rename(columns={old_name: new_name})
                        missing_columns.remove(new_name)
            
            # Filter for successful logins
            if 'reason' in df.columns:
                df = df[df['reason'].str.contains('success', case=False, na=False)]
            
            # Ensure we have basic columns
            if 'date' not in df.columns or 'time' not in df.columns or 'user' not in df.columns:
                raise ValueError("Required columns (date, time, user) not found in CSV")
                
            # Add missing columns with default values if they don't exist
            if 'tunneltype' not in df.columns:
                df['tunneltype'] = 'ssl-web'
            if 'remip' not in df.columns:
                df['remip'] = 'unknown'
            if 'reason' not in df.columns:
                df['reason'] = 'login successfully'
            if 'msg' not in df.columns:
                df['msg'] = 'SSL tunnel established'
            
            # Reorder columns to match expected format
            columns_order = ['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg']
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to parse CSV VPN logs: {str(e)}")
    
    def parse_csv_firewall_logs(self, file_path):
        """Parse firewall logs from CSV format"""
        try:
            df = pd.read_csv(file_path)
            
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Check for required columns
            if 'dstip' not in df.columns or 'sentbyte' not in df.columns:
                # Try alternative column names
                column_mapping = {
                    'destination_ip': 'dstip',
                    'dest_ip': 'dstip',
                    'dst_ip': 'dstip',
                    'sent_bytes': 'sentbyte',
                    'bytes_sent': 'sentbyte',
                    'sentbytes': 'sentbyte'
                }
                
                for old_name, new_name in column_mapping.items():
                    if old_name in df.columns:
                        df = df.rename(columns={old_name: new_name})
            
            if 'dstip' not in df.columns or 'sentbyte' not in df.columns:
                raise ValueError("Required columns (dstip, sentbyte) not found in CSV")
            
            # Convert sentbyte to numeric
            df['sentbyte'] = pd.to_numeric(df['sentbyte'], errors='coerce')
            df = df.dropna(subset=['sentbyte'])
            
            # Filter for public IPs and aggregate
            public_ips_data = {}
            for _, row in df.iterrows():
                dstip = str(row['dstip']).strip()
                sentbyte = int(row['sentbyte'])
                
                if self.is_public_ip(dstip):
                    if dstip in public_ips_data:
                        public_ips_data[dstip] += sentbyte
                    else:
                        public_ips_data[dstip] = sentbyte
            
            # Create result dataframe
            result_df = pd.DataFrame(list(public_ips_data.items()), columns=['dstip', 'total_sentbyte'])
            result_df['size_mb'] = result_df['total_sentbyte'] / (1024 * 1024)
            result_df = result_df.sort_values(by='total_sentbyte', ascending=False)
            
            return result_df
            
        except Exception as e:
            raise Exception(f"Failed to parse CSV firewall logs: {str(e)}")
    
    def parse_csv_vpn_shutdown_logs(self, file_path, target_user):
        """Parse VPN shutdown logs from CSV format"""
        try:
            df = pd.read_csv(file_path)
            
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Check for required columns
            required_columns = ['date', 'time', 'user', 'sentbyte']
            column_mapping = {
                'username': 'user',
                'sent_bytes': 'sentbyte',
                'bytes_sent': 'sentbyte',
                'sentbytes': 'sentbyte'
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns and new_name not in df.columns:
                    df = df.rename(columns={old_name: new_name})
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Required columns {missing_columns} not found in CSV")
            
            # Filter by user (case-insensitive)
            df = df[df['user'].str.lower() == target_user.lower()]
            
            # Filter for shutdown sessions if msg column exists
            if 'msg' in df.columns:
                df = df[df['msg'].str.contains('shutdown', case=False, na=False)]
            
            # Convert sentbyte to numeric and calculate MB
            df['sentbyte'] = pd.to_numeric(df['sentbyte'], errors='coerce')
            df = df.dropna(subset=['sentbyte'])
            df['sent_bytes_in_MB'] = df['sentbyte'] / (1024 * 1024)
            
            # Select relevant columns
            result_columns = ['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB']
            existing_columns = [col for col in result_columns if col in df.columns]
            df = df[existing_columns]
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to parse CSV VPN shutdown logs: {str(e)}")
    
    def is_public_ip(self, ip):
        """Returns True if the IP is public, False if it is private/local."""
        try:
            return not ipaddress.ip_address(ip).is_private
        except:
            return False