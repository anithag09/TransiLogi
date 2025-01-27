import folium
import numpy as np
from folium import plugins

def create_route_map(route_data):
    """Create a Folium map with delivery routes"""
    # Initialize map centered on mean coordinates
    center_lat = route_data['latitude'].mean()
    center_lon = route_data['longitude'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Add routes for each vehicle
    for vehicle_id in route_data['vehicle_id'].unique():
        vehicle_routes = route_data[route_data['vehicle_id'] == vehicle_id]
        route_coords = vehicle_routes[['latitude', 'longitude']].values.tolist()
        
        # Generate random color for this route
        route_color = '#{:06x}'.format(np.random.randint(0, 0xFFFFFF))
        
        # Add route line
        folium.PolyLine(
            route_coords,
            weight=2,
            color=route_color,
            opacity=0.8
        ).add_to(m)
        
        # Add markers for each stop
        for idx, row in vehicle_routes.iterrows():
            popup_html = f"""
                <div style='width: 200px'>
                    <b>Stop {row['stop_number']}</b><br>
                    Location: {row['location']}<br>
                    Time: {row['planned_delivery_time']}<br>
                    Order ID: {row['order_id']}
                </div>
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                popup=folium.Popup(popup_html, max_width=300),
                color=route_color,
                fill=True
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def create_density_map(location_data):
    """Create a heatmap of delivery locations"""
    center_lat = location_data['latitude'].mean()
    center_lon = location_data['longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
    
    # Add heatmap layer
    heat_data = location_data[['latitude', 'longitude', 'weight']].values.tolist()
    plugins.HeatMap(heat_data).add_to(m)
    
    return m