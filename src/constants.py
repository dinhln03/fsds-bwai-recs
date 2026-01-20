import os
from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT_DIR / "data"
RAW_DATA_PATH = PROJECT_ROOT_DIR / "data" / "raw" / "recsys_dataset.json"
INT_FOLDER = "data/interim"
PROCESSED_FOLDER = "data/processed"
MONGO_DUMP_DIR = PROJECT_ROOT_DIR / "data" / "mongo" / "fsds"

CSV_DATASET_FILE = "recsys_dataset.csv"
ITEM_METADATA_FILE = "item_metadata.csv"
ITEM_CLUSTERS_FILE = "item_clusters.csv"
SYNTHETIC_INTERACTIONS_FILE = "synthetic_interactions.csv"

# MongoDB settings
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = os.getenv("MONGO_URI", f"mongodb://{MONGO_HOST}:{MONGO_PORT}")
MONGO_DB = os.getenv("MONGO_DB", "fsds")