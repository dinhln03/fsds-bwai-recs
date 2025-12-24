from ..constants import (
    PROCESSED_FOLDER,
    PROJECT_ROOT_DIR,
    SYNTHETIC_INTERACTIONS_FILE,
)
from ..loaders import CSVDatasetLoader
from ..recommendation.popular_recs import PopularItemsRecommendationEngine


def calculate_popular_items(n: int = 100):
    """
    Application layer function to calculate popular items.

    1. Initialize the CSV dataset loader
    2. Load the synthetic interactions dataset
    3. Compute popular items using the recommendation engine
    4. Return the recommendation list
    """
    # Initialize the CSV dataset loader
    loader = CSVDatasetLoader()

    # Load the dataset from CSV
    dataset_path = PROJECT_ROOT_DIR / PROCESSED_FOLDER / SYNTHETIC_INTERACTIONS_FILE
    dataset = loader.load(file_path=str(dataset_path))

    # Initialize the recommendation engine with the dataset
    recommendation_engine = PopularItemsRecommendationEngine(dataset=dataset)

    # Compute and return popular items
    return recommendation_engine.recommend(n=n)


if __name__ == "__main__":
    recommendations = calculate_popular_items()
    print(recommendations.model_dump())
