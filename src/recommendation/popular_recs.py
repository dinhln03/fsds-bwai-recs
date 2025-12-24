from ..base import BaseRecommendationEngine
from ..entities.dataset import BaseDataset
from ..entities.recs import RecommendationList


class PopularItemsRecommendationEngine(BaseRecommendationEngine):
    def __init__(self, dataset: BaseDataset):
        self.dataset = dataset

    def recommend(self, n: int = 100):
        df = self.dataset.get_pandas_dataframe()

        popular_items_df = (
            df.groupby(self.dataset.item_col)[self.dataset.interaction_col]
            .sum()
            .sort_values(ascending=False)
            .head(n)
        )

        # Map popular item IDs to their scores
        popular_items = popular_items_df.index.tolist()
        popular_scores = popular_items_df.values.tolist()
        popular_scores = self._normalize_scores(popular_scores)

        return RecommendationList(root=list(zip(popular_items, popular_scores)))

    def _normalize_scores(self, scores: list[float]) -> list[float]:
        # Normalize scores to be between 0 and 1
        if not scores:
            return scores
        min_score = min(scores)
        max_score = max(scores)
        if max_score > min_score:
            return [(score - min_score) / (max_score - min_score) for score in scores]
        return scores
