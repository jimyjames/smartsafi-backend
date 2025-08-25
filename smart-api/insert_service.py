# insert_services_aligned.py
import sqlite3
from servicesData import services
import random

conn = sqlite3.connect("test.db")
cursor = conn.cursor()

def insert_data():
    for key, service in services.items():
        # Insert into service_names
        cursor.execute("INSERT INTO service_names (name) VALUES (?)", (service["title"],))
        service_name_id = cursor.lastrowid

        # Insert service_description
        cursor.execute(
            "INSERT INTO service_descriptions (title, description, service_name_id) VALUES (?, ?, ?)",
            (service["title"], service["description"], service_name_id)
        )
        service_description_id = cursor.lastrowid

        # Insert features
        for feature in service["features"]:
            cursor.execute(
                "INSERT INTO service_features (name, icon, service_description_id) VALUES (?, ?, ?)",
                (feature["title"], feature.get("icon", None), service_description_id)
            )
            service_feature_id = cursor.lastrowid

            # Insert price (dummy/randomized for now)
            price = round(random.uniform(1000, 5000), 2)
            unit = "KES"
            cursor.execute(
                "INSERT INTO service_prices (amount, unit, service_description_id, service_feature_id) VALUES (?, ?, ?, ?)",
                (price, unit, service_description_id, service_feature_id)
            )

    conn.commit()
    print("Data inserted aligned to schema.")

insert_data()
conn.close()
