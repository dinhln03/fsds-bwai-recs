import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.dto import HealthResponse, RecommendationItem, RecommendationResponse
from src.application.calculate_popular_items import calculate_popular_items
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
    """Pre-warm cache at startup."""
    try:
        get_popular_items(n=100)
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
