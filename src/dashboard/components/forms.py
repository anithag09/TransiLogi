import streamlit as st
from datetime import datetime, timedelta

class OrderForm:
    def __init__(self):
        self.form_data = {}
    
    def render(self):
        """Render the order form and return True if submitted"""
        with st.form("new_order_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                self.form_data['customer_location'] = st.text_input(
                    "Customer Location",
                    help="Enter the delivery address"
                )
                
                self.form_data['delivery_priority'] = st.selectbox(
                    "Delivery Priority",
                    ["Standard", "Express", "Same Day"]
                )
                
                self.form_data['package_weight'] = st.number_input(
                    "Package Weight (kg)",
                    min_value=0.1,
                    help="Enter the package weight in kilograms"
                )
            
            with col2:
                self.form_data['latitude'] = st.number_input(
                    "Latitude",
                    min_value=-90.0,
                    max_value=90.0,
                    help="Enter the delivery location latitude"
                )
                
                self.form_data['longitude'] = st.number_input(
                    "Longitude",
                    min_value=-180.0,
                    max_value=180.0,
                    help="Enter the delivery location longitude"
                )
                
                self.form_data['desired_delivery_time'] = st.time_input(
                    "Desired Delivery Time",
                    help="Select the preferred delivery time"
                )
            
            submitted = st.form_submit_button("Submit Order")
            
            if submitted:
                if self._validate_form():
                    return True
            
            return False
    
    def _validate_form(self):
        """Validate form inputs"""
        if not self.form_data['customer_location']:
            st.error("Customer location is required")
            return False
        
        if self.form_data['package_weight'] <= 0:
            st.error("Package weight must be greater than 0")
            return False
        
        # Validate delivery time is in the future
        current_time = datetime.now().time()
        if self.form_data['desired_delivery_time'] <= current_time:
            st.error("Delivery time must be in the future")
            return False
        
        return True
    
    def get_data(self):
        """Return the form data"""
        return self.form_data