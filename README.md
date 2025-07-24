# Poller Project

## Overview
The Poller project is a FastAPI application designed to monitor Roblox processes on a system. It provides an API to check the status of these processes and sends alerts when processes start or terminate.

## Project Structure
```
poller
├── src
│   ├── main.py            # Entry point of the application
│   ├── api
│   │   └── routes.py      # API routes for the FastAPI application
│   └── utils
│       └── process_monitor.py  # Logic for monitoring Roblox processes
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## Installation
To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd poller
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the FastAPI application, execute the following command:
```
uvicorn src.main:app --reload
```

You can then access the API at `http://127.0.0.1:8000`.

## API Endpoints
- **GET /processes**: Retrieve the current status of Roblox processes.
- **POST /alert**: Send an alert when a process starts or terminates.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.