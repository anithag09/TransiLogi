import os
import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from src.utils.config_loader import ConfigLoader
from functools import lru_cache
from scipy.spatial.distance import pdist, squareform

class RouteOptimization:
    def __init__(self):
        self.config = ConfigLoader().load_config()
        self.depot_location = (39.8283, -98.5795)
        self._init_cache()
        
    def _init_cache(self):
        """Initialize cache settings for frequently accessed data"""
        self._distance_matrix_cache = None
        self._data_model_cache = None
        
    @lru_cache(maxsize=128)
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Cached distance calculation between two points"""
        return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

    def solve_vrp(self):
        """Main function to solve the Vehicle Routing Problem with optimizations"""
        # Load and preprocess data efficiently
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
        self.delivery_df = pd.read_csv(csv_path, usecols=[
            'order_id', 'customer_location', 'latitude', 'longitude',
            'actual_delivery_time', 'package_weight', 'traffic_impact',
            'weather_impact', 'vehicle_id'
        ])
        
        # Vectorized distance matrix calculation
        distance_matrix = self._create_distance_matrix_vectorized()
        
        # Create data model with optimized structure
        data = self._create_data_model_optimized(distance_matrix)
        
        # Optimize routing parameters
        manager, routing = self._create_routing_model(data)
        
        # Register callbacks efficiently
        self._register_callbacks(routing, manager, data)
        
        # Optimize search parameters
        solution = self._solve_with_optimized_parameters(routing)
        
        if solution:
            routes = self._get_routes_optimized(solution, routing, manager)
            self._batch_save_routes_to_db(routes)
            return routes
        return None

    def _create_distance_matrix_vectorized(self):
        """Create distance matrix using vectorized operations"""
        if self._distance_matrix_cache is not None:
            return self._distance_matrix_cache
            
        locations = self.delivery_df[['latitude', 'longitude']].values
        
        # Use scipy's pdist for efficient distance calculation
        distances = pdist(locations, metric='euclidean')
        matrix = squareform(distances)
        
        # Vectorized impact calculations
        traffic_impact = self.delivery_df['traffic_impact'].values
        weather_impact = self.delivery_df['weather_impact'].values
        
        # Broadcasting for efficient multiplication
        impact_matrix = np.outer(np.ones(len(matrix)), traffic_impact * weather_impact)
        matrix *= impact_matrix
        
        self._distance_matrix_cache = matrix.astype(np.int32)
        return self._distance_matrix_cache

    def _create_data_model_optimized(self, distance_matrix):
        """Create optimized data model with minimal conversions"""
        if self._data_model_cache is not None:
            return self._data_model_cache
            
        data = {
            'distance_matrix': distance_matrix,
            'time_matrix': distance_matrix,
            'num_vehicles': min(
                self.config['route_optimization']['max_vehicles'],
                self.delivery_df['vehicle_id'].nunique()
            ),
            'depot': 0,
            'vehicle_capacities': [
                self.config['route_optimization']['max_capacity']
            ] * self.delivery_df['vehicle_id'].nunique(),
            'demands': self.delivery_df['package_weight'].astype(np.int32).tolist(),
        }
        
        # Vectorized time window calculation
        delivery_times = pd.to_datetime(self.delivery_df['actual_delivery_time'])
        minutes_since_midnight = delivery_times.dt.hour * 60 + delivery_times.dt.minute
        window_starts = minutes_since_midnight.astype(np.int32)
        window_ends = window_starts + 240
        
        data['time_windows'] = list(zip(window_starts, window_ends))
        
        self._data_model_cache = data
        return data

    def _create_routing_model(self, data):
        """Create routing model with optimized settings"""
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        routing = pywrapcp.RoutingModel(manager)
        return manager, routing

    def _register_callbacks(self, routing, manager, data):
        """Register all callbacks efficiently"""
        # Use numpy arrays for faster lookup
        distance_matrix = np.array(data['distance_matrix'])
        demands = np.array(data['demands'])
        time_matrix = np.array(data['time_matrix'])
        
        def distance_callback(from_index, to_index):
            return int(distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])
            
        def demand_callback(from_index):
            return int(demands[manager.IndexToNode(from_index)])
            
        def time_callback(from_index, to_index):
            return int(time_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])
        
        # Register callbacks
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            data['vehicle_capacities'],
            True,
            'Capacity'
        )
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_index,
            30,
            self.config['route_optimization']['time_window'],
            False,
            'Time'
        )
        
        # Add time windows efficiently
        time_dimension = routing.GetDimensionOrDie('Time')
        for location_idx, time_window in enumerate(data['time_windows']):
            if location_idx == data['depot']:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    def _solve_with_optimized_parameters(self, routing):
        """Solve with optimized search parameters"""
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30
        search_parameters.use_full_propagation = True
        search_parameters.log_search = False
        
        return routing.SolveWithParameters(search_parameters)

    def _get_routes_optimized(self, solution, routing, manager):
        """Extract routes with minimal dataframe operations"""
        routes = []
        df_values = self.delivery_df[['order_id', 'customer_location', 'latitude', 'longitude', 'actual_delivery_time']].values
        
        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                row = df_values[node_index]
                route.append({
                    'order_id': row[0],
                    'location': row[1],
                    'latitude': float(row[2]),
                    'longitude': float(row[3]),
                    'delivery_time': str(row[4])
                })
                index = solution.Value(routing.NextVar(index))
            routes.append({
                'vehicle_id': f'VEH-{vehicle_id:03d}',
                'stops': route
            })
        return routes

    def _batch_save_routes_to_db(self, routes):
        """Save routes to database using batch operations"""
        db = mysql.connector.connect(
            host=self.config['DB_HOST'],
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            database=self.config['DB_NAME']
        )
        cursor = db.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimized_routes (
                route_id VARCHAR(50),
                vehicle_id VARCHAR(50),
                stop_number INT,
                order_id VARCHAR(50),
                location VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                planned_delivery_time DATETIME,
                created_at DATETIME
            )
        """)
        
        # Prepare batch insert
        current_date = datetime.now().strftime('%Y%m%d')
        current_time = datetime.now()
        
        values = []
        for route in routes:
            route_id = f"ROUTE-{current_date}-{route['vehicle_id']}"
            for stop_num, stop in enumerate(route['stops'], 1):
                values.append((
                    route_id,
                    route['vehicle_id'],
                    stop_num,
                    stop['order_id'],
                    stop['location'],
                    stop['latitude'],
                    stop['longitude'],
                    stop['delivery_time'],
                    current_time
                ))
        
        # Batch insert
        cursor.executemany("""
            INSERT INTO optimized_routes (
                route_id, vehicle_id, stop_number, order_id, location,
                latitude, longitude, planned_delivery_time, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        
        db.commit()
        db.close()
