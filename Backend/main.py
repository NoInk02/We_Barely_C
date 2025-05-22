from fastapi import FastAPI, Form, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json

app = FastAPI()

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register/client")
async def register_client():
    return JSONResponse(content={"message": "Client registered successfully"}, status_code=status.HTTP_200_OK)

@app.post("/register/support_agent")
async def register_support_agent():
    return {"message": "Support agent registered successfully"}

@app.post("/login")
async def login(username: str, password = Form(...)):
    # Logic for checking

    return {"tokenID": "Jwt token"}