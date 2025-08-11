import psutil
import time
import asyncio
import json
import uuid
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import subprocess
import sys
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROBLOX_PROCESSES = [
    "RobloxPlayerBeta.exe",
    "RobloxStudioBeta.exe", 
    "RobloxPlayerLauncher.exe",
    "Roblox"
]

class SessionRecord:
    """Session record class matching Flutter model"""
    def __init__(self, child_profile: str = None):
        self.session_id = None
        self.child_profile = child_profile
        self.time_start = None
        self.time_end = None
        self.duration_seconds = 0
        self.metadata = {}
        self.is_active = False
    
    def start(self):
        """Start a new session"""
        self.time_start = datetime.now(timezone.utc)
        self.session_id = f"{self.child_profile}_{int(self.time_start.timestamp() * 1000)}"
        self.is_active = True
        logger.info(f"Session started: {self.session_id}")
    
    def end(self):
        """End the current session"""
        if self.is_active:
            self.time_end = datetime.now(timezone.utc)
            if self.time_start:
                self.duration_seconds = (self.time_end - self.time_start).total_seconds()
            self.is_active = False
            logger.info(f"Session ended: {self.session_id}, duration: {self.duration_seconds}s")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "session_id": self.session_id,
            "child_profile": self.child_profile,
            "time_start": self.time_start.isoformat() if self.time_start else None,
            "time_end": self.time_end.isoformat() if self.time_end else None,
            "duration_seconds": self.duration_seconds,
            "duration_minutes": int(self.duration_seconds / 60),
            "is_active": self.is_active,
            "metadata": self.metadata
        }

