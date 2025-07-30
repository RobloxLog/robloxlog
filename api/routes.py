from fastapi import APIRouter, BackgroundTasks
from utils.process_monitor import check_current_processes, simple_polling_monitor
import psutil
from fastapi import Request
import json
router = APIRouter()

@router.post("/load_config")
async def load_config(request: Request):
    """Load config as JSON data from POST request body."""
    data = await request.json()
    # Here you can process or save the config as needed
    with open('config.json', 'w') as f:
        json.dump(data, f, indent=4)
    return {"message": "Config loaded successfully."}
@router.get("/processes")
def get_current_processes():
    """Endpoint to get the current Roblox processes."""
    
    processes = check_current_processes()
    return {"processes": processes}

@router.post("/monitor")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Endpoint to start the process monitoring."""
    # This would ideally start the monitoring in a background task
    background_tasks.add_task(simple_polling_monitor)
    return {"message": "Monitoring started."}

@router.get("/kill_roblox")
async def kill_roblox():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            if 'roblox' in proc_name:
                print(f"Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
