from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT_DIR / "data"
RAW_DATA_PATH = PROJECT_ROOT_DIR / "data" / "raw" / "recsys_dataset.json"
INT_FOLDER = "data/interim"
PROCESSED_FOLDER = "data/processed"

CSV_DATASET_FILE = "recsys_dataset.csv"
ITEM_METADATA_FILE = "item_metadata.csv"
ITEM_CLUSTERS_FILE = "item_clusters.csv"
SYNTHETIC_INTERACTIONS_FILE = "synthetic_interactions.csv"
