from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
import asyncio
from contextlib import asynccontextmanager
from utils.process_monitor import (
    ProcessMonitorService, 
    NotificationService, 
    SystemInfoService, 
    SessionManager,
    DesktopClientService,
    load_config
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
monitor_service = None
notification_service = None
system_info_service = None
session_manager = None
desktop_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Roblox Parental Control Backend...")
    
    global monitor_service, notification_service, system_info_service, session_manager, desktop_service
    
    # Initialize services
    monitor_service = ProcessMonitorService()
    notification_service = NotificationService()
    system_info_service = SystemInfoService()
    session_manager = SessionManager()
    desktop_service = DesktopClientService()
    
    # Link services together
    monitor_service.set_session_manager(session_manager)
    monitor_service.set_desktop_service(desktop_service)
    session_manager.set_desktop_service(desktop_service)
    
    # Initialize WebSocket server for real-time communication
    await desktop_service.init_websocket_server()
    
    # Load configuration
    config = load_config()
    
    # Start monitoring service
    await monitor_service.start()
    
    logger.info("Backend services started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend services...")
    if monitor_service:
        await monitor_service.stop()
    logger.info("Backend shutdown complete")

app = FastAPI(
    title="Roblox Parental Control Backend",
    description="Backend service for monitoring and controlling Roblox sessions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Flutter client"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "monitor": monitor_service.is_running() if monitor_service else False,
            "notifications": True,
            "system_info": True
        }
    }

# Include all API routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    print("Starting Roblox Parental Control Backend on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
