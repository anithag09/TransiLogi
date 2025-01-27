# TransiLogi - Intelligent Delivery Management System

## Overview
TransiLogi is a comprehensive delivery management system that combines machine learning, route optimization, and real-time data processing to optimize delivery operations. The system predicts delivery times, optimizes routes for multiple vehicles, and provides API endpoints for seamless integration.

## Features
- 🚚 **Intelligent Delivery Time Prediction**
  - Machine learning models trained on historical delivery data
  - Considers weather, traffic, and location factors
  - Multiple model support (CatBoost, XGBoost, LightGBM, Neural Networks)

- 🗺️ **Route Optimization**
  - Vehicle Routing Problem (VRP) solver
  - Handles multiple vehicles and constraints
  - Considers time windows and vehicle capacity
  - Real-time traffic updates integration

- 🔄 **Data Pipeline**
  - Automated data processing and cleaning
  - Feature engineering for ML models
  - MySQL database integration
  - CSV data export capabilities

- 🌐 **REST API**
  - FastAPI-based backend
  - Endpoints for predictions and route optimization
  - Swagger documentation
  - JWT authentication (optional)

- 📊 **Interactive Dashboard**
  - Real-time delivery monitoring
  - Route visualization with interactive maps
  - Performance metrics and analytics
  - Order management interface

## Dashboard Components

### Pages
- **Route Visualization** (`pages/route_visualization.py`)
  - Interactive map display of delivery routes
  - Vehicle-specific route filtering
  - Stop-by-stop route details
  - Real-time route updates

- **Real-Time Metrics** (`pages/metrics_dashboard.py`)
  - Key performance indicators
  - Time series performance trends
  - Vehicle utilization metrics
  - Cost efficiency tracking

- **Order Management** (`pages/order_management.py`)
  - New order submission interface
  - Order status tracking
  - Historical order view
  - Filtering and search capabilities

- **Analytics** (`pages/analytics.py`)
  - Traffic impact analysis
  - Weather impact visualization
  - Delivery time patterns
  - Performance trends

### Components
- **Maps** (`components/maps.py`)
  - Route visualization
  - Delivery density heatmaps
  - Interactive markers
  - Custom route coloring

- **Charts** (`components/charts.py`)
  - Metric cards
  - Time series charts
  - Bar charts
  - Heat maps

- **Forms** (`components/forms.py`)
  - Order submission form
  - Form validation
  - Input formatting
  - Error handling

### Utils
- **Data Loader** (`utils/data_loader.py`)
  - Database connectivity
  - Query management
  - Data transformation
  - Cache management

- **State Management** (`utils/state_management.py`)
  - Session state handling
  - Page navigation
  - Filter persistence
  - Auto-refresh management

## Project Structure
```
TRANSILOGI/
├── main.py                    # Data pipeline execution
├── Dockerfile                 # Multi-stage docker build
├── docker-compose.yml        # Container orchestration
├── requirements.txt          # Python dependencies
├── README.md                # Project documentation
│
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py         # FastAPI application
│   │
│   ├── config/
│   │   └── config.yml      # Configuration settings
│   │
│   ├── data/
│   │   ├── delivery_data.csv
│   │   └── processed_data.csv
│   │
│   ├── database/
│   │   ├── data_engineering.py
│   │   └── db_loader.py
│   │
│   ├── models/
│   │   ├── prediction.py
│   │   └── route_optimization.py
│   │
│   ├── dashboard/           # Dashboard directory
│   │   ├── __init__.py
│   │   ├── app.py          # Main Streamlit application
│   │   ├── pages/          # Streamlit multi-page components
│   │   │   ├── __init__.py
│   │   │   ├── route_visualization.py
│   │   │   ├── metrics_dashboard.py
│   │   │   ├── order_management.py
│   │   │   └── analytics.py
│   │   ├── components/     # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── maps.py    # Map visualization components
│   │   │   ├── charts.py  # Chart components
│   │   │   └── forms.py   # Input form components
│   │   └── utils/         # Dashboard utility functions
│   │       ├── __init__.py
│   │       ├── data_loader.py
│   │       └── state_management.py
│   │
│   └── utils/
│       └── config_loader.py
│
└── .env                  # Environment variables
```

## Prerequisites
- Python 3.9+
- Docker and Docker Compose
- MySQL 8.0+
- Streamlit 1.10+

## Installation

### Using Docker (Recommended)
1. Clone the repository:
```bash
git clone https://github.com/yourusername/transilogi.git
cd transilogi
```

2. Create `.env` file:
```bash
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=translogi_db
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

### Manual Installation
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure MySQL database in `config.yml`

4. Run the data pipeline:
```bash
python main.py
```

5. Start the API server:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

6. Launch the dashboard:
```bash
streamlit run src/dashboard/app.py
```

## Dashboard Usage

### Route Visualization
- Access the route visualization page to view current delivery routes
- Filter routes by vehicle or time period
- Click on markers to view delivery details
- Toggle between map and table views

### Metrics Dashboard
- Monitor real-time delivery performance
- View historical trends and patterns
- Track vehicle utilization and efficiency
- Export metrics data for reporting

### Order Management
- Submit new delivery orders
- Track order status and history
- Filter and search past orders
- View delivery estimates

### Analytics
- Analyze traffic and weather impacts
- View delivery time patterns
- Monitor performance trends
- Generate custom reports

## API Usage

### Predict Delivery Time
```bash
curl -X POST "http://localhost:8000/api/v1/predict-delivery" \
     -H "Content-Type: application/json" \
     -d '{
       "customer_location": "New York",
       "delivery_priority": "Express",
       "package_weight": 15.5,
       "latitude": 40.7128,
       "longitude": -74.0060,
       "weather_condition": "Clear",
       "traffic_condition": "Moderate"
     }'
```

### Get Optimized Routes
```bash
curl "http://localhost:8000/api/v1/routes/2024-01-27"
```

## Configuration
Key configurations in `config.yml`:
```yaml
database:
  DB_HOST: 127.0.0.1
  DB_USER: root
  DB_PASSWORD: your_password
  DB_NAME: translogi_db

models:
  random_forest:
    n_estimators: 100
    max_depth: 10
  # ... other model configs

route_optimization:
  max_vehicles: 20
  max_capacity: 1000
  time_window: 600

dashboard:
  refresh_interval: 300
  map_default_zoom: 11
  enable_real_time_updates: true
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
The project follows PEP 8 guidelines. Run linter:
```bash
flake8 .
```

## Monitoring and Logging
- Logs are stored in `logs/` directory
- API metrics available at `/metrics` endpoint
- Docker container logs accessible via `docker-compose logs`
- Dashboard metrics visible in real-time

## Acknowledgments
- Google OR-Tools for route optimization
- FastAPI framework
- Streamlit for dashboard
- CatBoost, XGBoost, and LightGBM teams
