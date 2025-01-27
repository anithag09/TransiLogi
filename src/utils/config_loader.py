import os
import yaml

class ConfigLoader:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yml')

    def load_config(self):
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
            return {
                # Database configuration
                'DB_HOST': config['database']['DB_HOST'],
                'DB_USER': config['database']['DB_USER'],
                'DB_PASSWORD': config['database']['DB_PASSWORD'],
                'DB_NAME': config['database']['DB_NAME'],

                # Models configuration
                'models': config['models'],

                # Route optimization configuration
                'route_optimization': config['route_optimization']
            }