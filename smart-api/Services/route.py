from . import router
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session, joinedload
from schemas import ServiceNameBase,ServiceNameOut,ServiceDescriptionBase,ServiceDescriptionOut,ServiceFeatureBase,ServiceFeatureOut,ServicePriceBase,ServicePriceOut
from models import ServiceName,ServiceDescription,ServiceFeature,ServicePrice
from database import get_db

service_router = router
@service_router.post("/service-name", response_model=ServiceNameOut)
def create_service_name(service_name: ServiceNameBase, db: Session = Depends(get_db)):
    # Check if the service name already exists
    existing_service = db.query(ServiceName).filter(ServiceName.name == service_name.name).first()
    if existing_service:
        raise HTTPException(status_code=400, detail="Service name already exists")
    db_service_name = ServiceName(**service_name.dict())
    db.add(db_service_name)
    db.commit()
    db.refresh(db_service_name)
    return db_service_name

@service_router.post("/service-description/", response_model=ServiceDescriptionOut)
def create_service_description(service_description: ServiceDescriptionBase, db: Session = Depends(get_db)):
    # Ensure the service_name_id exists

    db_service_description = ServiceDescription(**service_description.dict())
    db.add(db_service_description)
    db.commit()
    db.refresh(db_service_description)
    return db_service_description

@service_router.post("/service-feature/", response_model=ServiceFeatureOut)
def create_service_feature(service_feature: ServiceFeatureBase, db: Session = Depends(get_db)):
    # Ensure the service_description_id exists
    db_service_feature = ServiceFeature(**service_feature.dict())
    db.add(db_service_feature)
    db.commit()
    db.refresh(db_service_feature)
    return db_service_feature
@service_router.post("/service-price/", response_model=ServicePriceOut)
def create_service_price(service_price: ServicePriceBase, db: Session = Depends(get_db)):
    # Ensure the service_feature_id and service_description_id exist
    db_service_price = ServicePrice(**service_price.dict())
    db.add(db_service_price)
    db.commit()
    db.refresh(db_service_price)
    return db_service_price

@service_router.get("/service-names/", response_model=list[ServiceNameOut])
def get_service_names(db: Session = Depends(get_db)):
    service_names = db.query(ServiceName).all()
    return service_names
@service_router.get("/service-descriptions/", response_model=list[ServiceDescriptionOut])
def get_service_descriptions(db: Session = Depends(get_db)):
    service_descriptions = db.query(ServiceDescription).all()
    return service_descriptions 


# @service_router.get("/service-features/", response_model=list[ServiceFeatureOut])
# def get_service_features(db: Session = Depends(get_db)):
#     # service_features = db.query(ServiceFeature).all()
#     service_features = (
#         db.query(ServiceFeature)
#         .options(joinedload(ServiceFeature.prices))
#         .all()
#     )
#     print("Fetching service features", service_features)
#     return service_features

from sqlalchemy.orm import joinedload

@service_router.get("/service-features/", response_model=list[ServiceFeatureOut])
def get_service_features(db: Session = Depends(get_db)):
    service_features = (
        db.query(ServiceFeature)
        .options(
            joinedload(ServiceFeature.prices),
            joinedload(ServiceFeature.service_description).joinedload(ServiceDescription.service_name)
        )
        .all()
    )
    return service_features

@service_router.get("/service-prices/", response_model=list[ServicePriceOut])
def get_service_prices(db: Session = Depends(get_db)):
    service_prices = db.query(ServicePrice).all()
    return service_prices


