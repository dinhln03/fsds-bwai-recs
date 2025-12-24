import pandas as pd

from .base import BaseDatasetLoader
from .entities.dataset import CSVDataset


class CSVDatasetLoader(BaseDatasetLoader):
    def load(self, *, file_path: str):
        """
        Load data from a CSV file and convert it into a Pandas DataFrame.
        Finally, return the CSVDataset domain entity.
        """

        df = pd.read_csv(file_path)
        return CSVDataset(
            pandas_df=df,
        )
