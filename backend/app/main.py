from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()
from services.s3 import S3FileManager

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "NVDIA Financial Reports Analysis: FastAPI Backend with OpenAI Integration available for user queries..."}

