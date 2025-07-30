from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status,APIRouter
from sqlalchemy.orm import Session
from schemas import ClientCreate, ClientOut, ClientBase
from models import Client,User  
from database import SessionLocal, get_db  
from pathlib import Path
import shutil



router = APIRouter(prefix="/clients", tags=["clients"])



UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/", response_model=ClientOut)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    user_exists = db.query(User).filter(User.id == client.user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(Client).filter(Client.user_id == client.user_id).first()
    if existing:
        raise HTTPException(status_code=403, detail="Client already exists for this user")

    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.post("/{client_id}/upload", response_model=ClientOut)
def upload_proof_files(
    client_id: int,
    national_id_proof: UploadFile = File(...),
    tax_document_proof: UploadFile = File(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Create upload folder
    client_folder = UPLOAD_DIR / f"client_{client.user_id}"
    client_folder.mkdir(parents=True, exist_ok=True)

    def save_file(upload: UploadFile, name: str) -> str:
        path = client_folder / f"{name}_{upload.filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        return str(path)

    # Save files
    client.national_id_proof = save_file(national_id_proof, "id")
    client.tax_document_proof = save_file(tax_document_proof, "tax")
    if image:
        client.image_path = save_file(image, "image")

    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.client_id == client_id).first()
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