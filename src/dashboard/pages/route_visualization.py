import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
from ..components.maps import create_route_map
from ..utils.data_loader import get_route_data

def render_route_page():
    st.header("Route Visualization")
    
    # Date filter
    selected_date = st.date_input("Select Date", pd.Timestamp.now().date())
    
    # Vehicle filter
    route_data = get_route_data(selected_date)
    vehicles = route_data['vehicle_id'].unique()
    selected_vehicles = st.multiselect(
        "Select Vehicles",
        vehicles,
        default=vehicles
    )
    
    # Filter data based on selection
    filtered_routes = route_data[route_data['vehicle_id'].isin(selected_vehicles)]
    
    # Create and display map
    route_map = create_route_map(filtered_routes)
    folium_static(route_map)
    
    # Route details
    st.subheader("Route Details")
    for vehicle in selected_vehicles:
        vehicle_data = filtered_routes[filtered_routes['vehicle_id'] == vehicle]
        with st.expander(f"Vehicle {vehicle}"):
            st.dataframe(
                vehicle_data[['stop_number', 'location', 'planned_delivery_time']]
            )