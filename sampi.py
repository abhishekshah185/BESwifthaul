from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

app = Flask(__name__) 

CORS(app)  # Enable CORS for frontend-backend communication

# Global variable to store the trained model
trained_model = None

def train_delivery_model():
    """
    Train a machine learning model to predict delivery time based on distance
    """
    try:
        # Try different dataset paths
        dataset_paths = [
            "Delhivery_Logistics_Cleaned.csv",
            "data/shipments.csv",
            "shipments.csv"
        ]
        
        df = None
        for dataset_path in dataset_paths:
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                print(f"✓ Loaded training data from {dataset_path}")
                break
        
        if df is None:
            print("⚠ No training data available, using dummy model")
            return create_dummy_model()
        
        # Filter rows with valid distance and time data
        distance_col = 'distance' if 'distance' in df.columns else 'Distance_Km'
        time_col = 'estimated_time' if 'estimated_time' in df.columns else 'Time_Taken_Hrs'
        
        if distance_col not in df.columns or time_col not in df.columns:
            print(f"⚠ Required columns not found. Available: {df.columns.tolist()}")
            return create_dummy_model()
        
        df = df.dropna(subset=[distance_col, time_col])
        
        if len(df) >= 5:  # Only train if we have enough data
            # Prepare features and target
            X = df[[distance_col]]
            y = df[time_col]
            
            # If time is in hours and we want minutes, convert
            if time_col == 'Time_Taken_Hrs':
                y = y * 60  # Convert hours to minutes
            
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                model = GradientBoostingRegressor(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                # Calculate training score
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)
                print(f"✓ Model trained successfully!")
                print(f"  Training Score: {train_score:.4f}")
                print(f"  Test Score: {test_score:.4f}")
                
                return model
            except Exception as e:
                print(f"✗ Error during model training: {e}")
                return create_dummy_model()
        else:
            print(f"⚠ Not enough data (only {len(df)} rows), using dummy model")
            return create_dummy_model()
    except Exception as e:
        print(f"✗ Overall error in train_delivery_model: {e}")
        return create_dummy_model()

def create_dummy_model():
    """
    Create a simple dummy model when not enough data is available
    This model assumes 1 km takes about 2 minutes on average
    """
    class DummyModel:
        def predict(self, X):
            # Simple formula: ~2 min per km
            if isinstance(X, pd.DataFrame):
                return X.iloc[:, 0] * 2 + np.random.normal(0, 5, size=len(X))
            else:
                return np.array(X) * 2 + np.random.normal(0, 5, size=len(X))
    
    print("ℹ Using dummy model (2 min/km baseline)")
    return DummyModel()

def predict_delivery_time(model, distance):
    """
    Predict delivery time based on distance using the trained model
    """
    try:
        input_data = pd.DataFrame([[distance]], columns=['distance'])
        prediction = model.predict(input_data)[0]
        return round(prediction, 2)
    except Exception as e:
        print(f"Prediction error: {e}")
        # Fallback to a simple heuristic if prediction fails
        return round(distance * 2, 2)  # ~2 min per km

