import os
import pandas as pd
from src.utils.config_loader import ConfigLoader
import mysql.connector

class DataEngineering:
    def __init__(self):
        self.config = ConfigLoader().load_config()

    def preprocess_data(self):
        # Extract raw data from the database
        raw_df = self.extract_raw_data()

        # Preprocess the data
        processed_df = self.preprocess_raw_data(raw_df)

        # Save the processed data back to the database
        self.save_processed_data(processed_df)

        # Save the processed data to a CSV file
        self.save_processed_data_to_csv(processed_df)

    def extract_raw_data(self):
        """
        Extract raw data from the MySQL database.
        """
        db = mysql.connector.connect(
            host=self.config['DB_HOST'],
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            database=self.config['DB_NAME']
        )
        cursor = db.cursor()

        cursor.execute("SELECT * FROM delivery_data")
        raw_data = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]
        raw_df = pd.DataFrame(raw_data, columns=column_names)

        db.close()
        return raw_df

    def preprocess_raw_data(self, raw_df):
        """
        Preprocess the raw data with improved datetime handling and feature engineering.
        """
        # Handle missing values
        raw_df.fillna(0, inplace=True)

        # Convert timestamp columns to datetime
        raw_df['timestamp'] = pd.to_datetime(raw_df['timestamp'])
        raw_df['actual_delivery_time'] = pd.to_datetime(raw_df['actual_delivery_time'])

        # Normalize geolocation data
        raw_df['latitude'] = raw_df['latitude'].apply(lambda x: x if -90 <= x <= 90 else None)
        raw_df['longitude'] = raw_df['longitude'].apply(lambda x: x if -180 <= x <= 180 else None)

        # Calculate average delivery time in seconds
        raw_df['average_delivery_time'] = raw_df.groupby('customer_location')['actual_delivery_time'].transform(
            lambda x: (x - pd.to_datetime(x.min())).dt.total_seconds().mean()
        )

        # Create impact features
        raw_df['traffic_impact'] = raw_df['traffic_condition'].map({
            'Light': 1.0,
            'Moderate': 1.2,
            'Heavy': 1.4
        }).fillna(1.0)

        raw_df['weather_impact'] = raw_df['weather_condition'].map({
            'Clear': 1.0,
            'Cloudy': 1.1,
            'Rain': 1.3,
            'Storm': 1.5
        }).fillna(1.0)

        # Calculate vehicle utilization
        raw_df['vehicle_utilization'] = (raw_df['package_weight'] / raw_df['vehicle_capacity']).clip(0, 1)

        return raw_df

    def save_processed_data(self, processed_df):
        """
        Save the processed data back into the MySQL database.
        """
        db = mysql.connector.connect(
            host=self.config['DB_HOST'],
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            database=self.config['DB_NAME']
        )
        cursor = db.cursor()

        # Drop the existing processed_data table if it exists
        cursor.execute("DROP TABLE IF EXISTS processed_data")

        # Create the processed_data table
        cursor.execute("""
            CREATE TABLE processed_data (
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
                vehicle_capacity INT,
                average_delivery_time FLOAT,
                traffic_impact FLOAT,
                weather_impact FLOAT,
                vehicle_utilization FLOAT
            )
        """)

        # Convert the timestamp and actual_delivery_time columns to the correct MySQL format
        processed_df['timestamp'] = processed_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        processed_df['actual_delivery_time'] = processed_df['actual_delivery_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Insert the processed data into the new table
        for _, row in processed_df.iterrows():
            sql = """
                INSERT INTO processed_data (
                    order_id, timestamp, customer_location, delivery_priority, package_weight,
                    vehicle_id, actual_delivery_time, weather_condition, traffic_condition,
                    latitude, longitude, distance_km, vehicle_capacity,
                    average_delivery_time, traffic_impact, weather_impact, vehicle_utilization
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                row['order_id'], row['timestamp'], row['customer_location'], row['delivery_priority'], row['package_weight'],
                row['vehicle_id'], row['actual_delivery_time'], row['weather_condition'], row['traffic_condition'],
                row['latitude'], row['longitude'], row['distance_km'], row['vehicle_capacity'],
                row['average_delivery_time'], row['traffic_impact'], row['weather_impact'], row['vehicle_utilization']
            )
            cursor.execute(sql, values)

        db.commit()
        db.close()
        
    def save_processed_data_to_csv(self, processed_df):
        """
        Save the processed data to a CSV file.
        """
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
        processed_df.to_csv(csv_path, index=False)