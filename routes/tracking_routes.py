from flask import Blueprint, jsonify
from models.tracking_model import get_tracking

tracking_bp = Blueprint("tracking", __name__)

@tracking_bp.route("/track/<shipment_id>", methods=["GET"])
def track(shipment_id):
    data = get_tracking(shipment_id)

    return jsonify({
        "success": True,
        "tracking": data
    })