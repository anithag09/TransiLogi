import os
import pandas as pd
import mysql.connector
from src.utils.config_loader import ConfigLoader

class DBLoader:
    def __init__(self):
        self.config = ConfigLoader().load_config()
    
    def load_delivery_data(self):
        # Connect to MySQL database
        db = mysql.connector.connect(
            host=self.config['DB_HOST'],
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            database=self.config['DB_NAME']
        )
        cursor = db.cursor()

        # Create the delivery_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delivery_data (
                order_id VARCHAR(50),
                timestamp DATETIME,
                customer_location VARCHAR(50),
                delivery_priority VARCHAR(50),
                package_weight FLOAT,
                vehicle_id VARCHAR(50),
                actual_delivery_time DATETIME,
                weather_condition VARCHAR(50),
                traffic_condition VARCHAR(50),
                latitude FLOAT,
                longitude FLOAT,
                distance_km FLOAT,
                vehicle_capacity INT
            )
        """)

        # Load data from CSV and insert into the database
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'delivery_data.csv')
        delivery_df = pd.read_csv(csv_path)
        for _, row in delivery_df.iterrows():
            sql = """
                INSERT INTO delivery_data (
                    order_id, timestamp, customer_location, delivery_priority, package_weight,
                    vehicle_id, actual_delivery_time, weather_condition, traffic_condition,
                    latitude, longitude, distance_km, vehicle_capacity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                row['order_id'], row['timestamp'], row['customer_location'], row['delivery_priority'], row['package_weight'],
                row['vehicle_id'], row['actual_delivery_time'], row['weather_condition'], row['traffic_condition'],
                row['latitude'], row['longitude'], row['distance_km'], row['vehicle_capacity']
            )
            cursor.execute(sql, values)

        db.commit()
        db.close()