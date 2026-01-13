import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException

from src.api.dto import HealthResponse, RecommendationItem, RecommendationResponse
from src.application.calculate_popular_items import calculate_popular_items
from src.application.fp_growth_recommendations import (
    get_recommendation_app,
    get_recommendations,
    get_similar_items,
)
from src.application.fp_growth_training import train_fp_growth_model
from src.entities.recs import RecommendationList

# Cache configuration
CACHE_TTL_SECONDS = 3600  # 1 hour


class CachedRecommendations:
    """Cache wrapper with TTL support."""

    def __init__(self):
        self._data: RecommendationList | None = None
        self._timestamp: float = 0

    def get(self) -> RecommendationList | None:
        """Get cached data if not expired."""
        if self._data is None:
            return None
        if time.time() - self._timestamp > CACHE_TTL_SECONDS:
            return None
        return self._data

    def set(self, data: RecommendationList) -> None:
        """Set cache data with current timestamp."""
        self._data = data
        self._timestamp = time.time()

    def invalidate(self) -> None:
        """Clear the cache."""
        self._data = None
        self._timestamp = 0


# Cache instance
popular_items_cache = CachedRecommendations()


def get_popular_items(n: int = 100) -> RecommendationList:
    """Get popular items from cache or compute if cache is stale/empty."""
    cached = popular_items_cache.get()
    if cached is not None:
        return cached

    # Recompute and cache
    recommendations = calculate_popular_items(n=n)
    popular_items_cache.set(recommendations)
    return recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm cache at startup and ensure FP-Growth model is trained."""
    try:
        # Pre-warm popular items cache
        get_popular_items(n=100)

        # Ensure FP-Growth model is available
        app_instance = get_recommendation_app()
        app_instance.refresh_model_if_needed(retrain_interval_minutes=10)

    except Exception as e:
        print(f"Warning: Failed to pre-warm cache at startup: {e}")
    yield
    # Cleanup on shutdown
    popular_items_cache.invalidate()


app = FastAPI(lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.get("/recommend/{user_id}", response_model=RecommendationResponse)
def get_popular_recommendations(
    user_id: str, top_k: int = 10
) -> RecommendationResponse:
    """
    Get popular item recommendations for a user.

    Args:
        user_id: The user ID to get recommendations for.
        top_k: Number of recommendations to return (default: 10).

    Returns:
        RecommendationResponse with user_id and list of recommendations with scores.
    """
    # Get from cache or recompute
    recommendations_list = get_popular_items(n=100)

    # Get top_k recommendations
    recommendations = recommendations_list.root[:top_k]

    return RecommendationResponse(
        user_id=user_id,
        recommendations=[
            RecommendationItem(item_id=rec.item_id, score=rec.score)
            for rec in recommendations
        ],
    )


@app.get("/recommend/fpgrowth/{user_id}", response_model=RecommendationResponse)
def get_fpgrowth_recommendations(
    user_id: str, top_k: int = 10, retrain_interval_minutes: int = 10
) -> RecommendationResponse:
    """
    Get FP-Growth based recommendations for a user.

    Args:
        user_id: The user ID to get recommendations for.
        top_k: Number of recommendations to return (default: 10).
        retrain_interval_minutes: Minutes between model retraining (default: 10).

    Returns:
        RecommendationResponse with user_id and list of recommendations.
    """
    try:
        # Get FP-Growth recommendations with automatic retraining
        recommendations = get_recommendations(
            user_id=user_id,
            num_items=top_k,
            retrain_interval_minutes=retrain_interval_minutes,
        )

        # Convert to response format (FP-Growth doesn't return scores, so use index-based scores)
        recommendation_items = [
            RecommendationItem(item_id=item_id, score=1.0 - (i * 0.1))
            for i, item_id in enumerate(recommendations)
        ]

        return RecommendationResponse(
            user_id=user_id, recommendations=recommendation_items
        )

    except Exception:
        # Fallback to popular recommendations if FP-Growth fails
        return get_popular_recommendations(user_id, top_k)


@app.get("/similar/{item_id}", response_model=RecommendationResponse)
def get_similar_items_endpoint(
    item_id: str, top_k: int = 10, retrain_interval_minutes: int = 10
) -> RecommendationResponse:
    """
    Get items similar to a given item using FP-Growth association rules.

    Args:
        item_id: The item ID to find similar items for.
        top_k: Number of similar items to return (default: 10).
        retrain_interval_minutes: Minutes between model retraining (default: 10).

    Returns:
        RecommendationResponse with similar items.
    """
    try:
        # Get similar items with automatic retraining
        similar_items = get_similar_items(
            item_id=item_id,
            num_items=top_k,
            retrain_interval_minutes=retrain_interval_minutes,
        )

        # Convert to response format
        recommendation_items = [
            RecommendationItem(item_id=similar_item, score=1.0 - (i * 0.1))
            for i, similar_item in enumerate(similar_items)
        ]

        return RecommendationResponse(
            user_id=f"similar_to_{item_id}", recommendations=recommendation_items
        )

    except Exception:
        # Return empty recommendations if similar items lookup fails
        return RecommendationResponse(
            user_id=f"similar_to_{item_id}", recommendations=[]
        )


@app.post("/admin/train-fpgrowth")
def train_fpgrowth_model():
    """
    Manually trigger FP-Growth model training.

    Returns:
        Training status and metadata.
    """
    try:
        success = train_fp_growth_model(force_retrain=True)

        if success:
            # Get model info
            app_instance = get_recommendation_app()
            model_info = app_instance.get_model_info()

            return {
                "status": "success",
                "message": "FP-Growth model trained successfully",
                "model_info": model_info,
            }
        else:
            return {"status": "error", "message": "Failed to train FP-Growth model"}

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error training FP-Growth model: {str(e)}",
        }


@app.get("/admin/fpgrowth-info")
def get_fpgrowth_model_info():
    """
    Get information about the current FP-Growth model.

    Returns:
        Model metadata and training information.
    """
    try:
        app_instance = get_recommendation_app()
        model_info = app_instance.get_model_info()

        return {
            "status": "success",
            "model_info": model_info,
            "is_stale": app_instance.is_model_stale(retrain_interval_minutes=10),
        }

    except Exception as e:
        return {"status": "error", "message": f"Error getting model info: {str(e)}"}
