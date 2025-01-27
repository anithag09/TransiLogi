from src.database.db_loader import DBLoader
from src.database.data_engineering import DataEngineering
from src.models.prediction import PredictionModel
from src.models.route_optimization import RouteOptimization

def main():
    # Initialize components
    db_loader = DBLoader()
    data_engineer = DataEngineering()
    prediction_model = PredictionModel()
    route_optimizer = RouteOptimization()

    # Execute pipeline
    print("Starting data pipeline...")
    
    print("1. Loading data...")
    db_loader.load_delivery_data()
    
    print("2. Processing data...")
    data_engineer.preprocess_data()
    
    print("3. Training prediction model...")
    prediction_model.train_and_save_model()
    
    print("4. Optimizing routes...")
    optimized_routes = route_optimizer.solve_vrp()
    
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    main()
