import os
import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from src.utils.config_loader import ConfigLoader

class RouteOptimization:
    def __init__(self):
        self.config = ConfigLoader().load_config()
        self.depot_location = (39.8283, -98.5795)  # Geographic center of US
        
    def solve_vrp(self):
        """Main function to solve the Vehicle Routing Problem"""
        # Load processed delivery data
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
        self.delivery_df = pd.read_csv(csv_path)
        
        # Create distance matrix
        distance_matrix = self._create_distance_matrix()
        
        # Create data model for OR-Tools
        data = self._create_data_model(distance_matrix)
        
        # Create routing model
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # Define distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add capacity constraint
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]
            
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )
        
        # Add time windows constraint
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['time_matrix'][from_node][to_node]
            
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_index,
            30,  # allow waiting time
            self.config['route_optimization']['time_window'],  # maximum time per vehicle
            False,  # don't force start cumul to zero
            'Time'
        )
        time_dimension = routing.GetDimensionOrDie('Time')
        
        # Add time window constraints
        for location_idx, time_window in enumerate(data['time_windows']):
            if location_idx == data['depot']:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(
                time_window[0],
                time_window[1]
            )
            
        # Set first solution strategy
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30
        
        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            routes = self._get_routes(solution, routing, manager)
            self._save_routes_to_db(routes)
            return routes
        return None
        
    def _create_distance_matrix(self):
        """Create distance matrix from latitude and longitude"""
        locations = self.delivery_df[['latitude', 'longitude']].values
        n_locations = len(locations)
        matrix = np.zeros((n_locations, n_locations))
        
        for i in range(n_locations):
            for j in range(n_locations):
                if i != j:
                    # Calculate Euclidean distance and apply traffic impact
                    base_distance = np.sqrt(
                        (locations[i][0] - locations[j][0])**2 +
                        (locations[i][1] - locations[j][1])**2
                    )
                    traffic_impact = self.delivery_df.iloc[j]['traffic_impact']
                    weather_impact = self.delivery_df.iloc[j]['weather_impact']
                    matrix[i][j] = base_distance * traffic_impact * weather_impact
                    
        return matrix.astype(int)
        
    def _create_data_model(self, distance_matrix):
        """Create the data model for OR-Tools"""
        data = {}
        data['distance_matrix'] = distance_matrix
        data['time_matrix'] = distance_matrix  # Using distance as proxy for time
        data['num_vehicles'] = min(
            self.config['route_optimization']['max_vehicles'],
            len(self.delivery_df['vehicle_id'].unique())
        )
        data['depot'] = 0
        
        # Vehicle capacities
        data['vehicle_capacities'] = [
            self.config['route_optimization']['max_capacity']
        ] * data['num_vehicles']
        
        # Node demands (package weights)
        data['demands'] = self.delivery_df['package_weight'].astype(int).tolist()
        
        # Time windows
        data['time_windows'] = []
        for _, row in self.delivery_df.iterrows():
            delivery_time = pd.to_datetime(row['actual_delivery_time'])
            window_start = int(delivery_time.hour * 60 + delivery_time.minute)
            window_end = window_start + 240  # 4-hour window
            data['time_windows'].append((window_start, window_end))
            
        return data
        
    def _get_routes(self, solution, routing, manager):
        """Extract the routes from the solution"""
        routes = []
        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append({
                    'order_id': self.delivery_df.iloc[node_index]['order_id'],
                    'location': self.delivery_df.iloc[node_index]['customer_location'],
                    'latitude': float(self.delivery_df.iloc[node_index]['latitude']),
                    'longitude': float(self.delivery_df.iloc[node_index]['longitude']),
                    'delivery_time': str(self.delivery_df.iloc[node_index]['actual_delivery_time'])
                })
                index = solution.Value(routing.NextVar(index))
            routes.append({
                'vehicle_id': f'VEH-{vehicle_id:03d}',
                'stops': route
            })
        return routes
        
    def _save_routes_to_db(self, routes):
        """Save the optimized routes to the database"""
        db = mysql.connector.connect(
            host=self.config['DB_HOST'],
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            database=self.config['DB_NAME']
        )
        cursor = db.cursor()
        
        # Create optimized_routes table if it doesn't exist
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
        
        # Insert routes into database
        for route in routes:
            for stop_num, stop in enumerate(route['stops'], 1):
                sql = """
                    INSERT INTO optimized_routes (
                        route_id, vehicle_id, stop_number, order_id, location,
                        latitude, longitude, planned_delivery_time, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    f"ROUTE-{datetime.now().strftime('%Y%m%d')}-{route['vehicle_id']}",
                    route['vehicle_id'],
                    stop_num,
                    stop['order_id'],
                    stop['location'],
                    stop['latitude'],
                    stop['longitude'],
                    stop['delivery_time'],
                    datetime.now()
                )
                cursor.execute(sql, values)
                
        db.commit()
        db.close()