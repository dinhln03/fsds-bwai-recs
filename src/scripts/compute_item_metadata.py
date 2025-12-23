import uuid

import pandas as pd

from ..constants import (
    CSV_DATASET_FILE,
    INT_FOLDER,
    ITEM_METADATA_FILE,
    PROCESSED_FOLDER,
    PROJECT_ROOT_DIR,
)


def compute_item_metadata(input_file: str, output_path: str):
    cols = [
        "title",
        "summary",
        "brief_summary",
        "details",
        "target_audience",
    ]

    # Load the dataset from a CSV file
    origin_df = pd.read_csv(input_file)
    final_df = origin_df[cols].reset_index(drop=True)

    # Generate item_id uuid based on the title column
    if "item_id" not in final_df.columns:
        final_df["item_id"] = final_df["title"].apply(
            lambda x: str(uuid.uuid5(uuid.NAMESPACE_DNS, x))
        )

    final_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    input_path = PROJECT_ROOT_DIR / INT_FOLDER / CSV_DATASET_FILE
    output_path = PROJECT_ROOT_DIR / PROCESSED_FOLDER / ITEM_METADATA_FILE

    compute_item_metadata(
        input_path,
        output_path,
    )
