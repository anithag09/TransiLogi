import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def create_metric_card(title, value, change):
    """Create a metric card with title, value, and change indicator"""
    delta_color = "green" if change >= 0 else "red"
    st.metric(
        title,
        value,
        f"{change:+.1f}%",
        delta_color=delta_color
    )

def create_time_series_chart(data, x_col, y_col, title):
    """Create a time series chart with trend line"""
    fig = px.line(
        data,
        x=x_col,
        y=y_col,
        title=title
    )
    
    # Add trend line
    z = np.polyfit(range(len(data)), data[y_col], 1)
    p = np.poly1d(z)
    
    fig.add_trace(
        go.Scatter(
            x=data[x_col],
            y=p(range(len(data))),
            name="Trend",
            line=dict(dash='dash')
        )
    )
    
    return fig

def create_bar_chart(data, x_col, y_col, title):
    """Create a bar chart with average line"""
    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        title=title
    )
    
    # Add average line
    avg = data[y_col].mean()
    fig.add_hline(
        y=avg,
        line_dash="dash",
        annotation_text=f"Average: {avg:.2f}"
    )
    
    return fig

def create_heatmap(data, title):
    """Create a heatmap visualization"""
    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale='RdYlBu_r'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time of Day",
        yaxis_title="Day of Week"
    )
    
    return fig