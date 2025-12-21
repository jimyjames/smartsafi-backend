from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status,APIRouter, Form
from sqlalchemy.orm import Session
from schemas import ClientCreate, ClientOut, ClientBase
from models import Client,User  
from database import SessionLocal, get_db  
from pathlib import Path
import shutil
from typing import Optional



router = APIRouter(prefix="/clients", tags=["clients"])



UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# @router.post("/", response_model=ClientOut)
# def create_client(client: ClientCreate, db: Session = Depends(get_db)):
#     user_exists = db.query(User).filter(User.id == client.user_id).first()
#     if not user_exists:
#         raise HTTPException(status_code=404, detail="User not found")
#     existing = db.query(Client).filter(Client.user_id == client.user_id).first()
#     if existing:
#         raise HTTPException(status_code=403, detail="Client already exists for this user")

#     db_client = Client(**client.dict())
#     db.add(db_client)
#     db.commit()
#     db.refresh(db_client)
#     return db_client


# @router.post("/{client_id}/upload", response_model=ClientOut)
# def upload_proof_files(
#     client_id: int,
#     national_id_proof: UploadFile = File(...),
#     tax_document_proof: UploadFile = File(...),
#     image: UploadFile = File(None),
#     db: Session = Depends(get_db)
# ):
#     client = db.query(Client).filter(Client.client_id == client_id).first()
#     if not client:
#         raise HTTPException(status_code=404, detail="Client not found")

#     # Create upload folder
#     client_folder = UPLOAD_DIR / f"client_{client.user_id}"
#     client_folder.mkdir(parents=True, exist_ok=True)

#     def save_file(upload: UploadFile, name: str) -> str:
#         path = client_folder / f"{name}_{upload.filename}"
#         with open(path, "wb") as f:
#             shutil.copyfileobj(upload.file, f)
#         return str(path)

#     # Save files
#     client.national_id_proof = save_file(national_id_proof, "id")
#     client.tax_document_proof = save_file(tax_document_proof, "tax")
#     if image:
#         client.image_path = save_file(image, "image")

#     db.commit()
#     db.refresh(client)
#     return client

@router.post("/", response_model=ClientOut)
def register_client_with_files(
    user_id: int = Form(...),
    client_type: str = Form(...),  # "individual" or "organization"
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    organization_name: Optional[str] = Form(None),
    tax_number: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    national_id_number: Optional[int] = Form(None),
    address: Optional[str] = Form(None),

    national_id_proof: UploadFile = File(...),
    tax_document_proof: UploadFile = File(None),
    profile_picture: UploadFile = File(None),

    db: Session = Depends(get_db)
):
    print
    # 1. Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check existing client
    if db.query(Client).filter(Client.user_id == user_id).first():
        raise HTTPException(status_code=403, detail="Client already exists")

    # 3. Validate fields based on client_type
    if client_type == "individual":
        if not first_name or not last_name:
            raise HTTPException(status_code=422, detail="first_name and last_name are required for individual clients.")
    elif client_type == "organization":
        if not organization_name or not tax_number:
            raise HTTPException(status_code=422, detail="organization_name and tax_number are required for organizations.")
    else:
        raise HTTPException(status_code=422, detail="Invalid client_type. Must be 'individual' or 'organization'.")

    # 4. Create client record
    client = Client(
        user_id=user_id,
        client_type=client_type,
        first_name=first_name,
        last_name=last_name,
        organization_name=organization_name,
        tax_number=tax_number,
        phone_number=phone_number,
        national_id_number=national_id_number,
        address=address,
        verification_id=False,
        verification_tax=False
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    # 5. Save uploaded files
    client_folder = UPLOAD_DIR / f"client_{user_id}"
    client_folder.mkdir(parents=True, exist_ok=True)

    def save_file(file: UploadFile, prefix: str) -> str:
        path = client_folder / f"{prefix}_{file.filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return str(path)

    client.national_id_proof = save_file(national_id_proof, "id")
    if tax_document_proof:
         client.tax_document_proof = save_file(tax_document_proof, "tax")
    if profile_picture:
        client.profile_picture = save_file(profile_picture, "profile")

    db.commit()
    db.refresh(client)
    return client

@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.get("/", response_model=list[ClientOut])    
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return clients
@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, client: ClientBase, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.client_id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in client.dict().items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client


router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.client_id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(db_client)
    db.commit()
    return {"message": "Client deleted successfully"}