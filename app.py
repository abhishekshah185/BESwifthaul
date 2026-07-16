# from flask import Flask, request, jsonify, session
# from flask_cors import CORS
# from werkzeug.security import generate_password_hash, check_password_hash
# import pandas as pd
# import numpy as np
# import os
# from datetime import datetime, timedelta
# from sklearn.ensemble import GradientBoostingRegressor
# from sklearn.model_selection import train_test_split
# import secrets

# app = Flask(__name__)
# app.secret_key = secrets.token_hex(16)
# CORS(app, supports_credentials=True)

# # In-memory storage (replace with database in production)
# users_db = {}
# shipments_db = {}
# shipment_counter = 1

# # Global ML model
# delivery_model = None

# # ==================== ML MODEL TRAINING ====================

# def train_delivery_model():
#     """Train ML model for delivery time prediction"""
#     try:
#         dataset_paths = [
#             "delivery_data.csv",
#             "data/delivery_data.csv",
#             "Delhivery_Logistics_Cleaned.csv"
#         ]
        
#         df = None
#         for path in dataset_paths:
#             if os.path.exists(path):
#                 df = pd.read_csv(path)
#                 print(f"✓ Loaded dataset from {path}")
#                 break
        
#         if df is None:
#             print("⚠ No dataset found, using dummy model")
#             return create_dummy_model()
        
#         # Handle different column naming conventions
#         distance_cols = ['actual_distance_to_destination', 'distance', 'Distance_Km']
#         time_cols = ['actual_time', 'estimated_time', 'Time_Taken_Hrs']
        
#         distance_col = None
#         time_col = None
        
#         for col in distance_cols:
#             if col in df.columns:
#                 distance_col = col
#                 break
        
#         for col in time_cols:
#             if col in df.columns:
#                 time_col = col
#                 break
        
#         if not distance_col or not time_col:
#             print(f"⚠ Required columns not found. Available: {df.columns.tolist()}")
#             return create_dummy_model()
        
#         # Clean data
#         df = df.dropna(subset=[distance_col, time_col])
#         df = df[df[distance_col] > 0]
#         df = df[df[time_col] > 0]
        
#         if len(df) < 5:
#             print(f"⚠ Insufficient data ({len(df)} rows), using dummy model")
#             return create_dummy_model()
        
#         X = df[[distance_col]]
#         y = df[time_col]
        
#         # Convert hours to minutes if needed
#         if 'Hrs' in time_col:
#             y = y * 60
        
#         # Train model
#         X_train, X_test, y_train, y_test = train_test_split(
#             X, y, test_size=0.2, random_state=42
#         )
        
#         model = GradientBoostingRegressor(
#             n_estimators=100,
#             learning_rate=0.1,
#             max_depth=5,
#             random_state=42
#         )
#         model.fit(X_train, y_train)
        
#         train_score = model.score(X_train, y_train)
#         test_score = model.score(X_test, y_test)
        
#         print(f"✓ Model trained successfully!")
#         print(f"  Training Score: {train_score:.4f}")
#         print(f"  Test Score: {test_score:.4f}")
        
#         return model
        
#     except Exception as e:
#         print(f"✗ Error training model: {e}")
#         return create_dummy_model()

# def create_dummy_model():
#     """Dummy model when real training fails"""
#     class DummyModel:
#         def predict(self, X):
#             distances = X.iloc[:, 0] if isinstance(X, pd.DataFrame) else X
#             # Simple heuristic: ~2 min per km + some variance
#             return distances * 2 + np.random.normal(0, 3, size=len(distances))
    
#     print("ℹ Using dummy model (2 min/km baseline)")
#     return DummyModel()

# def predict_delivery_time(distance):
#     """Predict delivery time for given distance"""
#     try:
#         input_data = pd.DataFrame([[float(distance)]], columns=['distance'])
#         prediction = delivery_model.predict(input_data)[0]
#         return max(round(prediction, 2), 1)  # Minimum 1 minute
#     except Exception as e:
#         print(f"Prediction error: {e}")
#         return round(float(distance) * 2, 2)

# # Initialize model
# print("=" * 60)
# print("Initializing SwiftHaul ML Model...")
# print("=" * 60)
# delivery_model = train_delivery_model()
# print("=" * 60)

# # ==================== AUTHENTICATION ROUTES ====================

