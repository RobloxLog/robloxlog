# Poller Project

## Overview
Poller is a FastAPI application designed to monitor Roblox processes on your system. It provides an API to check the status of these processes, start/stop monitoring, and send alerts when processes start or terminate.

## Project Structure
```
poller/
├── main.py                  # Entry point of the FastAPI application
├── api/
│   └── routes.py            # API routes for the FastAPI application
├── utils/
│   └── process_monitor.py   # Logic for monitoring Roblox processes
├── requirements.txt         # Project dependencies
├── config.json              # Configuration file
└── README.md                # Project documentation
```

## Installation
To set up the project, follow these steps:

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