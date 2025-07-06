# Forti-DFIR - IONSec Fortinet Log Parser Tool

## Overview
**IONSec Forti-DFIR Log Parser Tool** is a comprehensive solution for analyzing Fortinet VPN and firewall logs. Available as both a command-line utility and a modern web application, it extracts key data and exports it to CSV format, streamlining security investigations for incident responders.

Developed by the **IONSec Research Team**.

---

## Features
- 🔍 **VPN Login Parser**: Extracts successful VPN login details.
- 📊 **Firewall Log Aggregation**: Summarizes traffic by destination IP, filtering out private/local addresses.
- 📌 **VPN Session Shutdown Analyzer**: Extracts session termination statistics, including sent bytes, for a specific user.
- 💻 **Interactive CLI Interface**: Guides users through log selection and parsing options.
- 🌐 **Web Application**: Modern web interface with authentication, file upload, and real-time processing.
- 📂 **CSV Export**: Saves parsed data for easy analysis.
- 🐳 **Docker Support**: Easy deployment with Docker Compose.
- ☁️ **Cloud Ready**: Automatic deployment to Netlify and Vercel.
- ❓ **Help Function (`-help`)**: Displays usage instructions.

---

## Quick Start

### Option 1: Web Application (Recommended)
```bash
cd web_app
./run.sh  # For macOS/Linux
# OR
run.bat   # For Windows
```
Access the application at http://localhost:3000

### Option 2: Command Line Interface
```bash
python log_parser.py
```

---

## Installation

### Prerequisites for CLI
- Python **3.6+**
- `pandas` library

### Prerequisites for Web App
- Python **3.6+** OR Docker
- Node.js **14+** (if not using Docker)

### Installation Steps

1. Clone the repository:
   ```sh
   git clone https://github.com/ionsec/Forti-DFIR.git
   cd Forti-DFIR
   ```

2. **For CLI usage:**
   ```sh
   pip install pandas
   ```

3. **For Web App usage:**
   - **Option A - Using Docker (Recommended):**
     ```sh
     cd web_app
     docker-compose up
     ```
   
   - **Option B - Manual Installation:**
     ```sh
     cd web_app
     ./run.sh  # Automated setup for macOS/Linux
     # OR
     run.bat   # Automated setup for Windows
     ```

---

## Web Application

The web application provides a modern interface for all parsing operations:

- **Access**: http://localhost:3000 (frontend) / http://localhost:5000 (API)
- **Default Login**: admin / admin123
- **Features**: All CLI functionality plus:
  - User authentication
  - Drag-and-drop file upload
  - Real-time processing status
  - Download results as CSV
  - Parse history tracking

For detailed web app documentation, see [web_app/README.md](web_app/README.md)

---

## CLI Usage
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

## Deployment

The web application can be deployed to cloud platforms:

### Deploy to Netlify
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/ionsec/Forti-DFIR)

### Deploy to Vercel
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ionsec/Forti-DFIR)

See [web_app/DEPLOYMENT.md](web_app/DEPLOYMENT.md) for detailed deployment instructions.

---

## Contributing
Contributions are welcome! Feel free to submit issues or pull requests.
