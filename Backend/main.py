from fastapi import FastAPI, Form, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from router import admin_router, company_router, client_router, chats_router, helper_router, ticket_router
import uvicorn
import os
import json
import yaml

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


app.include_router(admin_router.router)
app.include_router(company_router.router)
app.include_router(client_router.router)
app.include_router(chats_router.router)
app.include_router(helper_router.router)
app.include_router(ticket_router.router)

if '__name__' == '__main__':
    uvicorn.run("main:app", host='localhost', port=8000)