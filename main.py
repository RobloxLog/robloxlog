from fastapi import FastAPI, Request
from api.routes import router as api_router
import asyncio
from utils.process_monitor import simple_polling_monitor, check_current_processes, kill_roblox_processes, load_config

app = FastAPI()

monitor_task = None

@app.on_event("startup")
async def startup_event():
    print("Starting up the application...")
    conf = load_config()
    # Check for running Roblox processes on startup
    processes = check_current_processes()
    if processes and conf.get("auto_close_roblox", False):
        await kill_roblox_processes()
    # Start monitoring automatically
    global monitor_task
    monitor_task = asyncio.create_task(simple_polling_monitor())

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down the application...")
    global monitor_task
    if monitor_task:
        monitor_task.cancel()

@app.post("/start_monitoring")
async def start_monitoring():
    global monitor_task
    if monitor_task is None or monitor_task.done():
        monitor_task = asyncio.create_task(simple_polling_monitor())
        return {"message": "Monitoring started."}
    else:
        return {"message": "Monitoring is already running."}

@app.post("/stop_monitoring")
async def stop_monitoring():
    global monitor_task
    if monitor_task and not monitor_task.done():
        monitor_task.cancel()
        return {"message": "Monitoring stopped."}
    else:
        return {"message": "Monitoring is not running."}

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)