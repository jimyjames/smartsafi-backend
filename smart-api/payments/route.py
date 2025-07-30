from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from . import lipa_na_mpesa_online,router
from sqlalchemy.orm import Session
from schemas import ClientCreate, ClientOut, ClientBase
from models import Client, User
from database import SessionLocal, get_db
from pathlib import Path
import shutil


paymentsrouter = router

@paymentsrouter.get("/stk", response_model=dict)
def get_stk_info():
    return lipa_na_mpesa_online()   