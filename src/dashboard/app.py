import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import mysql.connector
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from src.utils.config_loader import ConfigLoader

class DashboardApp:
    def __init__(self):
        self.config = ConfigLoader().load_config()
        self.setup_page()
        self.initialize_connection()

    def setup_page(self):
        st.set_page_config(
            page_title="TransiLogi Dashboard",
            page_icon="🚚",
            layout="wide"
        )
        st.title("TransiLogi Delivery Dashboard")

    def initialize_connection(self):
        self.conn = mysql.connector.connect(
            host=self.config['DB_HOST'],
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            database=self.config['DB_NAME']
        )

    def run(self):
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Route Visualization", "Real-Time Metrics", "Order Management", "Analytics"]
        )

        if page == "Route Visualization":
            self.show_route_visualization()
        elif page == "Real-Time Metrics":
            self.show_real_time_metrics()
        elif page == "Order Management":
            self.show_order_management()
        else:
            self.show_analytics()

    def show_route_visualization(self):
        st.header("Route Visualization")
        
        # Get route data
        routes_df = self.get_route_data()
        
        # Create map
        m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
        
        # Add routes to map
        for vehicle_id in routes_df['vehicle_id'].unique():
            vehicle_routes = routes_df[routes_df['vehicle_id'] == vehicle_id]
            route_coords = vehicle_routes[['latitude', 'longitude']].values.tolist()
            
            # Create route line
            folium.PolyLine(
                route_coords,
                weight=2,
                color=self.get_random_color(),
                opacity=0.8
            ).add_to(m)
            
            # Add markers for each stop
            for idx, row in vehicle_routes.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=6,
                    popup=f"Stop {row['stop_number']}<br>Location: {row['location']}<br>Time: {row['planned_delivery_time']}",
                    color='red',
                    fill=True
                ).add_to(m)

        # Display map
        folium_static(m)

    def show_real_time_metrics(self):
        st.header("Real-Time Metrics")

        # Create columns for metrics
        col1, col2, col3 = st.columns(3)

        # Fetch metrics data
        metrics = self.get_metrics_data()

        with col1:
            st.metric(
                "Average Delivery Time",
                f"{metrics['avg_delivery_time']:.1f} min",
                f"{metrics['delivery_time_change']:.1f}%"
            )

        with col2:
            st.metric(
                "Vehicle Utilization",
                f"{metrics['vehicle_utilization']:.1f}%",
                f"{metrics['utilization_change']:.1f}%"
            )

        with col3:
            st.metric(
                "Cost Efficiency",
                f"${metrics['cost_efficiency']:.2f}/km",
                f"{metrics['efficiency_change']:.1f}%"
            )

        # Time series charts
        st.subheader("Delivery Performance Over Time")
        performance_df = self.get_performance_data()
        fig = px.line(
            performance_df,
            x='timestamp',
            y=['delivery_time', 'vehicle_utilization', 'cost_per_km'],
            title='Key Metrics Trends'
        )
        st.plotly_chart(fig)

    def show_order_management(self):
        st.header("New Order Management")

        # Create order form
        with st.form("new_order_form"):
            col1, col2 = st.columns(2)

            with col1:
                customer_location = st.text_input("Customer Location")
                delivery_priority = st.selectbox(
                    "Delivery Priority",
                    ["Standard", "Express", "Same Day"]
                )
                package_weight = st.number_input("Package Weight (kg)", min_value=0.1)

            with col2:
                latitude = st.number_input("Latitude", -90.0, 90.0)
                longitude = st.number_input("Longitude", -180.0, 180.0)
                desired_delivery_time = st.time_input("Desired Delivery Time")

            submitted = st.form_submit_button("Submit Order")

            if submitted:
                self.submit_new_order(
                    customer_location,
                    delivery_priority,
                    package_weight,
                    latitude,
                    longitude,
                    desired_delivery_time
                )
                st.success("Order submitted successfully!")

    def show_analytics(self):
        st.header("Operational Insights")

        # Time period selector
        time_period = st.selectbox(
            "Select Time Period",
            ["Last 24 Hours", "Last Week", "Last Month"]
        )

        # Create columns for different analyses
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Traffic Impact Analysis")
            traffic_data = self.get_traffic_data(time_period)
            fig_traffic = px.bar(
                traffic_data,
                x='traffic_condition',
                y='count',
                title='Delivery Distribution by Traffic Conditions'
            )
            st.plotly_chart(fig_traffic)

        with col2:
            st.subheader("Weather Impact Analysis")
            weather_data = self.get_weather_data(time_period)
            fig_weather = px.bar(
                weather_data,
                x='weather_condition',
                y='count',
                title='Delivery Distribution by Weather Conditions'
            )
            st.plotly_chart(fig_weather)

        # Delivery time trends
        st.subheader("Delivery Time Trends")
        time_trends = self.get_delivery_time_trends(time_period)
        fig_trends = px.line(
            time_trends,
            x='hour',
            y='average_delivery_time',
            title='Average Delivery Times by Hour'
        )
        st.plotly_chart(fig_trends)

    # Helper methods for data fetching
    def get_route_data(self):
        query = """
            SELECT *
            FROM optimized_routes
            WHERE DATE(created_at) = CURDATE()
            ORDER BY vehicle_id, stop_number
        """
        return pd.read_sql(query, self.conn)

    def get_metrics_data(self):
        # Simplified example - in production, calculate these from actual data
        return {
            'avg_delivery_time': 45.5,
            'delivery_time_change': -2.3,
            'vehicle_utilization': 78.5,
            'utilization_change': 1.5,
            'cost_efficiency': 2.34,
            'efficiency_change': -0.8
        }

    def get_performance_data(self):
        query = """
            SELECT 
                DATE(timestamp) as date,
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) as delivery_time,
                AVG(vehicle_utilization) as vehicle_utilization,
                AVG(distance_km) as cost_per_km
            FROM processed_data
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        """
        return pd.read_sql(query, self.conn)

    def get_traffic_data(self, time_period):
        query = """
            SELECT 
                traffic_condition,
                COUNT(*) as count
            FROM processed_data
            WHERE timestamp >= NOW() - INTERVAL 1 DAY
            GROUP BY traffic_condition
        """
        return pd.read_sql(query, self.conn)

    def get_weather_data(self, time_period):
        query = """
            SELECT 
                weather_condition,
                COUNT(*) as count
            FROM processed_data
            WHERE timestamp >= NOW() - INTERVAL 1 DAY
            GROUP BY weather_condition
        """
        return pd.read_sql(query, self.conn)

    def get_delivery_time_trends(self, time_period):
        query = """
            SELECT 
                HOUR(timestamp) as hour,
                AVG(TIMESTAMPDIFF(MINUTE, timestamp, actual_delivery_time)) as average_delivery_time
            FROM processed_data
            WHERE timestamp >= NOW() - INTERVAL 1 DAY
            GROUP BY HOUR(timestamp)
            ORDER BY hour
        """
        return pd.read_sql(query, self.conn)

    def submit_new_order(self, location, priority, weight, lat, lon, delivery_time):
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
            location,
            priority,
            weight,
            lat,
            lon,
            datetime.combine(datetime.now().date(), delivery_time)
        )
        cursor.execute(sql, values)
        self.conn.commit()
        cursor.close()

    @staticmethod
    def get_random_color():
        return '#{:06x}'.format(np.random.randint(0, 0xFFFFFF))

if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.run()