import os
import yaml

def load_config():
    base_path = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(base_path, "config", "config.yaml")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)