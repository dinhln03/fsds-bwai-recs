import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from ..constants import PROJECT_ROOT_DIR
from ..loaders import CSVDatasetLoader
from ..recommendation.fp_growth_recs.training import FPGrowthRecommendationEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPGrowthTrainingApp:
    def __init__(
        self,
        min_support: float = 0.01,
        min_confidence: float = 0.5,
        model_dir: str = "models",
    ):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.model_dir = Path(PROJECT_ROOT_DIR) / "data" / model_dir
        self.model_path = self.model_dir / "fp_growth_model.pkl"
        self.metadata_path = self.model_dir / "fp_growth_metadata.pkl"

        # Ensure model directory exists
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.engine = FPGrowthRecommendationEngine(
            min_support=min_support, min_confidence=min_confidence
        )

    def _load_transaction_data(self) -> List[List[str]]:
        """Load and prepare transaction data"""
        try:
            # Use infrastructure loader to load synthetic interactions data
            interactions_path = (
                Path(PROJECT_ROOT_DIR)
                / "data"
                / "processed"
                / "synthetic_interactions.csv"
            )
            loader = CSVDatasetLoader()
            dataset = loader.load(file_path=str(interactions_path))
            df = dataset.get_pandas_dataframe()

            # Group by user_id to create transactions
            transactions = []
            for user_id, group in df.groupby("user_id"):
                transaction = group["item_id"].unique().tolist()
                if len(transaction) > 1:  # Only include users with multiple items
                    transactions.append(transaction)

            logger.info(f"Loaded {len(transactions)} transactions")
            return transactions

        except Exception as e:
            logger.error(f"Error loading transaction data: {e}")
            return []

    def train(self) -> bool:
        """Train the FP-Growth model and save to disk"""
        try:
            logger.info("Starting FP-Growth model training...")

            # Load transaction data
            transactions = self._load_transaction_data()
            if not transactions:
                logger.error("No transaction data loaded")
                return False

            # Train the model
            self.engine.fit(transactions)

            # Save the trained model
            with open(self.model_path, "wb") as f:
                pickle.dump(self.engine, f)

            # Save metadata
            metadata = {
                "training_time": datetime.now(),
                "num_transactions": len(transactions),
                "min_support": self.min_support,
                "min_confidence": self.min_confidence,
                "num_frequent_itemsets": len(self.engine.frequent_itemsets)
                if self.engine.frequent_itemsets is not None
                else 0,
                "num_association_rules": len(self.engine.association_rules_df)
                if self.engine.association_rules_df is not None
                else 0,
            }

            with open(self.metadata_path, "wb") as f:
                pickle.dump(metadata, f)

            logger.info(f"Model training completed and saved to {self.model_path}")
            logger.info(f"Training metadata: {metadata}")

            return True

        except Exception as e:
            logger.error(f"Error during training: {e}")
            return False

    def get_training_metadata(self) -> dict:
        """Get training metadata if exists"""
        try:
            if self.metadata_path.exists():
                with open(self.metadata_path, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")

        return {}

    def should_retrain(self, retrain_interval_minutes: int = 10) -> bool:
        """Check if model should be retrained based on time"""
        metadata = self.get_training_metadata()
        if not metadata or "training_time" not in metadata:
            return True

        last_training = metadata["training_time"]
        time_since_training = datetime.now() - last_training

        return time_since_training > timedelta(minutes=retrain_interval_minutes)


def train_fp_growth_model(
    min_support: float = 0.01,
    min_confidence: float = 0.5,
    force_retrain: bool = False,
) -> bool:
    """Standalone function to train FP-Growth model"""
    app = FPGrowthTrainingApp(min_support, min_confidence)

    if not force_retrain and not app.should_retrain():
        logger.info("Model is up to date, skipping training")
        return True

    return app.train()


if __name__ == "__main__":
    # Train the model when run directly
    success = train_fp_growth_model(force_retrain=True)
    if success:
        print("FP-Growth model training completed successfully!")
    else:
        print("FP-Growth model training failed!")
