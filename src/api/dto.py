from pydantic import BaseModel


class RecommendationItem(BaseModel):
    item_id: str
    score: float


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[RecommendationItem]


class HealthResponse(BaseModel):
    status: str