# @app.route('/api/auth/signup', methods=['POST'])
# def signup():
#     """User registration"""
#     try:
#         data = request.get_json()
#         email = data.get('email')
#         password = data.get('password')
#         name = data.get('name')
        
#         if not email or not password or not name:
#             return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
#         if email in users_db:
#             return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
#         # Store user
#         users_db[email] = {
#             'name': name,
#             'email': email,
#             'password': generate_password_hash(password),
#             'created_at': datetime.now().isoformat()
#         }
        
#         return jsonify({
#             'success': True,
#             'message': 'User registered successfully',
#             'user': {
#                 'name': name,
#                 'email': email
#             }
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/auth/login', methods=['POST'])
# def login():
#     """User login"""
#     try:
#         data = request.get_json()
#         email = data.get('email')
#         password = data.get('password')
        
#         if not email or not password:
#             return jsonify({'success': False, 'error': 'Missing credentials'}), 400
        
#         user = users_db.get(email)
#         if not user or not check_password_hash(user['password'], password):
#             return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
#         # Create session
#         session['user_email'] = email
        
#         return jsonify({
#             'success': True,
#             'message': 'Login successful',
#             'user': {
#                 'name': user['name'],
#                 'email': user['email']
#             }
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/auth/logout', methods=['POST'])
# def logout():
#     """User logout"""
#     session.pop('user_email', None)
#     return jsonify({'success': True, 'message': 'Logged out successfully'})

# # ==================== SHIPMENT ROUTES ====================

# @app.route('/api/shipments/create', methods=['POST'])
# def create_shipment():
#     """Create new shipment"""
#     global shipment_counter
    
#     try:
#         data = request.get_json()
        
#         # Extract shipment data
#         distance = float(data.get('distance', 0))
#         weight = float(data.get('weight', 0))
        
#         if distance <= 0 or weight <= 0:
#             return jsonify({'success': False, 'error': 'Invalid distance or weight'}), 400
        
#         # Predict delivery time using ML model
#         predicted_time = predict_delivery_time(distance)
#         estimated_time = predicted_time * 1.1  # Add 10% buffer for estimation
        
#         # Create shipment
#         shipment_id = str(shipment_counter)
#         shipment_counter += 1
        
#         shipment = {
#             'id': shipment_id,
#             'senderName': data.get('senderName'),
#             'senderContact': data.get('senderContact'),
#             'senderAddress': data.get('senderAddress'),
#             'pickupLocation': data.get('pickupLocation'),
#             'receiverName': data.get('receiverName'),
#             'receiverContact': data.get('receiverContact'),
#             'receiverAddress': data.get('receiverAddress'),
#             'deliveryLocation': data.get('deliveryLocation'),
#             'weight': weight,
#             'distance': distance,
#             'status': 'Pending',
#             'estimatedTime': round(estimated_time, 2),
#             'mlPrediction': predicted_time,
#             'createdAt': datetime.now().isoformat(),
#             'estimatedDelivery': (datetime.now() + timedelta(minutes=predicted_time)).isoformat()
#         }
        
#         shipments_db[shipment_id] = shipment
        
#         return jsonify({
#             'success': True,
#             'message': 'Shipment created successfully',
#             'shipment': shipment
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/shipments/track/<shipment_id>', methods=['GET'])
# def track_shipment(shipment_id):
#     """Track shipment by ID"""
#     try:
#         shipment = shipments_db.get(shipment_id)
        
#         if not shipment:
#             return jsonify({'success': False, 'error': 'Shipment not found'}), 404
        
#         return jsonify({
#             'success': True,
#             'shipment': shipment
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/shipments/all', methods=['GET'])
# def get_all_shipments():
#     """Get all shipments"""
#     try:
#         shipments = list(shipments_db.values())
#         return jsonify({
#             'success': True,
#             'shipments': shipments,
#             'count': len(shipments)
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/shipments/update/<shipment_id>', methods=['PUT'])
# def update_shipment_status(shipment_id):
#     """Update shipment status"""
#     try:
#         data = request.get_json()
#         new_status = data.get('status')
        
#         if shipment_id not in shipments_db:
#             return jsonify({'success': False, 'error': 'Shipment not found'}), 404
        
#         shipments_db[shipment_id]['status'] = new_status
#         shipments_db[shipment_id]['updatedAt'] = datetime.now().isoformat()
        
