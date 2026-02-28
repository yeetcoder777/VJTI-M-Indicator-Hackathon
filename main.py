from fastapi import FastAPI
from data_input import router as data_input_router

app = FastAPI()

app.include_router(data_input_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the M-Indicator Hackathon API"}