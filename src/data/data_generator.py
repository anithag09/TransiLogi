import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from geopy.distance import geodesic
import random

# Set random seed for reproducibility
np.random.seed(42)

def generate_delivery_data(num_records=1000):
    # Generate dates for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start_date, end_date, periods=num_records)
    
    # Sample customer locations (major cities)
    locations = {
        'New York': {'lat': 40.7128, 'lng': -74.0060},
        'Los Angeles': {'lat': 34.0522, 'lng': -118.2437},
        'Chicago': {'lat': 41.8781, 'lng': -87.6298},
        'Houston': {'lat': 29.7604, 'lng': -95.3698},
        'Phoenix': {'lat': 33.4484, 'lng': -112.0740}
    }
    
    # Generate delivery data
    data = {
        'order_id': [f'ORD-{i:06d}' for i in range(num_records)],
        'timestamp': dates,
        'customer_location': random.choices(list(locations.keys()), k=num_records),
        'delivery_priority': np.random.choice(['Standard', 'Express', 'Same-day'], num_records),
        'package_weight': np.random.uniform(1, 50, num_records).round(2),
        'vehicle_id': [f'VEH-{i:03d}' for i in np.random.randint(1, 21, num_records)],
        'actual_delivery_time': None,
        'weather_condition': np.random.choice(['Clear', 'Rain', 'Cloudy', 'Storm'], num_records),
        'traffic_condition': np.random.choice(['Light', 'Moderate', 'Heavy'], num_records)
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Add latitude and longitude based on customer location
    df['latitude'] = df['customer_location'].map(lambda x: locations[x]['lat'] + np.random.uniform(-0.1, 0.1))
    df['longitude'] = df['customer_location'].map(lambda x: locations[x]['lng'] + np.random.uniform(-0.1, 0.1))
    
    # Add distance from central depot
    depot_location = (39.8283, -98.5795)  # Near the geographic center of the US
    df['distance_km'] = df.apply(
        lambda row: geodesic(depot_location, (row['latitude'], row['longitude'])).kilometers, axis=1
    )
    
    # Add vehicle capacity
    vehicle_capacities = {f'VEH-{i:03d}': np.random.randint(50, 200) for i in range(1, 21)}
    df['vehicle_capacity'] = df['vehicle_id'].map(vehicle_capacities)
    
    # Add delivery windows
    df['delivery_start_time'] = df['timestamp'] + pd.to_timedelta(np.random.randint(2, 8, size=num_records), unit='h')
    df['delivery_end_time'] = df['delivery_start_time'] + pd.to_timedelta(4, unit='h')  # 4-hour window
    
    # Generate actual delivery times (adding random delays based on conditions)
    base_delivery_times = {
        'Standard': timedelta(hours=24),
        'Express': timedelta(hours=12),
        'Same-day': timedelta(hours=6)
    }
    
    weather_delays = {
        'Clear': 1,
        'Cloudy': 1.1,
        'Rain': 1.3,
        'Storm': 1.5
    }
    
    traffic_delays = {
        'Light': 1,
        'Moderate': 1.2,
        'Heavy': 1.4
    }
    
    for idx, row in df.iterrows():
        base_time = base_delivery_times[row['delivery_priority']]
        weather_factor = weather_delays[row['weather_condition']]
        traffic_factor = traffic_delays[row['traffic_condition']]
        
        # Calculate actual delivery time with delays
        delay = base_time * weather_factor * traffic_factor
        df.at[idx, 'actual_delivery_time'] = (row['timestamp'] + delay).to_pydatetime()
    
    return df

# Generate data
delivery_df = generate_delivery_data()

# Save to CSV
delivery_df.to_csv('./src/data/delivery_data.csv', index=False)

# Display first few rows
print(delivery_df.head())

# Display basic statistics
print("\nDataset Statistics:")
print(delivery_df.describe())
