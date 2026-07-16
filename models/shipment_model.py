from config.db import shipment_collection
from datetime import datetime

def create_shipment(data):
    shipment = {
        "pickupLocation": data["pickupLocation"],
        "deliveryLocation": data["deliveryLocation"],
        "weight": data["weight"],
        "distance": data["distance"],
        "estimatedTime": data["estimatedTime"],
        "status": "Pending",
        "createdAt": datetime.utcnow()
    }

    result = shipment_collection.insert_one(shipment)
    return str(result.inserted_id)