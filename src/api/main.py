import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.dto import HealthResponse, RecommendationItem, RecommendationResponse
from src.application.mongo_fpgrowth import get_mongo_fpgrowth_app
from src.application.mongo_popular_items import calculate_popular_items_mongo
from src.entities.recs import RecommendationList

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 3600


class CachedRecommendations:
    def __init__(self):
        self._data: RecommendationList | None = None
        self._timestamp: float = 0

    def get(self) -> RecommendationList | None:
        if self._data is None or time.time() - self._timestamp > CACHE_TTL_SECONDS:
            return None
        return self._data

    def set(self, data: RecommendationList) -> None:
        self._data = data
        self._timestamp = time.time()

    def invalidate(self) -> None:
        self._data = None
        self._timestamp = 0


class FPGrowthModelState:
    """Track FP-Growth model state (loaded or not)."""

    def __init__(self):
        self._model_loaded: bool = False

    def is_model_loaded(self) -> bool:
        return self._model_loaded

    def set_model_loaded(self, loaded: bool) -> None:
        self._model_loaded = loaded


popular_cache = CachedRecommendations()
fpgrowth_state = FPGrowthModelState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try to load existing FP-Growth model at startup (no training)
    try:
        logger.info("Attempting to load FP-Growth model...")
        fpgrowth_app = get_mongo_fpgrowth_app()
        if fpgrowth_app.model_path.exists():
            if fpgrowth_app._load_model_only():
                fpgrowth_state.set_model_loaded(True)
                logger.info("FP-Growth model loaded successfully")
            else:
                logger.warning("FP-Growth model file exists but failed to load")
        else:
            logger.info(
                "No FP-Growth model file found, will fallback to popular recommendations"
            )
    except Exception as e:
        logger.error(f"Failed to load FP-Growth model: {e}")
    yield
    popular_cache.invalidate()


app = FastAPI(lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.get("/popular", response_model=RecommendationResponse)
def get_popular_recommendations(
    user_id: str | None = None, top_k: int = 10
) -> RecommendationResponse:
    """Get popular recommendations from MongoDB CourseViews."""
    cached = popular_cache.get()
    if cached is None:
        cached = calculate_popular_items_mongo(n=100)
        popular_cache.set(cached)

    recommendations = cached.root[:top_k]
    return RecommendationResponse(
        user_id=user_id,
        recommendations=[
            RecommendationItem(item_id=r.item_id, score=r.score)
            for r in recommendations
        ],
    )


@app.post("/popular/compute")
def compute_popular():
    """Recompute popular items from MongoDB."""
    try:
        recs = calculate_popular_items_mongo(n=100)
        popular_cache.set(recs)
        return {"status": "success", "count": len(recs.root)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/fpgrowth/{user_id}", response_model=RecommendationResponse)
def get_fpgrowth_recommendations(
    user_id: str, top_k: int = 10
) -> RecommendationResponse:
    """Get personalized FP-Growth recommendations based on user's basket (enrolled/viewed courses)."""
    # If model is loaded, generate personalized recommendations
    # Try to generate personalized recommendations
    # This will attempt to load/train the model if needed via _ensure_model_loaded()
    try:
        app_instance = get_mongo_fpgrowth_app()
        recommendations = app_instance.recommend(user_id=user_id, num_items=top_k)
        
        if recommendations:
            # If successful, ensure state is updated
            if not fpgrowth_state.is_model_loaded():
                fpgrowth_state.set_model_loaded(True)
                
            return RecommendationResponse(
                user_id=user_id,
                recommendations=[
                    RecommendationItem(item_id=item_id, score=1.0 - (i * 0.05))
                    for i, item_id in enumerate(recommendations)
                ],
            )
    except Exception as e:
        logger.warning(f"FP-Growth recommendation failed: {e}")

    # Fallback to popular recommendations (no training triggered)
    return get_popular_recommendations(user_id, top_k)


@app.post("/fpgrowth/compute")
def compute_fpgrowth():
    """Train/retrain FP-Growth model from MongoDB user baskets."""
    try:
        app_instance = get_mongo_fpgrowth_app()
        success = app_instance.train()
        if success:
            fpgrowth_state.set_model_loaded(True)
            return {"status": "success", "model_info": app_instance.get_model_info()}
        return {"status": "error", "message": "Training failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
