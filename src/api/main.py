from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import pickle
import mysql.connector
from typing import List, Optional
import os
from src.utils.config_loader import ConfigLoader
from src.models.prediction import PredictionModel
from src.models.route_optimization import RouteOptimization

app = FastAPI(title="TransLogi API", version="1.0.0")
config = ConfigLoader().load_config()

# Initialize models
prediction_model = PredictionModel()
route_optimizer = RouteOptimization()

class DeliveryOrder(BaseModel):
    customer_location: str
    delivery_priority: str
    package_weight: float
    latitude: float
    longitude: float
    weather_condition: str
    traffic_condition: str

class DeliveryPrediction(BaseModel):
    order_id: str
    predicted_delivery_time: str
    confidence_score: float

class RouteStop(BaseModel):
    order_id: str
    location: str
    latitude: float
    longitude: float
    planned_delivery_time: str

class Route(BaseModel):
    route_id: str
    vehicle_id: str
    stops: List[RouteStop]

@app.post("/api/v1/predict-delivery", response_model=DeliveryPrediction)
async def predict_delivery(order: DeliveryOrder):
    try:
        # Prepare features for prediction
        features = pd.DataFrame({
            'distance_km': [prediction_model.calculate_distance(order.latitude, order.longitude)],
            'delivery_priority': [prediction_model.encode_priority(order.delivery_priority)],
            'package_weight': [order.package_weight],
            'traffic_impact': [order.traffic_condition],
            'weather_impact': [order.weather_condition],
            'average_delivery_time': [prediction_model.get_average_delivery_time(order.customer_location)]
        })

        predicted_time = prediction_model.predict(features)
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return DeliveryPrediction(
            order_id=order_id,
            predicted_delivery_time=str(predicted_time),
            confidence_score=0.95
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/routes/{date}", response_model=List[Route])
async def get_routes(date: str):
    try:
        routes = route_optimizer.get_routes_by_date(date)
        return routes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
