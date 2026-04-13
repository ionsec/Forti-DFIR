#!/usr/bin/env python3
"""
Forti-DFIR - Fortinet Log Parser CLI Tool

A comprehensive solution for analyzing Fortinet VPN and firewall logs.
Developed by the IONSec Research Team.

Usage:
    python log_parser.py              # Interactive mode
    python log_parser.py -help       # Show help
"""

import re
import sys
import os
from pathlib import Path
from typing import Optional, List, Tuple
import argparse

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas")
    sys.exit(1)

import ipaddress


__version__ = "1.0.0"
__author__ = "IONSec Research Team"


def print_banner() -> None:
    """Print ASCII art banner."""
    banner = r"""
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

    Forti-DFIR v{} - Fortinet Log Parser for DFIR Investigations
    Developed by IONSec Research Team
    """.format(__version__)
    print(banner)


def print_help() -> None:
    """Print help information."""
    help_text = """
Forti-DFIR - Fortinet Log Parser CLI Tool v{}
============================================

Usage:
    python log_parser.py              # Interactive mode
    python log_parser.py -help        # Show this help message

Options:
    1. Parse VPN logs
       - Extracts successful VPN login details
       - Fields: date, time, user, tunneltype, remip, reason, msg
       
    2. Parse and aggregate firewall logs
       - Aggregates traffic by destination IP
       - Filters out private/local IP addresses
       - Calculates total bytes and size in MB
       
    3. Parse VPN shutdown sessions
       - Extracts session termination logs
       - Filters by username (case-insensitive)
       - Calculates sent bytes and size in MB

Input/Output:
    - Input files: .txt, .log, or .csv format
    - Output: CSV file with parsed data

Examples:
    # Parse VPN logs
    python log_parser.py
    > Enter your choice: 1
    > Enter the path to the log file: vpn_logs.txt
    > Enter the path to save the parsed logs: output/vpn_parsed.csv

Tips:
    - Use forward slashes or escaped backslashes in file paths
    - Output directories are created automatically if they don't exist
    - Large files may take longer to process

For more information, visit: https://github.com/ionsec/Forti-DFIR
    """.format(__version__)
    print(help_text)


def validate_file_path(file_path: str, must_exist: bool = True) -> Path:
    """
    Validate and normalize a file path.
    
    Args:
        file_path: Path to validate
        must_exist: Whether the file must exist
        
    Returns:
        Normalized Path object
        
    Raises:
        FileNotFoundError: If file doesn't exist and must_exist is True
        ValueError: If path is invalid
    """
    path = Path(file_path.strip())
    
    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if must_exist and not path.is_file():
        raise ValueError(f"Not a file: {file_path}")
    
    return path


def ensure_output_path(output_path: str) -> Path:
    """
    Ensure output directory exists and return validated path.
    
    Args:
        output_path: Path for output file
        
    Returns:
        Validated Path object
    """
    path = Path(output_path.strip())
    
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    return path


def parse_vpn_logs(file_path: Path) -> pd.DataFrame:
    """
    Parse VPN logs and extract successful login details.
    
    Args:
        file_path: Path to the VPN log file
        
    Returns:
        DataFrame with columns: date, time, user, tunneltype, remip, reason, msg
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If file format is invalid
    """
    print(f"\n📄 Parsing VPN logs from: {file_path}")
    
    # Regex patterns for Fortinet log format
    patterns = {
        'date': re.compile(r'date=(\S+)'),
        'time': re.compile(r'time=(\S+)'),
        'user': re.compile(r'user="([^"]+)"'),
        'tunneltype': re.compile(r'tunneltype="([^"]+)"'),
        'remip': re.compile(r'remip=([\d\.]+)'),
        'reason': re.compile(r'reason="([^"]+)"'),
        'msg': re.compile(r'msg="([^"]+)"')
    }
    
    extracted_data: List[List[str]] = []
    lines_processed = 0
    lines_matched = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                lines_processed += 1
                
                # Extract all fields
                matches = {key: pattern.search(line) for key, pattern in patterns.items()}
                
                # Check if all required fields exist
                if all(matches.values()):
                    reason = matches['reason'].group(1)
                    
                    # Only keep successful logins
                    if reason.lower() == "login successfully":
                        extracted_data.append([
                            matches['date'].group(1),
                            matches['time'].group(1),
                            matches['user'].group(1),
                            matches['tunneltype'].group(1),
                            matches['remip'].group(1),
                            reason,
                            matches['msg'].group(1)
                        ])
                        lines_matched += 1
                        
                        # Progress indicator for large files
                        if lines_processed % 10000 == 0:
                            print(f"   Processed {lines_processed:,} lines...", end='\r')
    
    except UnicodeDecodeError:
        print("   ⚠️  Warning: Some characters couldn't be decoded")
        # Continue with what we have
    
    print(f"   ✅ Processed {lines_processed:,} lines, found {lines_matched:,} successful logins")
    
    df = pd.DataFrame(
        extracted_data, 
        columns=['date', 'time', 'user', 'tunneltype', 'remip', 'reason', 'msg']
    )
    
    return df


