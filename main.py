from fastapi import FastAPI
from routers import users
import database

database.init_db()
app = FastAPI(title="Graduation Project API")

@app.get("/")
def root():
    return {"message": "Welcome to the Graduation Project API!"}

app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)