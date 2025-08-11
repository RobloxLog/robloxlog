# Python ↔ Desktop Client Communication Solutions

## Problem
The Python backend needs to actively notify the Flutter desktop client when Roblox events happen (start/stop), but the original design only supported one-way communication (desktop → Python).

## Solutions Implemented

### 1. **WebSocket Server (Real-time, Preferred)**
- **Python**: Runs WebSocket server on `ws://localhost:8001`
- **Desktop Client**: Connects to WebSocket for real-time bidirectional communication
- **Benefits**: Instant notifications, low latency, persistent connection
- **Usage**: Primary method when both services are running

```python
# Python sends events immediately:
await desktop_service.send_roblox_event("roblox_started", process_info)
await desktop_service.send_session_event("session_ended", session_data)
```

```dart
// Flutter receives events in real-time:
_wsChannel.stream.listen((data) => _handlePythonEvent(json.decode(data)));
```

### 2. **HTTP Polling (Fallback)**
- **Desktop Client**: Polls `/desktop/events/poll` every 2 seconds
- **Python**: Queues events when WebSocket unavailable
- **Benefits**: Reliable fallback, works through firewalls
- **Usage**: Automatic fallback when WebSocket fails

```dart
// Flutter polls for events:
Timer.periodic(Duration(seconds: 2), (_) => _pollForEvents());
```

### 3. **Event Queue System**
- **Smart Queuing**: Events queued when desktop client offline
- **Auto-Processing**: Queue processed when client reconnects
- **Persistence**: No events lost during disconnections

## Event Types Sent to Desktop Client

### Roblox Process Events
```json
{
  "type": "roblox_event",
  "event_type": "roblox_started|roblox_stopped|roblox_auto_closed",
  "data": {
    "process_info": {
      "pid": 1234,
      "name": "RobloxPlayerBeta.exe",
      "started_at": "2025-08-11T10:30:00Z"
    }
  }
}
```

### Session Events
```json
{
  "type": "session_event", 
  "event_type": "session_started|session_ended|time_limit_warning",
  "data": {
    "session_data": {
      "session_id": "default_child_1691746200000",
      "child_profile": "default_child",
      "duration_minutes": 45,
      "is_active": false
    }
  }
}
```

### Notifications
```json
{
  "type": "notification",
  "data": {
    "title": "Time Limit Exceeded",
    "message": "Child has exceeded 2 hour limit",
    "type": "time_limit_exceeded"
  }
}
```

### Firebase Sync Requests
```json
{
  "type": "firebase_sync_request",
  "data": {
    "data_type": "session",
    "data": { /* session data to sync */ }
  }
}
```

## API Endpoints Added

### Connection Management
- `POST /desktop/connect` - Establish connection, get WebSocket info
- `POST /desktop/disconnect` - Clean disconnection
- `GET /desktop/status` - Check connection status and queue sizes

### Event Communication  
- `GET /desktop/events/poll` - HTTP polling for events (fallback)
- `GET /desktop/queue/sessions` - Get queued session data
- `GET /desktop/queue/notifications` - Get queued notifications

### Command Processing
- `POST /desktop/command` - Receive commands from mobile (via desktop)
- `POST /sync/confirm` - Confirm Firebase sync completion

## Flow Example

1. **Roblox Starts** → Python detects process
2. **Python** → WebSocket/Queue: `roblox_started` event  
3. **Desktop Client** → Receives event instantly
4. **Desktop Client** → Updates UI, syncs to Firebase
5. **Mobile App** → Gets Firebase update, shows notification
6. **Mobile App** → Sends "force_close" command via Firebase  
7. **Desktop Client** → Receives Firebase command
8. **Desktop Client** → HTTP POST to `/desktop/command`
9. **Python** → Executes command, kills Roblox
10. **Python** → WebSocket/Queue: `roblox_stopped` event
11. **Desktop Client** → Syncs result to Firebase
12. **Mobile App** → Gets confirmation

## Security Benefits

- **No Firebase credentials** in Python backend
- **Desktop client authenticates** all mobile commands
- **Command validation** before execution
- **Encrypted communication** path through Firebase
- **Local system isolation** - Python only does local operations

## Configuration

```json
{
  "desktop_client": {
    "websocket": {
      "enabled": true,
      "host": "localhost", 
      "port": 8001
    },
    "http_polling": {
      "enabled": true,
      "interval": 2
    }
  }
}
```

This solves the bidirectional communication problem while maintaining security!
