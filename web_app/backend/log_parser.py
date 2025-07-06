import re
import pandas as pd
import ipaddress
import sys

def print_help():
    help_text = """
Forti-DFIR - Fortinet Log Parser CLI Tool Help
------------------------
Usage:
  Run the script without any arguments to access the interactive menu:
    python log_parser.py

  The interactive menu offers three options:
    1. Parse VPN logs
       - Extracts date, time, user, tunneltype, remip, reason, and msg from VPN logs
         for successful logins.
       - You will be prompted to enter the path to the VPN log file and the destination CSV file.
    
    2. Parse and aggregate firewall logs
       - Aggregates firewall logs by destination IP (excluding local IPs) and calculates size in MB.
       - You will be prompted to enter the path to the firewall log file and the destination CSV file.
    
    3. Parse VPN shutdown sessions and extract sent bytes for a given user
       - Filters VPN logs for sessions with "SSL tunnel shutdown" in the msg field and a specified user (case-insensitive).
       - Extracts date, time, user, sentbyte, and calculates sent_bytes_in_MB.
       - You will be prompted to enter the VPN log file path, target user, and destination CSV file.
    
  For help, run:
    python log_parser.py -help
"""
    print(help_text)

def parse_vpn_logs(file_path):
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

def is_public_ip(ip):
    """Returns True if the IP is public, False if it is private/local."""
    return not ipaddress.ip_address(ip).is_private

def parse_firewall_logs(file_path):
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
                if is_public_ip(dstip):
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

def parse_vpn_shutdown_sentbytes_csv(file_path, target_user):
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

def main():
    ascii_art = r"""
  _____                 _                      _   ____          _____ ____                       
 |  __ \               | |                    | | |  _ \        |_   _/ __ \                      
 | |  | | _____   _____| | ___  _ __   ___  __| | | |_) |_   _    | || |  | |_ __  ___  ___  ___  
 | |  | |/ _ \ \ / / _ \ |/ _ \| '_ \ / _ \/ _` | |  _ <| | | |   | || |  | | '_ \/ __|/ _ \/ __| 
 | |__| |  __/\ V /  __/ | (_) | |_) |  __/ (_| | | |_) | |_| |  _| || |__| | | | \__ \  __/ (__  
 |_____/ \___| \_/ \___|_|\___/| .__/ \___|\__,_| |____/ \__, | |_____\____/|_| |_|___/\___|\___| 
                               | | | |     | |            __/ |                                   
  _ __ ___  ___  ___  __ _ _ __|_|_| |__   | |_ ___  __ _|___/ ___                                
 | '__/ _ \/ __|/ _ \/ _` | '__/ __| '_ \  | __/ _ \/ _` | '_ ` _ \                               
 | | |  __/\__ \  __/ (_| | | | (__| | | | | ||  __/ (_| | | | | | |                              
 |_|  \___||___/\___|\__,_|_|  \___|_| |_|  \__\___|\__,_|_| |_| |_|                              
"""

    print(ascii_art)


    # Check for help flag in the command-line arguments.
    if len(sys.argv) > 1 and sys.argv[1] == "-help":
        print_help()
        sys.exit(0)
    
    print("Forti-DFIR - Fortinet Log Parser CLI Tool")
    print("1. Parse VPN logs")
    print("2. Parse and aggregate firewall logs")
    print("3. Parse VPN shutdown sessions and extract sent bytes for a given user")
    
    choice = input("Enter your choice (1, 2, or 3): ").strip()
    
    if choice not in ["1", "2", "3"]:
        print("Invalid choice! Please restart the tool.")
        return

    input_file = input("Enter the path to the log file: ").strip()
    output_file = input("Enter the path to save the parsed logs (including file name and extension): ").strip()

    if choice == "1":
        df = parse_vpn_logs(input_file)
    elif choice == "2":
        df = parse_firewall_logs(input_file)
    elif choice == "3":
        target_user = input("Enter the user name to filter by: ").strip()
        df = parse_vpn_shutdown_sentbytes_csv(input_file, target_user)
    
    df.to_csv(output_file, index=False)
    print(f"Data saved at {output_file}")

if __name__ == "__main__":
    main()
