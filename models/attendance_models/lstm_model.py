import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
from datetime import datetime

class AttendanceLSTM:
    def __init__(self, models_path='models/attendance_models/trained_models/'):
        self.models_path = models_path
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = 30
        self.is_trained = False
        os.makedirs(models_path, exist_ok=True)
    
    def create_sequences(self, data):
        """Create sequences for LSTM training"""
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:(i + self.sequence_length)])
            y.append(data[i + self.sequence_length])
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape):
        """Build LSTM model architecture"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1, activation='sigmoid')  # Sigmoid for probability output
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def train(self, df):
        """Train the LSTM model"""
        try:
            if len(df) < self.sequence_length + 10:
                print("Insufficient data for LSTM training")
                return False
            
            # Prepare data
            data = df['attendance'].values.reshape(-1, 1)
            scaled_data = self.scaler.fit_transform(data)
            
            # Create sequences
            X, y = self.create_sequences(scaled_data)
            
            # Reshape for LSTM
            X = X.reshape((X.shape[0], X.shape[1], 1))
            
            # Build and train model
            self.model = self.build_model((X.shape[1], X.shape[2]))
            
            history = self.model.fit(
                X, y, 
                epochs=50, 
                batch_size=32, 
                validation_split=0.2,
                verbose=0
            )
            
            # Save model and scaler
            self.model.save(os.path.join(self.models_path, 'lstm_model.h5'))
            joblib.dump({
                'scaler': self.scaler,
                'sequence_length': self.sequence_length,
                'trained_at': datetime.now(),
                'final_loss': history.history['loss'][-1]
            }, os.path.join(self.models_path, 'lstm_scaler.pkl'))
            
            self.is_trained = True
            print(f"LSTM model trained - Final loss: {history.history['loss'][-1]:.4f}")
            return True
            
        except Exception as e:
            print(f"Error training LSTM model: {e}")
            return False
    
    def predict(self, df):
        """Predict next day's attendance using LSTM"""
        if not self.is_trained:
            self.load_model()
        
        if self.model is None:
            return 0.75  # Default fallback
        
        try:
            # Get recent sequence
            recent_data = df['attendance'].tail(self.sequence_length).values
            
            if len(recent_data) < self.sequence_length:
                # Pad with mean if insufficient data
                padding = np.full(self.sequence_length - len(recent_data), np.mean(recent_data))
                recent_data = np.concatenate([padding, recent_data])
            
            # Scale the data
            scaled_data = self.scaler.transform(recent_data.reshape(-1, 1))
            
            # Reshape for prediction
            X_pred = scaled_data.reshape(1, self.sequence_length, 1)
            
            # Make prediction
            scaled_prediction = self.model.predict(X_pred, verbose=0)[0][0]
            
            # Inverse transform to get actual probability
            prediction = self.scaler.inverse_transform([[scaled_prediction]])[0][0]
            
            # Ensure within bounds
            probability = max(0, min(1, prediction))
            
            return probability
            
        except Exception as e:
            print(f"Error in LSTM prediction: {e}")
            return 0.75
    
    def load_model(self):
        """Load trained model and scaler"""
        model_path = os.path.join(self.models_path, 'lstm_model.h5')
        scaler_path = os.path.join(self.models_path, 'lstm_scaler.pkl')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.model = tf.keras.models.load_model(model_path)
            scaler_data = joblib.load(scaler_path)
            self.scaler = scaler_data['scaler']
            self.sequence_length = scaler_data['sequence_length']
            self.is_trained = True