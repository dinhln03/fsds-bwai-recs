from ..entities.recs import RecommendationList
from ..loaders import MongoDatasetLoader


def calculate_popular_items_mongo(n: int = 100):
    """Calculate popular items from MongoDB Courses views field."""
    loader = MongoDatasetLoader()
    dataset = loader.load_courses_popularity(n=n)
    df = dataset.get_pandas_dataframe()
    
    if df.empty:
        return RecommendationList(root=[])
    
    # Normalize scores
    max_views = df["interaction"].max()
    items_with_scores = [
        (row["item_id"], row["interaction"] / max_views if max_views > 0 else 0)
        for _, row in df.iterrows()
    ]
    return RecommendationList(root=items_with_scores)