#         return jsonify({
#             'success': True,
#             'message': 'Status updated successfully',
#             'shipment': shipments_db[shipment_id]
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# # ==================== ML PREDICTION ROUTE ====================

# @app.route('/api/predict/delivery-time', methods=['POST'])
# def predict_time():
#     """Standalone prediction endpoint"""
#     try:
#         data = request.get_json()
#         distance = float(data.get('distance', 0))
        
#         if distance <= 0:
#             return jsonify({'success': False, 'error': 'Distance must be greater than 0'}), 400
        
#         predicted_time = predict_delivery_time(distance)
#         estimated_delivery = datetime.now() + timedelta(minutes=predicted_time)
        
#         return jsonify({
#             'success': True,
#             'distance': distance,
#             'predictedTime': predicted_time,
#             'estimatedDelivery': estimated_delivery.isoformat(),
#             'unit': 'minutes'
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# # ==================== SYSTEM INFO ROUTES ====================

# @app.route('/api/system/health', methods=['GET'])
# def health_check():
#     """System health check"""
#     return jsonify({
#         'status': 'healthy',
#         'timestamp': datetime.now().isoformat(),
#         'model_loaded': delivery_model is not None,
#         'total_users': len(users_db),
#         'total_shipments': len(shipments_db)
#     })

# @app.route('/api/system/model-info', methods=['GET'])
# def model_info():
#     """Get ML model information"""
#     model_type = "Gradient Boosting Regressor" if hasattr(delivery_model, 'n_estimators') else "Dummy Model"
#     return jsonify({
#         'modelType': model_type,
#         'status': 'active',
#         'description': 'ML model for delivery time prediction based on distance'
#     })

# # ==================== SAMPLE DATA SEEDER ====================

# @app.route('/api/system/seed-data', methods=['POST'])
# def seed_sample_data():
#     """Add sample shipment data for testing"""
#     global shipment_counter
    
#     sample_shipment = {
#         'id': str(shipment_counter),
#         'senderName': 'Umesh kumar',
#         'senderContact': '9321861857',
#         'senderAddress': 'mumbai maharashtra',
#         'pickupLocation': 'mumbai',
#         'receiverName': 'udayar',
#         'receiverContact': '9321861857',
#         'receiverAddress': 'maharashtra',
#         'deliveryLocation': 'chennai',
#         'weight': 50.0,
#         'distance': 1342.84,
#         'status': 'Pending',
#         'estimatedTime': 1444.02,
#         'mlPrediction': 1145.27,
#         'createdAt': datetime.now().isoformat(),
#         'estimatedDelivery': (datetime.now() + timedelta(minutes=1145.27)).isoformat()
#     }
    
#     shipments_db[str(shipment_counter)] = sample_shipment
#     shipment_counter += 1
    
#     return jsonify({
#         'success': True,
#         'message': 'Sample data seeded',
#         'shipment': sample_shipment
#     })

# # ==================== START SERVER ====================

# if __name__ == '__main__':
#     print("\n" + "=" * 60)
#     print("🚀 SwiftHaul Smart Logistics Backend")
#     print("=" * 60)
#     print("📍 Server running at: http://localhost:5000")
#     print("📊 ML Model: Active and ready")
#     print("🔗 CORS: Enabled for frontend integration")
#     print("=" * 60 + "\n")
    
#     app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify, session

from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, join_room
from pymongo import MongoClient
from bson import ObjectId
import pandas as pd
import numpy as np
import os
from datetime import datetime
import secrets
from dotenv import load_dotenv

# ==================== SETUP ====================

load_dotenv()

app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# ==================== MONGODB ====================

client = MongoClient(os.getenv("MONGO_URI"))
db = client["logistics_db"]

shipments_col = db["shipments"]
tracking_col = db["tracking"]

# ==================== HELPER ====================

def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# ==================== ML MODEL ====================

def create_dummy_model():
    class DummyModel:
        def predict(self, X):
            return X.iloc[:, 0] * 2 + np.random.normal(0, 3, size=len(X))
    return DummyModel()

delivery_model = create_dummy_model()

def predict_delivery_time(distance):
    try:
        input_data = pd.DataFrame([[float(distance)]], columns=['distance'])
        return max(round(delivery_model.predict(input_data)[0], 2), 1)
    except:
        return round(distance * 2, 2)

# ==================== SOCKET ====================

