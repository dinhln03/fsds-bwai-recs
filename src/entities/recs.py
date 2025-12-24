from pydantic import RootModel


class Recommendation(RootModel):
    root: tuple[str, float]

    @property
    def item_id(self) -> str:
        return self.root[0]

    @property
    def score(self) -> float:
        return self.root[1]


class RecommendationList(RootModel):
    root: list[Recommendation]
