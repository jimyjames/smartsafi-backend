from sqlalchemy.orm import Session
from models import ServiceCategory, ServiceFeature, FeatureOption
from database import SessionLocal

# Paste your JSON here
SERVICE_DATA = [
    {
        "slug": "commercial",
        "title": "Commercial Cleaning",
        "description": "Office and business cleaning services",
        "icon_name": "commercial",
        "id": 1,
        "features": [
            {
                "slug": "office-cleaning",
                "title": "Office Cleaning (Commercial)",
                "description": "Routine and deep cleaning of office spaces",
                "icon_name": "wrench",
                "id": 15,
                "options": []
            },
            {
                "slug": "post-construction",
                "title": "Post Construction (Commercial)",
                "description": "Cleanup after construction or renovations",
                "icon_name": "hammer",
                "id": 16,
                "options": []
            },
            {
                "slug": "institution-cleaning",
                "title": "Institution Cleaning (Commercial)",
                "description": "Cleaning services for schools, hospitals, and institutions",
                "icon_name": "sparkles",
                "id": 17,
                "options": [
                    {
                        "area_type": "Retail store",
                        "label": "Retail Store",
                        "unit_price": 1500.0,
                        "min_units": 1,
                        "max_units": 6,
                        "id": 4,
                        "feature": {
                            "slug": "institution-cleaning",
                            "title": "Institution Cleaning (Commercial)",
                            "category": {
                                "slug": "commercial",
                                "title": "Commercial Cleaning"
                            }
                        }
                    },
                    {
                        "area_type": "Restaurant/Cafe",
                        "label": "Restaurant/Cafe",
                        "unit_price": 20000.0,
                        "min_units": 1,
                        "max_units": 5,
                        "id": 5,
                        "feature": {
                            "slug": "institution-cleaning",
                            "title": "Institution Cleaning (Commercial)",
                            "category": {
                                "slug": "commercial",
                                "title": "Commercial Cleaning"
                            }
                        }
                    },
                    {
                        "area_type": "Club/Bar",
                        "label": "Club/bar",
                        "unit_price": 8000.0,
                        "min_units": 1,
                        "max_units": 2,
                        "id": 6,
                        "feature": {
                            "slug": "institution-cleaning",
                            "title": "Institution Cleaning (Commercial)",
                            "category": {
                                "slug": "commercial",
                                "title": "Commercial Cleaning"
                            }
                        }
                    },
                    {
                        "area_type": "Supermarket",
                        "label": "Supermarket",
                        "unit_price": 30000.0,
                        "min_units": 1,
                        "max_units": 2,
                        "id": 7,
                        "feature": {
                            "slug": "institution-cleaning",
                            "title": "Institution Cleaning (Commercial)",
                            "category": {
                                "slug": "commercial",
                                "title": "Commercial Cleaning"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "slug": "residential",
        "title": "Residential Cleaning",
        "description": "Homes, apartments, and residential properties",
        "icon_name": "residential",
        "id": 2,
        "features": [
            {
                "slug": "regular-maintenance",
                "title": "Regular Maintenance / General Cleaning (Residential)",
                "description": "Weekly or bi-weekly home upkeep cleaning",
                "icon_name": "wrench",
                "id": 13,
                "options": []
            },
            {
                "slug": "deep-cleaning",
                "title": "Deep Cleaning (Residential)",
                "description": "Comprehensive cleaning for every corner of your home",
                "icon_name": "sparkles",
                "id": 14,
                "options": []
            },
            {
                "slug": "specific-room-cleaning",
                "title": "Specific Room / Area Cleaning (Residential)",
                "description": "Targeted cleaning for kitchens, bathrooms, etc.",
                "icon_name": "home",
                "id": 18,
                "options": [
                    {
                        "area_type": "bedroom",
                        "label": "bedroom",
                        "unit_price": 800.0,
                        "min_units": 0,
                        "max_units": 10,
                        "id": 8,
                        "feature": {
                            "slug": "specific-room-cleaning",
                            "title": "Specific Room / Area Cleaning (Residential)",
                            "category": {
                                "slug": "residential",
                                "title": "Residential Cleaning"
                            }
                        }
                    },
                    {
                        "area_type": "bathroom",
                        "label": "Bathroom",
                        "unit_price": 1000.0,
                        "min_units": 1,
                        "max_units": 6,
                        "id": 9,
                        "feature": {
                            "slug": "specific-room-cleaning",
                            "title": "Specific Room / Area Cleaning (Residential)",
                            "category": {
                                "slug": "residential",
                                "title": "Residential Cleaning"
                            }
                        }
                    },
                    {
                        "area_type": "living_room",
                        "label": "Living Room",
                        "unit_price": 2500.0,
                        "min_units": 1,
                        "max_units": 5,
                        "id": 10,
                        "feature": {
                            "slug": "specific-room-cleaning",
                            "title": "Specific Room / Area Cleaning (Residential)",
                            "category": {
                                "slug": "residential",
                                "title": "Residential Cleaning"
                            }
                        }
                    },
                    {
                        "area_type": "kitchen",
                        "label": "Kitchen",
                        "unit_price": 3000.0,
                        "min_units": 1,
                        "max_units": 5,
                        "id": 11,
                        "feature": {
                            "slug": "specific-room-cleaning",
                            "title": "Specific Room / Area Cleaning (Residential)",
                            "category": {
                                "slug": "residential",
                                "title": "Residential Cleaning"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "slug": "upholstery",
        "title": "Upholstery & Carpet Cleaning",
        "description": "Fabric, carpet, and furniture cleaning services",
        "icon_name": "upholstery",
        "id": 3,
        "features": [
            {
                "slug": "carpet-cleaning",
                "title": "Carpet Cleaning",
                "description": "Deep and steam carpet cleaning",
                "icon_name": "sparkles",
                "id": 9,
                "options": []
            },
            {
                "slug": "leather-sofa-cleaning",
                "title": "Leather Sofa-set Cleaning (Upholstery)",
                "description": "Gentle cleaning for leather sofas",
                "icon_name": "sofa",
                "id": 10,
                "options": []
            },
            {
                "slug": "standard-sofa-cleaning-upholstery",
                "title": "Standard Sofa-set Cleaning (Upholstery)",
                "description": "General cleaning for fabric sofa sets",
                "icon_name": "sofa",
                "id": 11,
                "options": []
            },
            {
                "slug": "Mattress cleaning",
                "title": "Mattress  Cleaning (Upholstery)",
                "description": "General cleaning for Matresses, Remove Stains and bad odour",
                "icon_name": "mattress",
                "id": 12,
                "options": []
            }
        ]
    },
    {
        "slug": "pest-control",
        "title": "Pest Control",
        "description": "Safe and effective pest removal services",
        "icon_name": "pest-control",
        "id": 4,
        "features": [
            {
                "slug": "Rats",
                "title": "Rats",
                "description": "Some words here ",
                "icon_name": "spraycan",
                "id": 1,
                "options": []
            },
            {
                "slug": "Ants",
                "title": "Ants",
                "description": "Some words here ",
                "icon_name": "spraycan",
                "id": 2,
                "options": []
            },
            {
                "slug": "Coackroaches",
                "title": "Coackroaches",
                "description": "Some words here ",
                "icon_name": "spraycan",
                "id": 3,
                "options": []
            },
            {
                "slug": "Bedbugs",
                "title": "Bedbugs",
                "description": "Some words here ",
                "icon_name": "spraycan",
                "id": 4,
                "options": []
            },
            {
                "slug": "Bees",
                "title": "Bees",
                "description": "Some words here ",
                "icon_name": "spraycan",
                "id": 5,
                "options": []
            },
            {
                "slug": "Fleas",
                "title": "Fleas",
                "description": "Some words here ",
                "icon_name": "spraycan",
                "id": 6,
                "options": []
            }
        ]
    },
    {
        "slug": "sanitation",
        "title": "Sanitation & Hygiene Services",
        "description": "Deep sanitation for homes and businesses",
        "icon_name": "sanitation",
        "id": 5,
        "features": [
            {
                "slug": "sanitary bins",
                "title": "Sanitary Bins",
                "description": "Some words here ",
                "icon_name": "spraycan",
                "id": 19,
                "options": []
            },
            {
                "slug": "wasshroom hygiene solutions",
                "title": "Washroom Hygiene Solutions",
                "description": "Washroom maintenance",
                "icon_name": "sparkle",
                "id": 20,
                "options": [
                    {
                        "area_type": "Paper Rolls",
                        "label": "Paper Rolls",
                        "unit_price": 100.0,
                        "min_units": 1,
                        "max_units": 100,
                        "id": 12,
                        "feature": {
                            "slug": "wasshroom hygiene solutions",
                            "title": "Washroom Hygiene Solutions",
                            "category": {
                                "slug": "sanitation",
                                "title": "Sanitation & Hygiene Services"
                            }
                        }
                    },
                    {
                        "area_type": "Pedal Bins",
                        "label": "Pedal Bins",
                        "unit_price": 1500.0,
                        "min_units": 1,
                        "max_units": 20,
                        "id": 13,
                        "feature": {
                            "slug": "wasshroom hygiene solutions",
                            "title": "Washroom Hygiene Solutions",
                            "category": {
                                "slug": "sanitation",
                                "title": "Sanitation & Hygiene Services"
                            }
                        }
                    },
                    {
                        "area_type": "Dispenser",
                        "label": "Dispenser",
                        "unit_price": 15000.0,
                        "min_units": 1,
                        "max_units": 5,
                        "id": 14,
                        "feature": {
                            "slug": "wasshroom hygiene solutions",
                            "title": "Washroom Hygiene Solutions",
                            "category": {
                                "slug": "sanitation",
                                "title": "Sanitation & Hygiene Services"
                            }
                        }
                    },
                    {
                        "area_type": "Sanitizers",
                        "label": "Sanitizers",
                        "unit_price": 2000.0,
                        "min_units": 1,
                        "max_units": 50,
                        "id": 15,
                        "feature": {
                            "slug": "wasshroom hygiene solutions",
                            "title": "Washroom Hygiene Solutions",
                            "category": {
                                "slug": "sanitation",
                                "title": "Sanitation & Hygiene Services"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "slug": "laundry",
        "title": "Laundry Service",
        "description": "Professional laundry and folding services",
        "icon_name": "laundry",
        "id": 6,
        "features": [
            {
                "slug": "leather-cleaning-laundry",
                "title": "Leather Cleaning (Laundry)",
                "description": "Special treatment for leather garments",
                "icon_name": "spraycan",
                "id": 7,
                "options": []
            },
            {
                "slug": "Washing",
                "title": "Washing (Laundry)",
                "description": "Professional cleaning,Ironing and pressing of clothes",
                "icon_name": "wrench",
                "id": 8,
                "options": [
                    {
                        "area_type": "dry and fold",
                        "label": "dry and fold",
                        "unit_price": 600.0,
                        "min_units": 20,
                        "max_units": 100,
                        "id": 1,
                        "feature": {
                            "slug": "Washing",
                            "title": "Washing (Laundry)",
                            "category": {
                                "slug": "laundry",
                                "title": "Laundry Service"
                            }
                        }
                    },
                    {
                        "area_type": "Ironing",
                        "label": "Ironing",
                        "unit_price": 1000.0,
                        "min_units": 10,
                        "max_units": 100,
                        "id": 2,
                        "feature": {
                            "slug": "Washing",
                            "title": "Washing (Laundry)",
                            "category": {
                                "slug": "laundry",
                                "title": "Laundry Service"
                            }
                        }
                    },
                    {
                        "area_type": "Pressing",
                        "label": "Pressing",
                        "unit_price": 500.0,
                        "min_units": 15,
                        "max_units": 100,
                        "id": 3,
                        "feature": {
                            "slug": "Washing",
                            "title": "Washing (Laundry)",
                            "category": {
                                "slug": "laundry",
                                "title": "Laundry Service"
                            }
                        }
                    }
                ]
            }
        ]
    }
]


def seed_services(db: Session):
    for category_data in SERVICE_DATA:
        category = ServiceCategory(
            slug=category_data["slug"],
            title=category_data["title"],
            description=category_data.get("description"),
            icon_name=category_data.get("icon_name")
        )
        db.add(category)
        db.flush()  # get category.id before committing

        for feature_data in category_data.get("features", []):
            feature = ServiceFeature(
                slug=feature_data["slug"],
                title=feature_data["title"],
                description=feature_data.get("description"),
                icon_name=feature_data.get("icon_name"),
                category_id=category.id
            )
            db.add(feature)
            db.flush()

            for option_data in feature_data.get("options", []):
                option = FeatureOption(
                    area_type=option_data["area_type"],
                    label=option_data["label"],
                    unit_price=option_data["unit_price"],
                    min_units=option_data.get("min_units"),
                    max_units=option_data.get("max_units"),
                    feature_id=feature.id
                )
                db.add(option)

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    seed_services(db)
    db.close()
    print("✅ Service data seeded successfully!")
