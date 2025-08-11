import asyncio
import websockets
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket server for real-time communication with desktop client"""
    
    def __init__(self, host='localhost', port=8001):
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.is_running = False
        
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.handle_client, 
                self.host, 
                self.port
            )
            self.is_running = True
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            logger.info("WebSocket server stopped")
    
    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection"""
        self.connected_clients.add(websocket)
        logger.info(f"Desktop client connected via WebSocket: {websocket.remote_address}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Roblox Monitor WebSocket",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Desktop client WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def handle_message(self, websocket, data: Dict[str, Any]):
        """Handle incoming message from desktop client"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await websocket.send(json.dumps({
                "type": "pong", 
                "timestamp": datetime.now().isoformat()
            }))
        elif message_type == "desktop_ready":
            logger.info("Desktop client is ready to receive events")
        elif message_type == "command":
            # Handle commands from desktop client
            await self.handle_desktop_command(data.get("payload", {}))
    
    async def handle_desktop_command(self, payload: Dict[str, Any]):
        """Handle commands sent from desktop client"""
        command = payload.get("command")
        logger.info(f"Received command from desktop client: {command}")
        # Commands will be processed by main application
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected desktop clients"""
        if not self.connected_clients:
            logger.warning(f"No desktop clients connected to receive event: {event_type}")
            return
        
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients
        disconnected = set()
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.connected_clients.discard(client)
        
        logger.info(f"Broadcasted {event_type} to {len(self.connected_clients)} clients")
    
    async def send_to_desktop(self, message_type: str, data: Dict[str, Any]):
        """Send specific message to desktop clients"""
        await self.broadcast_event(message_type, data)
    
    def has_connected_clients(self) -> bool:
        """Check if any desktop clients are connected"""
        return len(self.connected_clients) > 0
