from abc import ABC, abstractmethod


class BaseDatasetLoader(ABC):
    @abstractmethod
    def load(self):
        pass


class BaseRecommendationEngine(ABC):
    @abstractmethod
    def recommend(self):
        pass