def is_public_ip(ip: str) -> bool:
    """
    Check if an IP address is public (not private/local).
    
    Args:
        ip: IP address string
        
    Returns:
        True if IP is public, False otherwise
    """
    try:
        return not ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def parse_firewall_logs(file_path: Path) -> pd.DataFrame:
    """
    Parse firewall logs and aggregate traffic by destination IP.
    
    Args:
        file_path: Path to the firewall log file
        
    Returns:
        DataFrame with columns: dstip, total_sentbyte, size_mb
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If file format is invalid
    """
    print(f"\n📄 Parsing firewall logs from: {file_path}")
    
    # Regex patterns
    dstip_pattern = re.compile(r'dstip=([\d\.]+)')
    sentbyte_pattern = re.compile(r'sentbyte=(\d+)')
    
    data: dict = {}
    lines_processed = 0
    lines_matched = 0
    private_ips_skipped = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                lines_processed += 1
                
                dstip_match = dstip_pattern.search(line)
                sentbyte_match = sentbyte_pattern.search(line)
                
                if dstip_match and sentbyte_match:
                    dstip = dstip_match.group(1)
                    
                    # Validate IP format
                    if not dstip.replace('.', '').isdigit():
                        continue
                    
                    # Skip private IPs
                    if is_public_ip(dstip):
                        sentbyte = int(sentbyte_match.group(1))
                        data[dstip] = data.get(dstip, 0) + sentbyte
                        lines_matched += 1
                    else:
                        private_ips_skipped += 1
                
                # Progress indicator
                if lines_processed % 10000 == 0:
                    print(f"   Processed {lines_processed:,} lines...", end='\r')
    
    except UnicodeDecodeError:
        print("   ⚠️  Warning: Some characters couldn't be decoded")
    
    print(f"   ✅ Processed {lines_processed:,} lines")
    print(f"   📊 Found {lines_matched:,} public IP entries")
    print(f"   🔒 Skipped {private_ips_skipped:,} private IP entries")
    
    df = pd.DataFrame(list(data.items()), columns=['dstip', 'total_sentbyte'])
    df['size_mb'] = df['total_sentbyte'] / (1024 * 1024)
    df = df.sort_values(by='total_sentbyte', ascending=False)
    
    return df


