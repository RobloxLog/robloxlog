from fastapi import FastAPI
from api.routes import router as api_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Starting up the application...")

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down the application...")

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)