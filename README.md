# Forti-DFIR - IONSec Fortinet Log Parser Tool

## Overview
**IONSec Forti-DFIR Log Parser Tool** is a command-line utility designed for analyzing VPN and firewall logs. It extracts key data and exports it to CSV format, streamlining security investigations for incident responders.

Developed by the **IONSec Research Team**.

---

## Features
- 🔍 **VPN Login Parser**: Extracts successful VPN login details.
- 📊 **Firewall Log Aggregation**: Summarizes traffic by destination IP, filtering out private/local addresses.
- 📌 **VPN Session Shutdown Analyzer**: Extracts session termination statistics, including sent bytes, for a specific user.
- 💻 **Interactive CLI Interface**: Guides users through log selection and parsing options.
- 📂 **CSV Export**: Saves parsed data for easy analysis.
- ❓ **Help Function (`-help`)**: Displays usage instructions.

---

## Installation
### Prerequisites
- Python **3.6+**
- `pandas` library

### Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/ionsec/Forti-DFIR.git
   cd Forti-DFIR
   ```
2. Install dependencies:
   ```sh
   pip install pandas
   ```

---

## Usage
Run the script in interactive mode:
```sh
python log_parser.py
```

### CLI Options
When executed, the tool presents the following menu:
```
Log Parser CLI Tool
1. Parse VPN logs
2. Parse and aggregate firewall logs
3. Parse VPN shutdown sessions and extract sent bytes for a given user
```

#### Option 1: VPN Login Parsing
✔ Extracts VPN login details (date, time, user, IP, reason, etc.).

#### Option 2: Firewall Log Aggregation
✔ Aggregates firewall logs by destination IP and calculates total sent bytes.

#### Option 3: VPN Session Shutdown Analysis
✔ Extracts session termination logs for a specified user, including sent bytes.

#### User Input Prompts
You will be asked to provide:
- 📌 The **path** to the input log file.
- 📌 The **path** to save the output CSV file.
- 📌 (For Option 3) The **username** to filter logs (case-insensitive).

---

## Help Function
To display usage instructions, run:
```sh
python log_parser.py -help
```

---

## Example Usage
### Parsing VPN Logs
```sh
python log_parser.py
```
- Choose **Option 1**
- Enter file paths:
  ```
  Enter the path to the log file: vpn_logs.txt
  Enter the path to save the parsed logs: parsed_vpn_logs.csv
  ```

### Parsing Firewall Logs
```sh
python log_parser.py
```
- Choose **Option 2**
- Enter file paths:
  ```
  Enter the path to the log file: firewall_logs.txt
  Enter the path to save the parsed logs: parsed_firewall_logs.csv
  ```

### Extracting VPN Shutdown Sessions
```sh
python log_parser.py
```
- Choose **Option 3**
- Enter details:
  ```
  Enter the path to the log file: vpn_logs.txt
  Enter the user name to filter by: USER1
  Enter the path to save the parsed logs: shutdown_sessions.csv
  ```

---

## Output Format
The tool generates a structured CSV file with parsed log data.

### Example: VPN Shutdown Sessions Output
| Date       | Time     | User        | Sent Bytes | Sent Bytes (MB) |
|------------|---------|-------------|------------|-----------------|
| 2020-02-14 | 05:59:52 | USER1 | 600590000  | 600.59          |
| 2020-02-15 | 07:30:10 | USER1 | 100370000  | 100.37          |

---

## Contributing
Contributions are welcome! Feel free to submit issues or pull requests.

---

## License
This project is licensed under the **MIT License**.
