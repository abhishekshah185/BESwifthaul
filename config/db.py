from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["logistics_db"]

shipment_collection = db["shipments"]
tracking_collection = db["tracking_updates"]