import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from ..constants import PROJECT_ROOT_DIR
from ..loaders import MongoDatasetLoader
from ..recommendation.fp_growth_recs.training import FPGrowthRecommendationEngine

logger = logging.getLogger(__name__)


class MongoFPGrowthApp:
    """FP-Growth training and recommendations using MongoDB data."""

    def __init__(self, min_support: float = 0.02, min_confidence: float = 0.2):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.model_dir = Path(PROJECT_ROOT_DIR) / "data" / "models"
        self.model_path = self.model_dir / "mongo_fp_growth_model.pkl"
        self.metadata_path = self.model_dir / "mongo_fp_growth_metadata.pkl"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._engine: Optional[FPGrowthRecommendationEngine] = None
        self._loader = MongoDatasetLoader()

    def _load_transactions(self) -> List[List[str]]:
        """Load transactions from MongoDB.

        First tries user enrollment baskets (proper basket analysis).
        Falls back to tag-based transactions if not enough user data.
        """
        logger.info("Loading user enrollment transactions from MongoDB...")
        transactions = self._loader.load_user_baskets()

        if len(transactions) >= 10:
            logger.info(f"Using {len(transactions)} user baskets for training")
            if transactions:
                avg_size = sum(len(t) for t in transactions) / len(transactions)
                logger.info(f"Average basket size: {avg_size:.1f}")
            return transactions

        # Fallback to tag-based transactions
        logger.info(
            "Not enough user baskets, falling back to tag-based transactions..."
        )
        transactions = self._loader.load_courses_by_tags(max_transaction_size=10)
        logger.info(f"Loaded {len(transactions)} tag-based transactions from MongoDB")
        if transactions:
            avg_size = sum(len(t) for t in transactions) / len(transactions)
            logger.info(f"Average transaction size: {avg_size:.1f}")
        return transactions

    def train(self) -> bool:
        """Train FP-Growth model from MongoDB data."""
        try:
            logger.info("Starting FP-Growth training...")
            transactions = self._load_transactions()
            if not transactions:
                logger.warning("No transactions found")
                return False

            logger.info("Fitting FP-Growth engine...")
            self._engine = FPGrowthRecommendationEngine(
                min_support=self.min_support, min_confidence=self.min_confidence
            )
            self._engine.fit(transactions)

            with open(self.model_path, "wb") as f:
                pickle.dump(self._engine, f)

            metadata = {
                "training_time": datetime.now(),
                "num_transactions": len(transactions),
                "min_support": self.min_support,
                "min_confidence": self.min_confidence,
            }
            with open(self.metadata_path, "wb") as f:
                pickle.dump(metadata, f)

            logger.info("MongoDB FP-Growth model trained successfully")
            return True
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False

    def _load_model_only(self) -> bool:
        """Load model from disk only, do not trigger training."""
        if not self.model_path.exists():
            return False
        try:
            with open(self.model_path, "rb") as f:
                self._engine = pickle.load(f)
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def _ensure_model_loaded(self) -> bool:
        if self._engine is not None:
            return True
        if not self.model_path.exists():
            return self.train()
        try:
            with open(self.model_path, "rb") as f:
                self._engine = pickle.load(f)
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def get_user_items(self, user_id: str) -> List[str]:
        """Get courses the user has enrolled in or viewed, sorted by latest."""
        return self._loader.get_user_courses(user_id)

    def recommend(self, user_id: str, num_items: int = 10) -> List[str]:
        """Generate personalized recommendations based on user's basket."""
        if not self._ensure_model_loaded():
            return []

        # Get user's current items (their basket), sorted by latest
        all_user_items = self.get_user_items(user_id)

        # Use only latest 5 items for context to generate recommendations
        context_items = set(all_user_items[:5])
        # But we want to exclude ALL items the user has already seen
        exclude_items = set(all_user_items)

        if context_items:
            # Use association rules to recommend based on user's recent items
            # We request more items to account for filtering
            raw_recommendations = self._engine.recommend(
                user_id=user_id,
                num_items=num_items + 20,
                user_items=context_items,
            )
            
            # Filter out items the user has already seen
            recommendations = [
                item for item in raw_recommendations 
                if item not in exclude_items
            ]
            
            if recommendations:
                return recommendations[:num_items]

        # Fallback: return popular associated items if user has no items or no rules match
        return self._engine.get_popular_associated_items(num_items=num_items)

    def get_model_info(self) -> dict:
        if self.metadata_path.exists():
            with open(self.metadata_path, "rb") as f:
                return pickle.load(f)
        return {}


# Singleton instance
_mongo_fpgrowth_app: Optional[MongoFPGrowthApp] = None


def get_mongo_fpgrowth_app() -> MongoFPGrowthApp:
    global _mongo_fpgrowth_app
    if _mongo_fpgrowth_app is None:
        _mongo_fpgrowth_app = MongoFPGrowthApp()
    return _mongo_fpgrowth_app
