import streamlit as st
from ..components.forms import OrderForm
from ..utils.data_loader import submit_order, get_order_history

def render_order_page():
    st.header("Order Management")
    
    # Tabs for new order and order history
    tab1, tab2 = st.tabs(["New Order", "Order History"])
    
    with tab1:
        order_form = OrderForm()
        if order_form.render():
            # Form was submitted
            order_data = order_form.get_data()
            success = submit_order(order_data)
            if success:
                st.success("Order submitted successfully!")
            else:
                st.error("Error submitting order. Please try again.")
    
    with tab2:
        # Order history view
        st.subheader("Recent Orders")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Status",
                ["Pending", "In Progress", "Delivered", "Cancelled"]
            )
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=[pd.Timestamp.now().date() - pd.Timedelta(days=7), 
                       pd.Timestamp.now().date()]
            )
        
        # Get and display order history
        orders = get_order_history(status_filter, date_range)
        st.dataframe(orders)