def parse_vpn_shutdown_sentbytes(file_path: Path, target_user: str) -> pd.DataFrame:
    """
    Parse VPN shutdown sessions for a specific user.
    
    Args:
        file_path: Path to the VPN log file
        target_user: Username to filter (case-insensitive)
        
    Returns:
        DataFrame with columns: date, time, user, sentbyte, sent_bytes_in_MB
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If file format is invalid
    """
    print(f"\n📄 Parsing VPN shutdown sessions from: {file_path}")
    print(f"   Filtering for user: {target_user}")
    
    # Regex patterns
    patterns = {
        'date': re.compile(r'date=(\S+)'),
        'time': re.compile(r'time=(\S+)'),
        'user': re.compile(r'user="([^"]+)"', flags=re.IGNORECASE),
        'sentbyte': re.compile(r'sentbyte=(\d+)'),
        'msg': re.compile(r'msg="([^"]+)"')
    }
    
    extracted_data: List[List[str]] = []
    lines_processed = 0
    lines_matched = 0
    target_user_lower = target_user.lower().strip()
    
    if not target_user_lower:
        raise ValueError("Username cannot be empty")
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                lines_processed += 1
                
                msg_match = patterns['msg'].search(line)
                
                # Only process shutdown messages
                if msg_match and msg_match.group(1) == "SSL tunnel shutdown":
                    user_match = patterns['user'].search(line)
                    
                    # Filter by user
                    if user_match and user_match.group(1).lower() == target_user_lower:
                        date_match = patterns['date'].search(line)
                        time_match = patterns['time'].search(line)
                        sentbyte_match = patterns['sentbyte'].search(line)
                        
                        if all([date_match, time_match, sentbyte_match]):
                            sentbyte = int(sentbyte_match.group(1))
                            extracted_data.append([
                                date_match.group(1),
                                time_match.group(1),
                                user_match.group(1),
                                sentbyte,
                                sentbyte / (1024 * 1024)
                            ])
                            lines_matched += 1
                
                # Progress indicator
                if lines_processed % 10000 == 0:
                    print(f"   Processed {lines_processed:,} lines...", end='\r')
    
    except UnicodeDecodeError:
        print("   ⚠️  Warning: Some characters couldn't be decoded")
    
    print(f"   ✅ Processed {lines_processed:,} lines")
    print(f"   📊 Found {lines_matched:,} shutdown sessions for user '{target_user}'")
    
    df = pd.DataFrame(
        extracted_data, 
        columns=['date', 'time', 'user', 'sentbyte', 'sent_bytes_in_MB']
    )
    
    return df


def save_results(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path to output file
    """
    df.to_csv(output_path, index=False)
    print(f"\n💾 Results saved to: {output_path}")
    print(f"   📁 File size: {output_path.stat().st_size:,} bytes")
    print(f"   📊 Records: {len(df):,}")


def interactive_mode() -> None:
    """Run the CLI in interactive mode."""
    print_banner()
    print("Forti-DFIR - Fortinet Log Parser CLI Tool")
    print("=" * 50)
    
    while True:
        print("\nSelect an option:")
        print("  1. Parse VPN logs")
        print("  2. Parse and aggregate firewall logs")
        print("  3. Parse VPN shutdown sessions for a user")
        print("  4. Exit")
        print()
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == '4':
            print("\n👋 Thank you for using Forti-DFIR!")
            break
        
        if choice not in ['1', '2', '3']:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
            continue
        
        # Get input file
        input_path = input("Enter the path to the log file: ").strip()
        
        try:
            input_file = validate_file_path(input_path, must_exist=True)
        except FileNotFoundError:
            print(f"❌ Error: File not found: {input_path}")
            continue
        except ValueError as e:
            print(f"❌ Error: {e}")
            continue
        
        # Get username filter for option 3
        target_user = None
        if choice == '3':
            target_user = input("Enter the username to filter by: ").strip()
            if not target_user:
                print("❌ Error: Username cannot be empty.")
                continue
        
        # Get output file
        output_path = input("Enter the path to save the parsed logs: ").strip()
        
        try:
            output_file = ensure_output_path(output_path)
        except Exception as e:
            print(f"❌ Error creating output path: {e}")
            continue
        
        # Parse based on choice
        try:
            if choice == '1':
                df = parse_vpn_logs(input_file)
            elif choice == '2':
                df = parse_firewall_logs(input_file)
            elif choice == '3':
                df = parse_vpn_shutdown_sentbytes(input_file, target_user)
            
            if df.empty:
                print("\n⚠️  Warning: No matching records found.")
                print("   The file may be empty or contain no matching entries.")
                continue
            
            # Save results
            save_results(df, output_file)
            
            # Show preview
            print("\n📋 Preview (first 5 records):")
            print(df.head().to_string(index=False))
            
        except Exception as e:
            print(f"\n❌ Error processing file: {e}")
            continue


def main() -> None:
    """Main entry point."""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-help', '--help', '-h', '--h']:
        print_banner()
        print_help()
        sys.exit(0)
    
    # Check for version flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-v', '--version']:
        print(f"Forti-DFIR v{__version__}")
        sys.exit(0)
    
    # Run in interactive mode
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
