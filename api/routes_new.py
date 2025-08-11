from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
import asyncio

# Import our services (we'll need to update imports when we replace files)
from utils.process_monitor_new import (
    ProcessMonitorService, 
    SessionManager, 
    NotificationService, 
    SystemInfoService,
    FirebaseService,
    load_config, 
    save_config
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instances (will be injected from main app)
monitor_service: Optional[ProcessMonitorService] = None
session_manager: Optional[SessionManager] = None  
notification_service: Optional[NotificationService] = None
system_info_service: Optional[SystemInfoService] = None
firebase_service: Optional[FirebaseService] = None

# Initialize services on module load
def init_services():
    global monitor_service, session_manager, notification_service, system_info_service, firebase_service
    monitor_service = ProcessMonitorService()
    session_manager = SessionManager()
    notification_service = NotificationService()
    system_info_service = SystemInfoService()
    firebase_service = FirebaseService()
    
    # Link services
    monitor_service.set_session_manager(session_manager)

# Pydantic models for request validation
class MonitorStartRequest(BaseModel):
    child_profile: str
    timestamp: Optional[str] = None

class MonitorStopRequest(BaseModel):
    child_profile: str
    timestamp: Optional[str] = None

class ForceCloseRequest(BaseModel):
    child_profile: str
    reason: Optional[str] = "Parent control - session ended"

class NotificationRequest(BaseModel):
    title: str
    message: str
    timestamp: Optional[str] = None

class TimeLimitRequest(BaseModel):
    child_profile: str
    limit_minutes: int
    enforce_immediately: Optional[bool] = True

class SyncFirebaseRequest(BaseModel):
    session_data: Dict[str, Any]

# Health and Status Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/roblox/status")
async def get_roblox_status():
    """Get current Roblox process status"""
    if not monitor_service:
        init_services()
    
    try:
        status = monitor_service.get_roblox_status()
        return status
    except Exception as e:
        logger.error(f"Error getting Roblox status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/roblox/process")
async def get_roblox_process_info():
    """Get detailed Roblox process information"""
    if not monitor_service:
        init_services()
    
    try:
        info = monitor_service.get_process_info()
        return info
    except Exception as e:
        logger.error(f"Error getting process info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring Control Endpoints
@router.post("/monitor/start")
async def start_monitoring(request: MonitorStartRequest):
    """Start monitoring a child's Roblox activity"""
    if not monitor_service or not session_manager:
        init_services()
    
    try:
        # Start monitoring service if not already running
        if not monitor_service.is_running():
            await monitor_service.start()
        
        # Start session for the child
        session = await session_manager.start_session(request.child_profile)
        
        logger.info(f"Started monitoring for child profile: {request.child_profile}")
        
        return {
            "status": "success",
            "message": f"Monitoring started for {request.child_profile}",
            "session_id": session.session_id,
            "child_profile": request.child_profile,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitor/stop") 
async def stop_monitoring(request: MonitorStopRequest):
    """Stop monitoring a child's Roblox activity"""
    if not session_manager:
        init_services()
    
    try:
        # End session for the child
        session = await session_manager.end_session(request.child_profile)
        
        if session:
            # Sync to Firebase if available
            if firebase_service and firebase_service.firebase_initialized:
                await firebase_service.sync_session(session.to_dict())
        
        logger.info(f"Stopped monitoring for child profile: {request.child_profile}")
        
        return {
            "status": "success", 
            "message": f"Monitoring stopped for {request.child_profile}",
            "session_data": session.to_dict() if session else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Roblox Control Endpoints
@router.post("/roblox/close")
async def force_close_roblox(request: ForceCloseRequest):
    """Force close Roblox application"""
    if not monitor_service:
        init_services()
    
    try:
        success = await monitor_service.force_close_roblox(request.reason)
        
        if success:
            # Also end any active sessions
            if session_manager:
                await session_manager.end_session(request.child_profile)
            
            # Send notification
            if notification_service:
                await notification_service.send_desktop_notification(
                    "Roblox Closed",
                    f"Roblox has been closed for {request.child_profile}: {request.reason}"
                )
        
        return {
            "status": "success" if success else "error",
            "message": "Roblox closed successfully" if success else "Failed to close Roblox",
            "child_profile": request.child_profile,
            "reason": request.reason,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error closing Roblox: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints  
@router.get("/session/live/{child_profile}")
async def get_live_session(child_profile: str):
    """Get live session data for a child profile"""
    if not session_manager:
        init_services()
    
    try:
        session_data = session_manager.get_live_session(child_profile)
        
        if session_data:
            return session_data
        else:
            return {
                "session_id": None,
                "child_profile": child_profile,
                "is_active": False,
                "message": "No active session found"
            }
            
    except Exception as e:
        logger.error(f"Error getting live session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Firebase Sync Endpoints
@router.post("/sync/firebase")
async def sync_session_with_firebase(request: SyncFirebaseRequest):
    """Sync session data with Firebase"""
    if not firebase_service:
        init_services()
    
    try:
        if firebase_service.firebase_initialized:
            success = await firebase_service.sync_session(request.session_data)
            
            return {
                "status": "success" if success else "error",
                "message": "Session synced successfully" if success else "Failed to sync session",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Firebase not initialized",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error syncing with Firebase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System Information Endpoints
@router.get("/system/info")
async def get_system_info():
    """Get system information"""
    if not system_info_service:
        init_services()
    
    try:
        info = system_info_service.get_system_info()
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Time Limits and Parental Controls
@router.post("/limits/set")
async def set_system_time_limit(request: TimeLimitRequest):
    """Configure time limits on the system level"""
    if not session_manager:
        init_services()
    
    try:
        # Set time limit
        session_manager.set_time_limit(request.child_profile, request.limit_minutes)
        
        # Check if we need to enforce immediately
        if request.enforce_immediately:
            exceeded_profiles = session_manager.check_time_limits()
            if request.child_profile in exceeded_profiles:
                # Force close Roblox
                if monitor_service:
                    await monitor_service.force_close_roblox("Time limit exceeded")
                
                # Send notification
                if notification_service:
                    await notification_service.send_desktop_notification(
                        "Time Limit Reached",
                        f"Time limit of {request.limit_minutes} minutes reached for {request.child_profile}"
                    )
        
        return {
            "status": "success",
            "message": f"Time limit set to {request.limit_minutes} minutes for {request.child_profile}",
            "child_profile": request.child_profile,
            "limit_minutes": request.limit_minutes,
            "enforced_immediately": request.enforce_immediately,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error setting time limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Notification Endpoints
@router.post("/notification/send")
async def send_desktop_notification(request: NotificationRequest):
    """Send notification to desktop system"""
    if not notification_service:
        init_services()
    
    try:
        success = await notification_service.send_desktop_notification(
            request.title, 
            request.message
        )
        
        return {
            "status": "success" if success else "error",
            "message": "Notification sent successfully" if success else "Failed to send notification",
            "title": request.title,
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoints for backward compatibility
@router.post("/load_config")
async def load_config_endpoint(request: Request):
    """Load config as JSON data from POST request body"""
    try:
        data = await request.json()
        save_config(data)
        
        return {
            "status": "success",
            "message": "Config loaded successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processes")
def get_current_processes():
    """Get the current Roblox processes"""
    if not monitor_service:
        init_services()
    
    try:
        status = monitor_service.get_roblox_status()
        return {"processes": status.get("processes", [])}
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitor")
async def start_monitoring_legacy(background_tasks: BackgroundTasks):
    """Legacy endpoint to start monitoring"""
    if not monitor_service:
        init_services()
    
    try:
        if not monitor_service.is_running():
            await monitor_service.start()
            
        return {
            "status": "success",
            "message": "Monitoring started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kill_roblox")
async def kill_roblox_legacy():
    """Legacy endpoint to kill Roblox processes"""
    if not monitor_service:
        init_services()
    
    try:
        await monitor_service.force_close_roblox("Manual termination")
        return {
            "status": "success", 
            "message": "Roblox processes terminated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error killing Roblox: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize services when module loads
init_services()
