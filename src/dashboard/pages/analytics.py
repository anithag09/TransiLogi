import streamlit as st
import plotly.express as px
from ..components.charts import create_bar_chart, create_heatmap
from ..utils.data_loader import get_analytics_data

def render_analytics_page():
    st.header("Operational Insights")
    
    # Time period selector
    time_period = st.selectbox(
        "Select Time Period",
        ["Last 24 Hours", "Last Week", "Last Month"]
    )
    
    # Get analytics data
    analytics_data = get_analytics_data(time_period)
    
    # Traffic Impact Analysis
    st.subheader("Traffic Impact Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        traffic_fig = create_bar_chart(
            analytics_data['traffic'],
            'traffic_condition',
            'count',
            'Deliveries by Traffic Condition'
        )
        st.plotly_chart(traffic_fig)
    
    with col2:
        traffic_time_fig = create_bar_chart(
            analytics_data['traffic_time'],
            'traffic_condition',
            'avg_delivery_time',
            'Average Delivery Time by Traffic'
        )
        st.plotly_chart(traffic_time_fig)
    
    # Weather Impact Analysis
    st.subheader("Weather Impact Analysis")
    weather_impact = create_heatmap(
        analytics_data['weather_impact'],
        'Weather Impact on Delivery Times'
    )
    st.plotly_chart(weather_impact)
    
    # Delivery Time Patterns
    st.subheader("Delivery Time Patterns")
    patterns_fig = create_bar_chart(
        analytics_data['time_patterns'],
        'hour',
        'count',
        'Delivery Distribution by Hour'
    )
    st.plotly_chart(patterns_fig)