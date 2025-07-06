import re
import pandas as pd
import ipaddress

class LogParserService:
    def __init__(self):
        pass
    
    def parse_vpn_logs(self, file_path):
        """Parses VPN logs and extracts date, time, user, tunneltype, remip, reason, and msg only for successful logins."""
        date_pattern = re.compile(r'date=(\S+)')
        time_pattern = re.compile(r'time=(\S+)')
        user_pattern = re.compile(r'user="([^"]+)"')
        tunneltype_pattern = re.compile(r'tunneltype="([^"]+)"')
        remip_pattern = re.compile(r'remip=([\d\.]+)')
        reason_pattern = re.compile(r'reason="([^"]+)"')
        msg_pattern = re.compile(r'msg="([^"]+)"')

        extracted_data = []

        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                date_match = date_pattern.search(line)
                time_match = time_pattern.search(line)
                user_match = user_pattern.search(line)
                tunneltype_match = tunneltype_pattern.search(line)
                remip_match = remip_pattern.search(line)
                reason_match = reason_pattern.search(line)
                msg_match = msg_pattern.search(line)

                # Ensure all required fields exist in the log
                if date_match and time_match and user_match and tunneltype_match and remip_match and reason_match and msg_match:
                    date = date_match.group(1)
                    time = time_match.group(1)
                    user = user_match.group(1)
                    tunneltype = tunneltype_match.group(1)
                    remip = remip_match.group(1)
                    reason = reason_match.group(1)
                    msg = msg_match.group(1)

                    # Only keep logs where login was successful based on reason
                    if reason.lower() == "login successfully":
                        extracted_data.append([date, time, user, tunneltype, remip, reason, msg])

        df = pd.DataFrame(extracted_data, columns=['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg'])
        return df

    def is_public_ip(self, ip):
        """Returns True if the IP is public, False if it is private/local."""
        try:
            return not ipaddress.ip_address(ip).is_private
        except:
            return False

    def parse_firewall_logs(self, file_path):
        """Parses firewall logs, aggregates data by destination IP (excluding local IPs), sorts in descending order, and adds size in MB."""
        dstip_pattern = re.compile(r'dstip=([\d\.]+)')
        sentbyte_pattern = re.compile(r'sentbyte=(\d+)')
        
        data = {}
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                dstip_match = dstip_pattern.search(line)
                sentbyte_match = sentbyte_pattern.search(line)
                
                if dstip_match and sentbyte_match:
                    dstip = dstip_match.group(1)
                    sentbyte = int(sentbyte_match.group(1))
                    
                    # Exclude private/local IPs
                    if self.is_public_ip(dstip):
                        if dstip in data:
                            data[dstip] += sentbyte
                        else:
                            data[dstip] = sentbyte
        
        df = pd.DataFrame(list(data.items()), columns=['dstip', 'total_sentbyte'])
        
        # Convert bytes to megabytes
        df['size_mb'] = df['total_sentbyte'] / (1024 * 1024)

        # Sort data in descending order based on total sent bytes
        df = df.sort_values(by='total_sentbyte', ascending=False)
        
        return df

    def parse_vpn_shutdown_sentbytes(self, file_path, target_user):
        """
        Parses VPN logs to extract date, time, user, and sentbyte information for sessions 
        where the msg field equals "SSL tunnel shutdown". It then calculates the sent bytes in MB.
        
        Returns a DataFrame with the following columns:
        - date
        - time
        - user
        - sentbyte
        - sent_bytes_in_MB
        """
        # Define regex patterns for the fields of interest.
        date_pattern = re.compile(r'date=(\S+)')
        time_pattern = re.compile(r'time=(\S+)')
        user_pattern = re.compile(r'user="([^"]+)"', flags=re.IGNORECASE)
        sentbyte_pattern = re.compile(r'sentbyte=(\d+)')
        msg_pattern = re.compile(r'msg="([^"]+)"')

        extracted_data = []

        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Check if the message indicates a shutdown.
                msg_match = msg_pattern.search(line)
                if msg_match and msg_match.group(1) == "SSL tunnel shutdown":
                    # Filter by user (case-insensitive).
                    user_match = user_pattern.search(line)
                    if user_match and user_match.group(1).lower() == target_user.lower():
                        date_match = date_pattern.search(line)
                        time_match = time_pattern.search(line)
                        sentbyte_match = sentbyte_pattern.search(line)
                        if date_match and time_match and sentbyte_match:
                            date_val = date_match.group(1)
                            time_val = time_match.group(1)
                            user_val = user_match.group(1)
                            sentbyte = int(sentbyte_match.group(1))
                            sent_bytes_in_mb = sentbyte / (1024 * 1024)
                            extracted_data.append([date_val, time_val, user_val, sentbyte, sent_bytes_in_mb])
        
        df = pd.DataFrame(extracted_data, columns=['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB'])
        return df