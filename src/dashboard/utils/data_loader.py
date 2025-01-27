import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np
from src.utils.config_loader import ConfigLoader

class DataLoader:
    def __init__(self):
        self.config = ConfigLoader().load_config()
        self.initialize_connection()

    def initialize_connection(self):
        """Initialize database connection"""
        self.conn = mysql.connector.connect(
            host=self.config['DB_HOST'],
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            database=self.config['DB_NAME']
        )

    def get_route_data(self, selected_date):
        """Get route data for a specific date"""
        query = """
            SELECT *
            FROM optimized_routes
            WHERE DATE(created_at) = %s
            ORDER BY vehicle_id, stop_number
        """
        return pd.read_sql(query, self.conn, params=[selected_date])

    def get_metrics_data(self, time_range):
        """Get metrics data for the specified time range"""
        if time_range == "Last 24 Hours":
            time_filter = "timestamp >= NOW() - INTERVAL 1 DAY"
        elif time_range == "Last Week":
            time_filter = "timestamp >= NOW() - INTERVAL 7 DAY"
        else:  # Last Month
            time_filter = "timestamp >= NOW() - INTERVAL 30 DAY"

        query = f"""
            SELECT 
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) as avg_delivery_time,
                AVG(vehicle_utilization) as vehicle_utilization,
                SUM(distance_km) / COUNT(*) as cost_efficiency,
                
                -- Calculate changes
                (AVG(CASE WHEN timestamp >= NOW() - INTERVAL 12 HOUR 
                    THEN TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time) END) -
                 AVG(CASE WHEN timestamp < NOW() - INTERVAL 12 HOUR 
                    THEN TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time) END)) /
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) * 100 as delivery_time_change,
                
                (AVG(CASE WHEN timestamp >= NOW() - INTERVAL 12 HOUR 
                    THEN vehicle_utilization END) -
                 AVG(CASE WHEN timestamp < NOW() - INTERVAL 12 HOUR 
                    THEN vehicle_utilization END)) /
                AVG(vehicle_utilization) * 100 as utilization_change,
                
                (AVG(CASE WHEN timestamp >= NOW() - INTERVAL 12 HOUR 
                    THEN distance_km END) -
                 AVG(CASE WHEN timestamp < NOW() - INTERVAL 12 HOUR 
                    THEN distance_km END)) /
                AVG(distance_km) * 100 as efficiency_change
                
            FROM processed_data
            WHERE {time_filter}
        """
        return pd.read_sql(query, self.conn).iloc[0].to_dict()

    def get_performance_data(self, time_range):
        """Get performance data over time"""
        if time_range == "Last 24 Hours":
            interval = "HOUR"
            time_filter = "timestamp >= NOW() - INTERVAL 1 DAY"
        elif time_range == "Last Week":
            interval = "DAY"
            time_filter = "timestamp >= NOW() - INTERVAL 7 DAY"
        else:  # Last Month
            interval = "DAY"
            time_filter = "timestamp >= NOW() - INTERVAL 30 DAY"

        query = f"""
            SELECT 
                DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as timestamp,
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) as delivery_time,
                AVG(vehicle_utilization) as vehicle_utilization,
                SUM(distance_km) / COUNT(*) as cost_per_km
            FROM processed_data
            WHERE {time_filter}
            GROUP BY DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00')
            ORDER BY timestamp
        """
        return pd.read_sql(query, self.conn)

    def get_analytics_data(self, time_period):
        """Get analytics data for visualizations"""
        if time_period == "Last 24 Hours":
            time_filter = "timestamp >= NOW() - INTERVAL 1 DAY"
        elif time_period == "Last Week":
            time_filter = "timestamp >= NOW() - INTERVAL 7 DAY"
        else:  # Last Month
            time_filter = "timestamp >= NOW() - INTERVAL 30 DAY"

        # Traffic analysis
        traffic_query = f"""
            SELECT 
                traffic_condition,
                COUNT(*) as count,
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) as avg_delivery_time
            FROM processed_data
            WHERE {time_filter}
            GROUP BY traffic_condition
        """
        traffic_data = pd.read_sql(traffic_query, self.conn)

        # Weather impact analysis
        weather_query = f"""
            SELECT 
                weather_condition,
                HOUR(timestamp) as hour,
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) as avg_delivery_time
            FROM processed_data
            WHERE {time_filter}
            GROUP BY weather_condition, HOUR(timestamp)
        """
        weather_data = pd.read_sql(weather_query, self.conn)
        weather_pivot = weather_data.pivot(
            index='weather_condition',
            columns='hour',
            values='avg_delivery_time'
        )

        # Time patterns
        patterns_query = f"""
            SELECT 
                HOUR(timestamp) as hour,
                COUNT(*) as count,
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) as avg_delivery_time
            FROM processed_data
            WHERE {time_filter}
            GROUP BY HOUR(timestamp)
            ORDER BY hour
        """
        time_patterns = pd.read_sql(patterns_query, self.conn)

        return {
            'traffic': traffic_data,
            'weather_impact': weather_pivot,
            'time_patterns': time_patterns
        }

    def submit_order(self, order_data):
        """Submit a new order to the database"""
        try:
            cursor = self.conn.cursor()
            sql = """
                INSERT INTO delivery_data (
                    order_id, timestamp, customer_location, delivery_priority,
                    package_weight, latitude, longitude, actual_delivery_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            values = (
                order_id,
                datetime.now(),
                order_data['customer_location'],
                order_data['delivery_priority'],
                order_data['package_weight'],
                order_data['latitude'],
                order_data['longitude'],
                datetime.combine(datetime.now().date(), order_data['desired_delivery_time'])
            )
            cursor.execute(sql, values)
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error submitting order: {e}")
            return False

    def get_order_history(self, status_filter=None, date_range=None):
        """Get order history with optional filters"""
        query = """
            SELECT 
                order_id,
                timestamp,
                customer_location,
                delivery_priority,
                package_weight,
                actual_delivery_time,
                CASE 
                    WHEN actual_delivery_time IS NULL THEN 'Pending'
                    WHEN actual_delivery_time > timestamp THEN 'Delivered'
                    ELSE 'In Progress'
                END as status
            FROM delivery_data
            WHERE 1=1
        """
        params = []

        if status_filter:
            query += " AND status IN (%s)" % ','.join(['%s'] * len(status_filter))
            params.extend(status_filter)

        if date_range:
            query += " AND DATE(timestamp) BETWEEN %s AND %s"
            params.extend(date_range)

        query += " ORDER BY timestamp DESC"
        return pd.read_sql(query, self.conn, params=params)

    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'conn') and self.conn.is_connected():
            self.conn.close()