# Initialize model when app starts
print("=" * 50)
print("Initializing Delivery Time Predictor...")
print("=" * 50)
trained_model = train_delivery_model()
print("=" * 50)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Delivery Time Predictor</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 min-h-screen">
        <div class="container mx-auto p-6 max-w-4xl">
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-gray-800 mb-2">🚚 Delivery Time Predictor</h1>
                <p class="text-gray-600">AI-powered delivery time estimation using Gradient Boosting</p>
            </div>
            
            <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
                <div class="mb-6">
                    <label class="block text-sm font-semibold text-gray-700 mb-2">
                        Enter Distance (km)
                    </label>
                    <input 
                        type="number" 
                        id="distance" 
                        placeholder="e.g., 50"
                        class="w-full px-4 py-3 text-lg border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none"
                        step="0.1"
                        min="0"
                    >
                </div>
                
                <button 
                    onclick="predictTime()"
                    class="w-full py-4 rounded-lg font-semibold text-white text-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 transition-all"
                >
                    Predict Delivery Time
                </button>
                
                <div id="result" class="mt-6 hidden"></div>
            </div>
            
            <div id="history" class="bg-white rounded-2xl shadow-lg p-6 hidden">
                <h2 class="text-xl font-bold text-gray-800 mb-4">Recent Predictions</h2>
                <div id="historyList"></div>
            </div>
        </div>
        
        <script>
            let history = [];
            
            async function predictTime() {
                const distance = document.getElementById('distance').value;
                
                if (!distance || distance <= 0) {
                    alert('Please enter a valid distance greater than 0');
                    return;
                }
                
                try {
                    const response = await fetch('/predict', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({distance: parseFloat(distance)})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        displayResult(data.predicted_time, distance);
                        addToHistory(distance, data.predicted_time);
                    } else {
                        alert('Error: ' + data.error);
                    }
                } catch (error) {
                    alert('Failed to connect to server');
                }
            }
            
            function displayResult(time, distance) {
                const resultDiv = document.getElementById('result');
                const speed = (parseFloat(distance) / (time / 60)).toFixed(2);
                
                resultDiv.innerHTML = `
                    <div class="p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-200">
                        <div class="flex items-center justify-between mb-4">
                            <div>
                                <p class="text-sm text-gray-600 font-medium">Estimated Delivery Time</p>
                                <p class="text-3xl font-bold text-gray-800">
                                    ${time} <span class="text-xl text-gray-600">minutes</span>
                                </p>
                            </div>
                            <div class="text-right">
                                <p class="text-sm text-gray-600">Distance</p>
                                <p class="text-xl font-semibold text-gray-800">${distance} km</p>
                            </div>
                        </div>
                        <div class="pt-4 border-t border-green-200">
                            <p class="text-sm text-gray-600">
                                Average Speed: <span class="font-semibold text-gray-800">${speed} km/h</span>
                            </p>
                        </div>
                    </div>
                `;
                resultDiv.classList.remove('hidden');
            }
            
            function addToHistory(distance, time) {
                history.unshift({
                    distance: distance,
                    time: time,
                    timestamp: new Date().toLocaleTimeString()
                });
                history = history.slice(0, 5);
                
                const historyDiv = document.getElementById('history');
                const historyList = document.getElementById('historyList');
                
                historyList.innerHTML = history.map((entry, idx) => `
                    <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg mb-3 hover:bg-gray-100 transition-colors">
                        <div class="flex items-center">
                            <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center mr-3">
                                <span class="text-indigo-600 font-semibold text-sm">${idx + 1}</span>
                            </div>
                            <div>
                                <p class="font-semibold text-gray-800">${entry.distance} km</p>
                                <p class="text-xs text-gray-500">${entry.timestamp}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-indigo-600">${entry.time} min</p>
                        </div>
                    </div>
                `).join('');
                
                historyDiv.classList.remove('hidden');
            }
            
            // Allow Enter key to submit
            document.getElementById('distance').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') predictTime();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/predict', methods=['POST'])
def predict():
    """API endpoint for predictions"""
    try:
        data = request.get_json()
        distance = float(data.get('distance', 0))
        
        if distance <= 0:
            return jsonify({
                'success': False,
                'error': 'Distance must be greater than 0'
            })
        
        predicted_time = predict_delivery_time(trained_model, distance)
        
        return jsonify({
            'success': True,
            'predicted_time': predicted_time,
            'distance': distance
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/model-info', methods=['GET'])
def model_info():
    """Get information about the trained model"""
    model_type = "Gradient Boosting Regressor" if hasattr(trained_model, 'n_estimators') else "Dummy Model"
    return jsonify({
        'model_type': model_type,
        'status': 'active'

    })

if __name__ == '__main__':

    print("\n🚀 Starting Flask server...")
    print("📍 Access the app at: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=False, host='0.0.0.0', port=5000)