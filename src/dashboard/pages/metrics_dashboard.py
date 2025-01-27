import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from ..components.charts import create_metric_card, create_time_series_chart
from ..utils.data_loader import get_metrics_data, get_performance_data

def render_metrics_page():
    st.header("Real-Time Metrics Dashboard")
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        ["Last 24 Hours", "Last Week", "Last Month"]
    )
    
    # Get metrics data
    metrics_data = get_metrics_data(time_range)
    performance_data = get_performance_data(time_range)
    
    # Display metric cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_metric_card(
            "Average Delivery Time",
            f"{metrics_data['avg_delivery_time']:.1f} min",
            metrics_data['delivery_time_change']
        )
    
    with col2:
        create_metric_card(
            "Vehicle Utilization",
            f"{metrics_data['vehicle_utilization']:.1f}%",
            metrics_data['utilization_change']
        )
    
    with col3:
        create_metric_card(
            "Cost Efficiency",
            f"${metrics_data['cost_efficiency']:.2f}/km",
            metrics_data['efficiency_change']
        )
    
    # Display performance charts
    st.subheader("Performance Trends")
    
    tab1, tab2 = st.tabs(["Delivery Times", "Vehicle Utilization"])
    
    with tab1:
        delivery_chart = create_time_series_chart(
            performance_data,
            'timestamp',
            'delivery_time',
            'Average Delivery Time'
        )
        st.plotly_chart(delivery_chart)
    
    with tab2:
        utilization_chart = create_time_series_chart(
            performance_data,
            'timestamp',
            'vehicle_utilization',
            'Vehicle Utilization'
        )
        st.plotly_chart(utilization_chart)