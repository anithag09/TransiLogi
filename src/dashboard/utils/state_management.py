import streamlit as st
from datetime import datetime, timedelta

class SessionState:
    """Manage session state for the dashboard"""
    
    @staticmethod
    def init_session_state():
        """Initialize session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.selected_date = datetime.now().date()
            st.session_state.time_range = "Last 24 Hours"
            st.session_state.selected_vehicles = []
            st.session_state.status_filter = ["Pending", "In Progress", "Delivered"]
            st.session_state.refresh_data = True
            st.session_state.last_update = datetime.now()
            st.session_state.selected_view = "map"  # or "table"
            st.session_state.show_historical = False
            st.session_state.metric_preferences = {
                'show_delivery_time': True,
                'show_utilization': True,
                'show_efficiency': True
            }

    @staticmethod
    def get_state(key, default=None):
        """Get a value from session state"""
        return st.session_state.get(key, default)

    @staticmethod
    def set_state(key, value):
        """Set a value in session state"""
        st.session_state[key] = value

    @staticmethod
    def clear_state(key):
        """Clear a value from session state"""
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def should_refresh_data():
        """Check if data should be refreshed based on last update time"""
        if st.session_state.refresh_data:
            current_time = datetime.now()
            time_diff = current_time - st.session_state.last_update
            
            # Refresh every 5 minutes
            if time_diff.total_seconds() >= 300:
                st.session_state.last_update = current_time
                return True
        return False

    @staticmethod
    def toggle_metric_visibility(metric_name):
        """Toggle visibility of a metric"""
        current_value = st.session_state.metric_preferences.get(f'show_{metric_name}', True)
        st.session_state.metric_preferences[f'show_{metric_name}'] = not current_value

    @staticmethod
    def save_filter_preferences():
        """Save current filter preferences"""
        st.session_state.saved_filters = {
            'time_range': st.session_state.time_range,
            'status_filter': st.session_state.status_filter,
            'selected_vehicles': st.session_state.selected_vehicles
        }

    @staticmethod
    def load_filter_preferences():
        """Load saved filter preferences"""
        if 'saved_filters' in st.session_state:
            filters = st.session_state.saved_filters
            st.session_state.time_range = filters['time_range']
            st.session_state.status_filter = filters['status_filter']
            st.session_state.selected_vehicles = filters['selected_vehicles']

    @staticmethod
    def reset_filters():
        """Reset all filters to default values"""
        st.session_state.time_range = "Last 24 Hours"
        st.session_state.status_filter = ["Pending", "In Progress", "Delivered"]
        st.session_state.selected_vehicles = []
        st.session_state.selected_view = "map"
        st.session_state.show_historical = False

class DashboardState:
    """Manage dashboard-wide state and configurations"""

    def __init__(self):
        self.session = SessionState()
        self.session.init_session_state()

    def check_authentication(self):
        """Check if user is authenticated"""
        return 'authenticated' in st.session_state and st.session_state.authenticated

    def require_authentication(self):
        """Require authentication to view the dashboard"""
        if not self.check_authentication():
            st.warning("Please log in to access the dashboard")
            return False
        return True

    def handle_page_navigation(self):
        """Handle navigation between dashboard pages"""
        pages = {
            "Route Visualization": "route_viz",
            "Real-Time Metrics": "metrics",
            "Order Management": "orders",
            "Analytics": "analytics"
        }
        
        selected_page = st.sidebar.selectbox("Navigation", list(pages.keys()))
        
        # Update session state
        st.session_state.current_page = pages[selected_page]
        
        # Reset page-specific states when navigating
        if st.session_state.get('last_page') != st.session_state.current_page:
            self.reset_page_state()
            st.session_state.last_page = st.session_state.current_page

    def reset_page_state(self):
        """Reset page-specific session state variables"""
        page_specific_keys = [
            'selected_vehicles',
            'show_historical',
            'metric_preferences'
        ]
        
        for key in page_specific_keys:
            if key in st.session_state:
                del st.session_state[key]

    def get_refresh_interval(self):
        """Get refresh interval based on current page"""
        refresh_intervals = {
            'route_viz': 300,  # 5 minutes
            'metrics': 60,     # 1 minute
            'orders': 120,     # 2 minutes
            'analytics': 3600  # 1 hour
        }
        return refresh_intervals.get(st.session_state.current_page, 300)

    def manage_auto_refresh(self):
        """Manage automatic data refresh"""
        current_time = datetime.now()
        refresh_interval = self.get_refresh_interval()
        
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = current_time
            return True
            
        time_diff = (current_time - st.session_state.last_refresh).total_seconds()
        
        if time_diff >= refresh_interval:
            st.session_state.last_refresh = current_time
            return True
            
        return False

    def save_dashboard_state(self):
        """Save current dashboard state"""
        state = {
            'time_range': st.session_state.time_range,
            'selected_vehicles': st.session_state.selected_vehicles,
            'metric_preferences': st.session_state.metric_preferences,
            'show_historical': st.session_state.show_historical
        }
        return state

    def load_dashboard_state(self, state):
        """Load saved dashboard state"""
        for key, value in state.items():
            setattr(st.session_state, key, value)