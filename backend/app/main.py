from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.cv_router import router as cv_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv_router)

@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!"}

@app.get("/api/data")
def get_data():
    return {"data": [1, 2, 3, 4, 5]}
