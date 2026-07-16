from config.db import tracking_collection
from datetime import datetime

def add_tracking_update(shipment_id, status, location):
    tracking = {
        "shipment_id": shipment_id,
        "status": status,
        "location": location,
        "timestamp": datetime.utcnow()
    }

    tracking_collection.insert_one(tracking)


def get_tracking(shipment_id):
    return list(tracking_collection.find(
        {"shipment_id": shipment_id},
        {"_id": 0}
    ).sort("timestamp", 1))