class ProcessMonitorService:
    """Main service for monitoring Roblox processes"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitor_task = None
        self.known_processes = set()
        self.session_manager = None
        self.config = {}
        
    def set_session_manager(self, session_manager):
        """Set the session manager reference"""
        self.session_manager = session_manager
        
    async def start(self):
        """Start the monitoring service"""
        if not self.is_monitoring:
            self.config = load_config()
            self.is_monitoring = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("Process monitoring started")
            
            # Handle existing processes
            await self._handle_existing_processes()
    
    async def stop(self):
        """Stop the monitoring service"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            logger.info("Process monitoring stopped")
    
    def is_running(self) -> bool:
        """Check if monitoring is active"""
        return self.is_monitoring and self.monitor_task and not self.monitor_task.done()
    
    async def _handle_existing_processes(self):
        """Handle Roblox processes that are already running"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if self._is_roblox_process(proc.info['name']):
                    self.known_processes.add((proc.info['pid'], proc.info['name']))
                    
                    if self.config.get("auto_close_roblox", False):
                        logger.info(f"Auto-closing existing Roblox process: {proc.info['name']} (PID: {proc.info['pid']})")
                        await self._kill_roblox_processes()
                        self.known_processes.clear()
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                current_processes = set()
                
                # Get current Roblox processes
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if self._is_roblox_process(proc.info['name']):
                            current_processes.add((proc.info['pid'], proc.info['name']))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Check for new processes
                new_processes = current_processes - self.known_processes
                for pid, name in new_processes:
                    await self._handle_process_started(pid, name)
                
                # Check for terminated processes
                terminated_processes = self.known_processes - current_processes
                for pid, name in terminated_processes:
                    await self._handle_process_terminated(pid, name)
                
                self.known_processes = current_processes
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _handle_process_started(self, pid: int, name: str):
        """Handle when a Roblox process starts"""
        logger.info(f"Roblox process started: {name} (PID: {pid})")
        
        # Check if auto-close is enabled
        if self.config.get("auto_close_roblox", False):
            logger.info(f"Auto-closing Roblox process: {name} (PID: {pid})")
            await self._kill_roblox_processes()
            return
        
        # Start a session if session manager is available
        if self.session_manager:
            await self.session_manager.start_session("default_child")
    
    async def _handle_process_terminated(self, pid: int, name: str):
        """Handle when a Roblox process terminates"""
        logger.info(f"Roblox process terminated: {name} (PID: {pid})")
        
        # End session if session manager is available
        if self.session_manager:
            await self.session_manager.end_session("default_child")
    
    def _is_roblox_process(self, process_name: str) -> bool:
        """Check if a process name is a Roblox process"""
        return (process_name in ROBLOX_PROCESSES or 
                'roblox' in process_name.lower())
    
    async def _kill_roblox_processes(self):
        """Kill all Roblox processes"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if self._is_roblox_process(proc.info['name']):
                    logger.info(f"Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"Could not kill process: {e}")
    
    def get_roblox_status(self) -> Dict[str, Any]:
        """Get current Roblox process status"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            try:
                if self._is_roblox_process(proc.info['name']):
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "started_at": datetime.fromtimestamp(proc.info['create_time']).isoformat(),
                        "memory_usage": proc.memory_info().rss if hasattr(proc, 'memory_info') else 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return {
            "is_running": len(processes) > 0,
            "process_count": len(processes),
            "processes": processes,
            "monitoring_active": self.is_running()
        }
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get detailed Roblox process information"""
        return self.get_roblox_status()
    
    async def force_close_roblox(self, reason: str = "Parent control"):
        """Force close all Roblox processes"""
        logger.info(f"Force closing Roblox - Reason: {reason}")
        await self._kill_roblox_processes()
        return True

class SessionManager:
    """Manages gaming sessions for different child profiles"""
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionRecord] = {}
        self.session_history: List[SessionRecord] = []
        self.time_limits: Dict[str, int] = {}  # minutes per child
        
    async def start_session(self, child_profile: str) -> SessionRecord:
        """Start a new session for a child"""
        if child_profile in self.active_sessions:
            # End existing session first
            await self.end_session(child_profile)
        
        session = SessionRecord(child_profile)
        session.start()
        self.active_sessions[child_profile] = session
        
        logger.info(f"Started session for {child_profile}: {session.session_id}")
        return session
    
    async def end_session(self, child_profile: str) -> Optional[SessionRecord]:
        """End the active session for a child"""
        if child_profile in self.active_sessions:
            session = self.active_sessions[child_profile]
            session.end()
            
            # Move to history
            self.session_history.append(session)
            del self.active_sessions[child_profile]
            
            logger.info(f"Ended session for {child_profile}: {session.session_id}")
            return session
        return None
    
    def get_live_session(self, child_profile: str) -> Optional[Dict[str, Any]]:
        """Get the current live session for a child"""
        if child_profile in self.active_sessions:
            return self.active_sessions[child_profile].to_dict()
        return None
    
    def set_time_limit(self, child_profile: str, limit_minutes: int):
        """Set time limit for a child profile"""
        self.time_limits[child_profile] = limit_minutes
        logger.info(f"Set time limit for {child_profile}: {limit_minutes} minutes")
    
    def check_time_limits(self) -> List[str]:
        """Check if any active sessions exceed time limits"""
        exceeded_profiles = []
        
        for child_profile, session in self.active_sessions.items():
            if child_profile in self.time_limits:
                limit_seconds = self.time_limits[child_profile] * 60
                current_duration = (datetime.now(timezone.utc) - session.time_start).total_seconds()
                
                if current_duration > limit_seconds:
                    exceeded_profiles.append(child_profile)
        
        return exceeded_profiles

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self):
        self.notification_history = []
    
    async def send_desktop_notification(self, title: str, message: str) -> bool:
        """Send a desktop notification"""
        try:
            notification_data = {
                "title": title,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.notification_history.append(notification_data)
            
            # Try to send system notification
            if platform.system() == "Windows":
                await self._send_windows_notification(title, message)
            elif platform.system() == "Darwin":  # macOS
                await self._send_macos_notification(title, message)
            else:  # Linux
                await self._send_linux_notification(title, message)
            
            logger.info(f"Sent notification: {title} - {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def _send_windows_notification(self, title: str, message: str):
        """Send Windows toast notification"""
        try:
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(title, message, duration=10)
        except ImportError:
            logger.warning("win10toast not available, using print fallback")
            print(f"🚨 NOTIFICATION: {title} - {message}")
    
    async def _send_macos_notification(self, title: str, message: str):
        """Send macOS notification"""
        try:
            subprocess.run([
                "osascript", "-e", 
                f'display notification "{message}" with title "{title}"'
            ])
        except Exception:
            print(f"🚨 NOTIFICATION: {title} - {message}")
    
    async def _send_linux_notification(self, title: str, message: str):
        """Send Linux notification"""
        try:
            subprocess.run(["notify-send", title, message])
        except Exception:
            print(f"🚨 NOTIFICATION: {title} - {message}")

class SystemInfoService:
    """Service for retrieving system information"""
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "platform": platform.platform(),
                "system": platform.system(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}

# Firebase Integration
class FirebaseService:
    """Service for Firebase integration"""
    
    def __init__(self):
        self.firebase_initialized = False
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase connection"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Look for Firebase credentials file
            cred_file = "robloxlog-264f8-firebase-adminsdk-fbsvc-4b42b3cb1f.json"
            if Path(cred_file).exists():
                cred = credentials.Certificate(cred_file)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.firebase_initialized = True
                logger.info("Firebase initialized successfully")
            else:
                logger.warning("Firebase credentials file not found")
                
        except ImportError:
            logger.warning("Firebase SDK not installed")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
    
    async def sync_session(self, session_data: Dict[str, Any]) -> bool:
        """Sync session data to Firebase"""
        if not self.firebase_initialized:
            return False
        
        try:
            doc_ref = self.db.collection('sessions').document(session_data['session_id'])
            doc_ref.set(session_data)
            logger.info(f"Synced session to Firebase: {session_data['session_id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to sync session to Firebase: {e}")
            return False

# Utility functions
def load_config() -> dict:
    """Load configuration from config.json"""
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Return default config
        default_config = {
            "auto_close_roblox": False,
            "monitor_interval": 2,
            "enable_notifications": True,
            "time_limits": {}
        }
        # Save default config
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config

def save_config(config: dict):
    """Save configuration to config.json"""
    with open("config.json", 'w') as f:
        json.dump(config, f, indent=4)
    logger.info("Configuration saved")

# Compatibility functions for existing code
async def simple_polling_monitor():
    """Legacy function for backward compatibility"""
    monitor = ProcessMonitorService()
    await monitor.start()
    while True:
        await asyncio.sleep(1)

def check_current_processes():
    """Legacy function for backward compatibility"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'roblox' in proc.info['name'].lower():
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes

async def kill_roblox_processes():
    """Legacy function for backward compatibility"""
    monitor = ProcessMonitorService()
    await monitor._kill_roblox_processes()
