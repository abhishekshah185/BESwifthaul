# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from werkzeug.security import generate_password_hash, check_password_hash
# import os

# app = Flask(__name__)
# # A secret key is required for session management
# app.secret_key = os.urandom(24)

# # --- Dummy Database for Demonstration ---
# # In a real application, this would be a proper database.
# USERS_DB = {
#     'user@example.com': {
#         'name': 'Test User',
#         'password': generate_password_hash('user123'),
#         'role': 'user'
#     },
#     'admin@example.com': {
#         'name': 'Admin User',
#         'password': generate_password_hash('admin123'),
#         'role': 'admin'
#     }
# }
# SHIPMENTS_DB = []


# @app.route('/')
# def home():
#     """Redirects to the login page if not logged in."""
#     if 'user_email' not in session:
#         return redirect(url_for('login'))
#     return redirect(url_for('dashboard'))


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     """Handles user login."""
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         user = USERS_DB.get(email)

#         if user and check_password_hash(user['password'], password):
#             # Store user info in session
#             session['user_email'] = email
#             session['user_role'] = user['role']
#             flash('Login successful!', 'success')
#             return redirect(url_for('dashboard'))
#         else:
#             flash('Invalid email or password.', 'danger')
#     return render_template('login.html')


# @app.route('/dashboard')
# def dashboard():
#     """Displays the user or admin dashboard."""
#     if 'user_email' not in session:
#         flash('Please log in to access the dashboard.', 'warning')
#         return redirect(url_for('login'))

#     user_role = session.get('user_role', 'user')
#     return render_template('dashboard.html', role=user_role)


# @app.route('/new-shipment', methods=['GET', 'POST'])
# def new_shipment():
#     """Handles the creation of a new shipment."""
#     if 'user_email' not in session:
#         return redirect(url_for('login'))

#     if request.method == 'POST':
#         # Create a new shipment record from the form data
#         shipment = {
#             "consignor_name": request.form.get('consignor_name'),
#             "consignor_number": request.form.get('consignor_number'),
#             "address": request.form.get('address'),
#             "consignee_name": request.form.get('consignee_name'),
#             "consignee_number": request.form.get('consignee_number'),
#             "from_location": request.form.get('from_location'),
#             "to_location": request.form.get('to_location'),
#             "weight_kg": request.form.get('weight_kg'),
#             "quantity": request.form.get('quantity'),
#             "status": "Pending Approval"
#         }
#         SHIPMENTS_DB.append(shipment)
#         flash('New shipment request has been created.', 'success')
#         return redirect(url_for('dashboard'))

#     return render_template('new_shipment.html')


# @app.route('/logout')
# def logout():
#     """Logs the user out by clearing the session."""
#     session.clear()
#     flash('You have been logged out.', 'info')
#     return redirect(url_for('login'))


# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app, supports_credentials=True)

# In-memory storage (replace with database in production)
users_db = {}
shipments_db = {}
shipment_counter = 1

# Global ML model
delivery_model = None

# ==================== ML MODEL TRAINING ====================

def train_delivery_model():
    """Train ML model for delivery time prediction"""
    try:
        dataset_paths = [
            "delivery_data.csv",
            "data/delivery_data.csv",
            "Delhivery_Logistics_Cleaned.csv"
        ]
        
        df = None
        for path in dataset_paths:
            if os.path.exists(path):
                df = pd.read_csv(path)
                print(f"✓ Loaded dataset from {path}")
                break
        
        if df is None:
            print("⚠ No dataset found, using dummy model")
            return create_dummy_model()
        
        # Handle different column naming conventions
        distance_cols = ['actual_distance_to_destination', 'distance', 'Distance_Km']
        time_cols = ['actual_time', 'estimated_time', 'Time_Taken_Hrs']
        
        distance_col = None
        time_col = None
        
        for col in distance_cols:
            if col in df.columns:
                distance_col = col
                break
        
        for col in time_cols:
            if col in df.columns:
                time_col = col
                break
        
        if not distance_col or not time_col:
            print(f"⚠ Required columns not found. Available: {df.columns.tolist()}")
            return create_dummy_model()
        
        # Clean data
        df = df.dropna(subset=[distance_col, time_col])
        df = df[df[distance_col] > 0]
        df = df[df[time_col] > 0]
        
        if len(df) < 5:
            print(f"⚠ Insufficient data ({len(df)} rows), using dummy model")
            return create_dummy_model()
        
        X = df[[distance_col]]
        y = df[time_col]
        
        # Convert hours to minutes if needed
        if 'Hrs' in time_col:
            y = y * 60
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        print(f"✓ Model trained successfully!")
        print(f"  Training Score: {train_score:.4f}")
        print(f"  Test Score: {test_score:.4f}")
        
        return model
        
    except Exception as e:
        print(f"✗ Error training model: {e}")
        return create_dummy_model()

def create_dummy_model():
    """Dummy model when real training fails"""
    class DummyModel:
        def predict(self, X):
            distances = X.iloc[:, 0] if isinstance(X, pd.DataFrame) else X
            # Simple heuristic: ~2 min per km + some variance
            return distances * 2 + np.random.normal(0, 3, size=len(distances))
    
    print("ℹ Using dummy model (2 min/km baseline)")
    return DummyModel()

def predict_delivery_time(distance):
    """Predict delivery time for given distance"""
    try:
        input_data = pd.DataFrame([[float(distance)]], columns=['distance'])
        prediction = delivery_model.predict(input_data)[0]
        return max(round(prediction, 2), 1)  # Minimum 1 minute
    except Exception as e:
        print(f"Prediction error: {e}")
        return round(float(distance) * 2, 2)

