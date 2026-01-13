import logging
import pickle
from pathlib import Path
from typing import List, Optional, Set

from ..constants import PROJECT_ROOT_DIR
from ..loaders import CSVDatasetLoader
from ..recommendation.fp_growth_recs.training import FPGrowthRecommendationEngine
from .fp_growth_training import FPGrowthTrainingApp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPGrowthRecommendationApp:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(PROJECT_ROOT_DIR) / "data" / model_dir
        self.model_path = self.model_dir / "fp_growth_model.pkl"
        self.metadata_path = self.model_dir / "fp_growth_metadata.pkl"
        self._engine: Optional[FPGrowthRecommendationEngine] = None

    def _load_model(self) -> bool:
        """Load the trained model from disk"""
        try:
            if not self.model_path.exists():
                logger.warning("Model file not found, training new model...")
                # If no model exists, train one
                trainer = FPGrowthTrainingApp()
                if trainer.train():
                    return self._load_model()  # Retry loading after training
                else:
                    logger.error("Failed to train new model")
                    return False

            with open(self.model_path, "rb") as f:
                self._engine = pickle.load(f)

            logger.info(f"Model loaded successfully from {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def _ensure_model_loaded(self) -> bool:
        """Ensure model is loaded, load if necessary"""
        if self._engine is None:
            return self._load_model()
        return True

    def get_user_items(self, user_id: str) -> Set[str]:
        """Get items that user has interacted with"""
        try:
            # Use infrastructure loader to load user interaction data
            interactions_path = (
                Path(PROJECT_ROOT_DIR)
                / "data"
                / "processed"
                / "synthetic_interactions.csv"
            )
            loader = CSVDatasetLoader()
            dataset = loader.load(file_path=str(interactions_path))
            df = dataset.get_pandas_dataframe()

            # Get user's items
            user_items = df[df["user_id"] == user_id]["item_id"].unique()
            return set(user_items)

        except Exception as e:
            logger.error(f"Error loading user items for {user_id}: {e}")
            return set()

    def recommend(
        self, user_id: str, num_items: int = 10, user_items: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Generate recommendations for a user
        """
        try:
            # Ensure model is loaded
            if not self._ensure_model_loaded():
                logger.error("Failed to load model")
                return []

            # Get user items if not provided
            if user_items is None:
                user_items = self.get_user_items(user_id)

            if not user_items:
                logger.warning(f"No interaction history found for user {user_id}")
                return []

            # Generate recommendations
            recommendations = self._engine.recommend(
                user_id=user_id, num_items=num_items, user_items=user_items
            )

            logger.info(
                f"Generated {len(recommendations)} recommendations for user {user_id}"
            )
            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            return []

    def recommend_similar_items(self, item_id: str, num_items: int = 10) -> List[str]:
        """
        Get items similar to a given item based on association rules
        """
        try:
            # Ensure model is loaded
            if not self._ensure_model_loaded():
                logger.error("Failed to load model")
                return []

            # Get recommendations for this item
            item_recs = self._engine.get_item_recommendations_dict()

            if item_id in item_recs:
                similar_items = [item for item, score in item_recs[item_id][:num_items]]
                return similar_items
            else:
                logger.warning(f"No similar items found for {item_id}")
                return []

        except Exception as e:
            logger.error(f"Error getting similar items for {item_id}: {e}")
            return []

    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        try:
            if self.metadata_path.exists():
                with open(self.metadata_path, "rb") as f:
                    metadata = pickle.load(f)
                return metadata
        except Exception as e:
            logger.error(f"Error loading model metadata: {e}")

        return {}

    def is_model_stale(self, retrain_interval_minutes: int = 10) -> bool:
        """Check if model needs retraining"""
        trainer = FPGrowthTrainingApp()
        return trainer.should_retrain(retrain_interval_minutes)

    def refresh_model_if_needed(self, retrain_interval_minutes: int = 10) -> bool:
        """Refresh model if it's stale"""
        if self.is_model_stale(retrain_interval_minutes):
            logger.info("Model is stale, retraining...")
            trainer = FPGrowthTrainingApp()
            if trainer.train():
                # Reload the model
                self._engine = None
                return self._load_model()
            else:
                logger.error("Failed to retrain model")
                return False
        return True


# Global instance for the API
_recommendation_app: Optional[FPGrowthRecommendationApp] = None


def get_recommendation_app() -> FPGrowthRecommendationApp:
    """Get singleton recommendation app instance"""
    global _recommendation_app
    if _recommendation_app is None:
        _recommendation_app = FPGrowthRecommendationApp()
    return _recommendation_app


def get_recommendations(
    user_id: str, num_items: int = 10, retrain_interval_minutes: int = 10
) -> List[str]:
    """
    Standalone function to get recommendations with automatic model refresh
    """
    app = get_recommendation_app()

    # Check if model needs refresh
    app.refresh_model_if_needed(retrain_interval_minutes)

    # Generate recommendations
    return app.recommend(user_id, num_items)


def get_similar_items(
    item_id: str, num_items: int = 10, retrain_interval_minutes: int = 10
) -> List[str]:
    """
    Standalone function to get similar items with automatic model refresh
    """
    app = get_recommendation_app()

    # Check if model needs refresh
    app.refresh_model_if_needed(retrain_interval_minutes)

    # Get similar items
    return app.recommend_similar_items(item_id, num_items)


if __name__ == "__main__":
    # Test the recommendation system
    app = FPGrowthRecommendationApp()

    # Get sample user for testing using the infrastructure loader
    interactions_path = (
        Path(PROJECT_ROOT_DIR) / "data" / "processed" / "synthetic_interactions.csv"
    )
    loader = CSVDatasetLoader()
    dataset = loader.load(file_path=str(interactions_path))
    df = dataset.get_pandas_dataframe()
    sample_user = df["user_id"].iloc[0]

    print(f"Testing recommendations for user: {sample_user}")
    recommendations = app.recommend(sample_user, num_items=5)
    print(f"Recommendations: {recommendations}")

    # Test model info
    model_info = app.get_model_info()
    print(f"Model info: {model_info}")
