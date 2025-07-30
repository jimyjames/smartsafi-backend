from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, APIRouter
from sqlalchemy.orm import Session
from schemas import WorkerBase, WorkerOut
from models import Workers, User, Client
from database import get_db
from pathlib import Path
import shutil

router = APIRouter(prefix="/workers", tags=["workers"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.put("/", response_model=WorkerOut)
def update_worker(worker_id: int, worker: WorkerBase, db: Session = Depends(get_db)):
    db_worker = db.query(Workers).filter(Workers.worker_id == worker_id).first()
    if not db_worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    for key, value in worker.dict().items():
        setattr(db_worker, key, value)
    db.commit()
    db.refresh(db_worker)
    return db_worker

@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(worker_id: int, db: Session = Depends(get_db)):
    db_worker = db.query(Workers).filter(Workers.worker_id == worker_id).first()
    if not db_worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    db.delete(db_worker)
    db.commit()
    return {"message": "Worker deleted successfully"}


@router.get("/", response_model=list[WorkerOut])
def get_workers(db: Session = Depends(get_db)):
    workers = db.query(Workers).all()
    return workers

@router.get("/{worker_id}", response_model=WorkerOut)
def get_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Workers).filter(Workers.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker

@router.post("/", response_model=WorkerOut)
def create_worker(worker: WorkerBase, db: Session = Depends(get_db)):
    existing_worker = db.query(Workers).filter(Workers.user_id == worker.user_id).first()
    if existing_worker:
        raise HTTPException(status_code=403, detail="Worker account already exists for this user, try updating the account")
    user_exists = db.query(User).filter(User.id == worker.user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")
    existing_client = db.query(Client).filter(Client.user_id == worker.user_id).first()
    if existing_client:
        raise HTTPException(status_code=403, detail="Client account already exists for this user, try updating the account")
    db_worker = Workers(**worker.dict())
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker

@router.post("/{worker_id}/upload", response_model=WorkerOut)
def upload_worker_documents(
    worker_id:int,
    national_id_proof: UploadFile = File(...),
    good_conduct_proof: UploadFile = File(...),
    tax_document_proof: UploadFile = File(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    worker = db.query(Workers).filter(Workers.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="worker not found")

    # Create upload folder
    worker_folder = UPLOAD_DIR / f"worker_{worker.user_id}"
    worker_folder.mkdir(parents=True, exist_ok=True)

    

    def save_file(upload: UploadFile, name: str) -> str:
        path = worker_folder / f"{name}_{upload.filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        return str(path)

    # Save files
    worker.national_id_proof = save_file(national_id_proof, "id")
    worker.good_conduct_proof = save_file(good_conduct_proof, "conduct")
    if tax_document_proof:
        worker.tax_document_proof = save_file(tax_document_proof, "tax")
    if image:
        worker.image_path = save_file(image, "image")

    db.commit()
    db.refresh(worker)
    return worker
    pass
