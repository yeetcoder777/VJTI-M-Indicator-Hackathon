from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data_input import router as data_input_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_input_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the M-Indicator Hackathon API"}