# Initialize model
print("=" * 60)
print("Initializing SwiftHaul ML Model...")
print("=" * 60)
delivery_model = train_delivery_model()
print("=" * 60)

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password or not name:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if email in users_db:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Store user
        users_db[email] = {
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': {
                'name': name,
                'email': email
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Missing credentials'}), 400
        
        user = users_db.get(email)
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Create session
        session['user_email'] = email
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'name': user['name'],
                'email': user['email']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    session.pop('user_email', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# ==================== SHIPMENT ROUTES ====================

@app.route('/api/shipments/create', methods=['POST'])
def create_shipment():
    """Create new shipment"""
    global shipment_counter
    
    try:
        data = request.get_json()
        
        # Extract shipment data
        distance = float(data.get('distance', 0))
        weight = float(data.get('weight', 0))
        
        if distance <= 0 or weight <= 0:
            return jsonify({'success': False, 'error': 'Invalid distance or weight'}), 400
        
        # Predict delivery time using ML model
        predicted_time = predict_delivery_time(distance)
        estimated_time = predicted_time * 1.1  # Add 10% buffer for estimation
        
        # Create shipment
        shipment_id = str(shipment_counter)
        shipment_counter += 1
        
        shipment = {
            'id': shipment_id,
            'senderName': data.get('senderName'),
            'senderContact': data.get('senderContact'),
            'senderAddress': data.get('senderAddress'),
            'pickupLocation': data.get('pickupLocation'),
            'receiverName': data.get('receiverName'),
            'receiverContact': data.get('receiverContact'),
            'receiverAddress': data.get('receiverAddress'),
            'deliveryLocation': data.get('deliveryLocation'),
            'weight': weight,
            'distance': distance,
            'status': 'Pending',
            'estimatedTime': round(estimated_time, 2),
            'mlPrediction': predicted_time,
            'createdAt': datetime.now().isoformat(),
            'estimatedDelivery': (datetime.now() + timedelta(minutes=predicted_time)).isoformat()
        }
        
        shipments_db[shipment_id] = shipment
        
        return jsonify({
            'success': True,
            'message': 'Shipment created successfully',
            'shipment': shipment
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shipments/track/<shipment_id>', methods=['GET'])
def track_shipment(shipment_id):
    """Track shipment by ID"""
    try:
        shipment = shipments_db.get(shipment_id)
        
        if not shipment:
            return jsonify({'success': False, 'error': 'Shipment not found'}), 404
        
        return jsonify({
            'success': True,
            'shipment': shipment
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shipments/all', methods=['GET'])
def get_all_shipments():
    """Get all shipments"""
    try:
        shipments = list(shipments_db.values())
        return jsonify({
            'success': True,
            'shipments': shipments,
            'count': len(shipments)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shipments/update/<shipment_id>', methods=['PUT'])
def update_shipment_status(shipment_id):
    """Update shipment status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if shipment_id not in shipments_db:
            return jsonify({'success': False, 'error': 'Shipment not found'}), 404
        
        shipments_db[shipment_id]['status'] = new_status
        shipments_db[shipment_id]['updatedAt'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully',
            'shipment': shipments_db[shipment_id]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ML PREDICTION ROUTE ====================

@app.route('/api/predict/delivery-time', methods=['POST'])
def predict_time():
    """Standalone prediction endpoint"""
    try:
        data = request.get_json()
        distance = float(data.get('distance', 0))
        
        if distance <= 0:
            return jsonify({'success': False, 'error': 'Distance must be greater than 0'}), 400
        
        predicted_time = predict_delivery_time(distance)
        estimated_delivery = datetime.now() + timedelta(minutes=predicted_time)
        
        return jsonify({
            'success': True,
            'distance': distance,
            'predictedTime': predicted_time,
            'estimatedDelivery': estimated_delivery.isoformat(),
            'unit': 'minutes'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SYSTEM INFO ROUTES ====================

@app.route('/api/system/health', methods=['GET'])
def health_check():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': delivery_model is not None,
        'total_users': len(users_db),
        'total_shipments': len(shipments_db)
    })

@app.route('/api/system/model-info', methods=['GET'])
def model_info():
    """Get ML model information"""
    model_type = "Gradient Boosting Regressor" if hasattr(delivery_model, 'n_estimators') else "Dummy Model"
    return jsonify({
        'modelType': model_type,
        'status': 'active',
        'description': 'ML model for delivery time prediction based on distance'
    })

# ==================== SAMPLE DATA SEEDER ====================

@app.route('/api/system/seed-data', methods=['POST'])
def seed_sample_data():
    """Add sample shipment data for testing"""
    global shipment_counter
    
    sample_shipment = {
        'id': str(shipment_counter),
        'senderName': 'Umesh kumar',
        'senderContact': '9321861857',
        'senderAddress': 'mumbai maharashtra',
        'pickupLocation': 'mumbai',
        'receiverName': 'udayar',
        'receiverContact': '9321861857',
        'receiverAddress': 'maharashtra',
        'deliveryLocation': 'chennai',
        'weight': 50.0,
        'distance': 1342.84,
        'status': 'Pending',
        'estimatedTime': 1444.02,
        'mlPrediction': 1145.27,
        'createdAt': datetime.now().isoformat(),
        'estimatedDelivery': (datetime.now() + timedelta(minutes=1145.27)).isoformat()
    }
    
    shipments_db[str(shipment_counter)] = sample_shipment
    shipment_counter += 1
    
    return jsonify({
        'success': True,
        'message': 'Sample data seeded',
        'shipment': sample_shipment
    })

# ==================== START SERVER ====================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 SwiftHaul Smart Logistics Backend")
    print("=" * 60)
    print("📍 Server running at: http://localhost:5000")
    print("📊 ML Model: Active and ready")
    print("🔗 CORS: Enabled for frontend integration")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)