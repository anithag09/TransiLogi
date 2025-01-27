import os
import pandas as pd
import lightgbm as lgb
import pickle
import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from tensorflow import keras
from src.utils.config_loader import ConfigLoader

class PredictionModel:
    def __init__(self):
        self.config = ConfigLoader().load_config()
        
        # Create neural network model separately
        self.nn_model = self._create_neural_network()
        
        # Other models with configuration from config.yml
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=self.config['models']['random_forest']['n_estimators'],
                max_depth=self.config['models']['random_forest']['max_depth']
            ),
            'xgboost': XGBRegressor(
                n_estimators=self.config['models']['xgboost']['n_estimators'],
                learning_rate=self.config['models']['xgboost']['learning_rate']
            ),
            'lightgbm': lgb.LGBMRegressor(
                n_estimators=self.config['models']['lightgbm']['n_estimators'],
                num_leaves=self.config['models']['lightgbm']['num_leaves']
            ),
            'catboost': CatBoostRegressor(
                iterations=self.config['models']['catboost']['iterations'],
                depth=self.config['models']['catboost']['depth']
            ),
        }

    def _create_neural_network(self):
        # Use configuration from config.yml for neural network
        nn_config = self.config['models']['neural_network']
        
        model = keras.Sequential([
            keras.layers.Dense(nn_config['hidden_layers'][0], input_dim=6, activation='relu'),
            keras.layers.Dropout(nn_config['dropout_rate']),
            keras.layers.Dense(nn_config['hidden_layers'][1], activation='relu'),
            keras.layers.Dropout(nn_config['dropout_rate']),
            keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def train_and_save_model(self):
        # Load the processed data
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
        delivery_df = pd.read_csv(csv_path)

        # Convert datetime columns to timestamps
        delivery_df['actual_delivery_time'] = pd.to_datetime(delivery_df['actual_delivery_time']).astype(np.int64) // 10**9

        # Convert categorical variables to numeric
        delivery_df['delivery_priority'] = pd.Categorical(delivery_df['delivery_priority']).codes

        # Split the data into features and target
        X = delivery_df[['distance_km', 'delivery_priority', 'package_weight', 'traffic_impact', 'weather_impact', 'average_delivery_time']]
        y = delivery_df['actual_delivery_time']

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the models
        for name, model in self.models.items():
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            print(f"{name} R-squared: {score:.2f}")

        # Select the best model
        best_model = max(self.models.items(), key=lambda x: x[1].score(X_test, y_test))[1]

        # Save the best model
        model_path = os.path.join(os.path.dirname(__file__), 'best_delivery_time_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(best_model, f)