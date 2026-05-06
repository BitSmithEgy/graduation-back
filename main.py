import sys
sys.dont_write_bytecode = True

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import importlib
import database

database.init_db()
app = FastAPI(title="Graduation Project API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to the Graduation Project API!"}

ROUTERS_DIR = os.path.join(os.path.dirname(__file__), "routers")
for filename in os.listdir(ROUTERS_DIR):
    if filename.endswith(".py") and not filename.startswith("__"):
        module_name = filename[:-3]
        module = importlib.import_module(f"routers.{module_name}")
        if hasattr(module, "router"):
            app.include_router(module.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)