# main.py
from fastapi import FastAPI

app = FastAPI(title="llm-p") 

@app.get("/")
def read_root():
    return {"Hello": "World"}