@socketio.on('join_shipment')
def handle_join(data):
    shipment_id = data.get('shipment_id')
    join_room(shipment_id)

# ==================== AUTH ====================

users_db = {}

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()

    if data['email'] in users_db:
        return jsonify({'error': 'Email exists'}), 400

    users_db[data['email']] = {
        'name': data['name'],
        'password': generate_password_hash(data['password'])
    }

    return jsonify({'success': True})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users_db.get(data['email'])

    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'error': 'Invalid'}), 401

    session['user'] = data['email']
    return jsonify({'success': True})

# ==================== CREATE SHIPMENT ====================

@app.route('/api/shipments/create', methods=['POST'])
def create_shipment():
    data = request.get_json()

    distance = float(data.get('distance', 0))
    predicted_time = predict_delivery_time(distance)

    shipment = {
        "sender": {
            "name": data.get('senderName'),
            "contact": data.get('senderContact'),
            "address": data.get('senderAddress')
        },
        "receiver": {
            "name": data.get('receiverName'),
            "contact": data.get('receiverContact'),
            "address": data.get('receiverAddress')
        },
        "pickupLocation": data.get('pickupLocation'),
        "deliveryLocation": data.get('deliveryLocation'),
        "distance": distance,
        "weight": float(data.get('weight', 0)),
        "status": "Pending",
        "estimatedTime": predicted_time,
        "mlPrediction": predicted_time,
        "createdAt": datetime.utcnow().isoformat()   # ✅ FIXED
    }

    result = shipments_col.insert_one(shipment)
    shipment_id = str(result.inserted_id)

    # ✅ Convert ObjectId → string
    shipment["_id"] = shipment_id
    shipment["id"] = shipment_id

    # ✅ FIX tracking datetime
    tracking_col.insert_one({
        "shipment_id": shipment_id,
        "status": "Pending",
        "location": shipment["pickupLocation"],
        "timestamp": datetime.utcnow().isoformat()   # ✅ FIXED
    })

    socketio.emit('new_shipment', shipment)

    return jsonify({
        "success": True,
        "shipment": shipment
    })
# ==================== TRACK SHIPMENT ====================

@app.route('/api/shipments/track/<shipment_id>', methods=['GET'])
def track(shipment_id):
    try:
        shipment = shipments_col.find_one({"_id": ObjectId(shipment_id)})

        if not shipment:
            return jsonify({"error": "Shipment not found"}), 404

        # ✅ Convert ObjectId + datetime
        shipment["_id"] = str(shipment["_id"])
        if isinstance(shipment.get("createdAt"), datetime):
            shipment["createdAt"] = shipment["createdAt"].isoformat()

        # ✅ FIX tracking serialization
        tracking_list = []
        for t in tracking_col.find({"shipment_id": shipment_id}).sort("timestamp", 1):
            t.pop("_id", None)

            if isinstance(t.get("timestamp"), datetime):
                t["timestamp"] = t["timestamp"].isoformat()

            tracking_list.append(t)

        return jsonify({
            "success": True,
            "shipment": shipment,
            "tracking": tracking_list
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": "Invalid shipment ID"}), 400
# ==================== UPDATE STATUS ====================

@app.route('/api/shipments/update/<shipment_id>', methods=['PUT'])
def update_status(shipment_id):
    data = request.get_json()

    new_status = data.get('status')
    location = data.get('location', 'Unknown')

    shipments_col.update_one(
        {"_id": ObjectId(shipment_id)},
        {"$set": {"status": new_status}}
    )

    tracking_entry = {
        "shipment_id": shipment_id,
        "status": new_status,
        "location": location,
        "timestamp": datetime.utcnow()
    }

    tracking_col.insert_one(tracking_entry)

    # Real-time emit
    socketio.emit('shipment_update', tracking_entry, room=shipment_id)

    return jsonify({"success": True})

# ==================== GET ALL ====================

@app.route('/api/shipments/all', methods=['GET'])
def all_shipments():
    shipments = []

    for s in shipments_col.find():
        shipments.append(serialize_doc(s))

    return jsonify({'shipments': shipments})

# ==================== SYSTEM ====================

@app.route('/api/system/health')
def health():
    return jsonify({
        'status': 'ok'
    })

# ==================== RUN ====================

if __name__ == '__main__':
    print("🚀 Real-Time Logistics Backend Running...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)