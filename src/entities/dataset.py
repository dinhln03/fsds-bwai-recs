from abc import abstractmethod

import pandas as pd
from pydantic import BaseModel


class BaseDataset(BaseModel):
    user_col: str
    item_col: str
    interaction_col: str
    timestamp_col: str

    @abstractmethod
    def get_pandas_dataframe(self) -> pd.DataFrame:
        pass


class CSVDataset(BaseDataset):
    model_config = {"arbitrary_types_allowed": True}

    user_col: str = "user_id"
    item_col: str = "item_id"
    interaction_col: str = "interaction"
    timestamp_col: str = "timestamp"
    pandas_df: pd.DataFrame

    def get_pandas_dataframe(self) -> pd.DataFrame:
        return self.pandas_df
