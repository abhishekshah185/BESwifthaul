from flask import Blueprint, request, jsonify
from models.shipment_model import create_shipment
from services.tracking_service import update_shipment_tracking

shipment_bp = Blueprint("shipment", __name__)

@shipment_bp.route("/create", methods=["POST"])
def create():
    data = request.json

    shipment_id = create_shipment(data)

    # Automatically add tracking steps
    update_shipment_tracking(shipment_id)

    return jsonify({
        "success": True,
        "shipment_id": shipment_id
    })