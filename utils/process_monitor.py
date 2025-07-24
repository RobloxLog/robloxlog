import psutil
import time
import asyncio
import json
from record import Record

ROBLOX_PROCESSES = [
    "RobloxPlayerBeta.exe",
    "RobloxStudioBeta.exe",
    "RobloxPlayerLauncher.exe",
]

def load_config() -> dict:
    with open('config.json', 'r') as f:
        return json.load(f)

def check_current_processes():
    """Debug function to see what processes are currently running"""
    print("Current running processes containing 'roblox' or 'dart':")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            if 'roblox' in proc_name:
                print(f"  Found: {proc.info['name']} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

async def kill_roblox_processes():
    """Kill all Roblox processes"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            if 'roblox' in proc_name:
                print(f"Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

async def simple_polling_monitor():
    record = Record()
    """Alternative monitoring method using simple polling"""
    known_processes = set()

    conf = load_config()

    # Get initial state
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in ROBLOX_PROCESSES:
                known_processes.add((proc.info['pid'], proc.info['name']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    while True:
        
        current_processes = set()

        # Get current processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] in ROBLOX_PROCESSES:
                    current_processes.add((proc.info['pid'], proc.info['name']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Check for new processes
        new_processes = current_processes - known_processes
        for pid, name in new_processes:
            print(f"Process started: {name} (PID: {pid})")
            print(conf)
            if conf["auto_close_roblox"]:
                await kill_roblox_processes()

            
            record.start()
            send_mobile_alert(f"{name} has started (PID: {pid})")

        # Check for terminated processes
        terminated_processes = known_processes - current_processes
        for pid, name in terminated_processes:
            print(f"Process terminated: {name} (PID: {pid})")
            send_mobile_alert(f"{name} has closed (PID: {pid})")
            record.end()

        known_processes = current_processes
        await asyncio.sleep(1)  # Poll every 5 seconds

def send_mobile_alert(message):
    print(f"🚨 ALERT TRIGGERED: {message}")
    # TODO: Add Firebase notification logic here