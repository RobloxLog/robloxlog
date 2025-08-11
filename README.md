# Roblox Parental Control Backend

## Overview
This is the Python backend component of a comprehensive Roblox parental control system. It monitors Roblox processes, manages gaming sessions, and provides APIs for a Flutter desktop client that handles Firebase integration and mobile app communication.

## Architecture
The system follows a secure three-tier architecture:
- **Python Backend** (this project): Monitors Roblox processes and local system control
- **Flutter Desktop Client**: Handles Firebase authentication, data sync, and acts as intermediary
- **Mobile App**: Remote monitoring and control via Firebase

This design keeps Firebase credentials secure in the desktop client rather than stored locally with the Python service.

## Project Structure
```
poller/
├── main.py                  # FastAPI application entry point with service initialization
├── api/
│   └── routes.py            # Comprehensive API routes matching Flutter client expectations
├── utils/
│   └── process_monitor.py   # Core monitoring services and desktop client communication
├── record.py                # Session recording and profile management
├── config.json              # Configuration with security-focused defaults
├── requirements.txt         # Python dependencies
└── README.md                # This documentation
```

## Installation
1. Ensure you have Python 3.8+ installed
2. Clone this repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
The `config.json` file contains all system settings:
- **Security**: Firebase handled by desktop client (no credentials stored locally)
- **Monitoring**: Process detection intervals and behavior
- **Parental Controls**: Time limits, auto-close behavior, notifications
- **Desktop Client**: Communication settings and queuing

## API Endpoints

### Core Monitoring
- `GET /health` - Health check for Flutter client
- `GET /roblox/status` - Current Roblox process status
- `GET /roblox/process` - Detailed process information
- `POST /roblox/close` - Force close Roblox processes

### Session Management
- `POST /monitor/start` - Start monitoring for child profile
- `POST /monitor/stop` - Stop monitoring for child profile
- `GET /session/live/{child_profile}` - Get live session data

### Desktop Client Communication
- `POST /desktop/connect` - Desktop client connection notification
- `POST /desktop/disconnect` - Desktop client disconnection
- `GET /desktop/status` - Connection status and queued items
- `GET /desktop/queue/sessions` - Retrieve queued session data
- `GET /desktop/queue/notifications` - Retrieve queued notifications
- `POST /desktop/command` - Receive commands from mobile app via desktop client

### System & Controls
- `GET /system/info` - System information
- `POST /limits/set` - Set time limits for child profiles
- `POST /notification/send` - Send desktop notifications
- `POST /sync/firebase` - Request Firebase sync via desktop client

## Security Features
- **No Local Firebase Credentials**: All Firebase operations handled by desktop client
- **Process Isolation**: Python backend only handles local system operations
- **Command Queuing**: Commands queued when desktop client disconnected
- **Secure Communication**: All mobile commands routed through authenticated desktop client

1. Clone the repository:
   ```
   git clone <repository-url>
   cd poller
   ```

2. (Optional) Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On macOS/Linux
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the FastAPI application, execute:
```
python main.py
OR
uvicorn main:app --reload --port 8100
```

The API will be available at `http://127.0.0.1:8100`.

## API Endpoints
- **GET /processes**: Retrieve the current status of Roblox processes.
- **POST /monitor**: Start the background process monitor.
- **GET /kill_roblox**: Kill all running Roblox processes.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for improvements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.