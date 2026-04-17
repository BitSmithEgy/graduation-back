from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users
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

app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)