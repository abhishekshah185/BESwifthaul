from models.tracking_model import add_tracking_update

def update_shipment_tracking(shipment_id):
    add_tracking_update(shipment_id, "Pending", "Mumbai")
    add_tracking_update(shipment_id, "Picked Up", "Mumbai Warehouse")
    add_tracking_update(shipment_id, "In Transit", "Surat")
    add_tracking_update(shipment_id, "Out for Delivery", "Delhi")