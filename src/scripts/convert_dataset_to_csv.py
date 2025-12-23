import pandas as pd

from ..constants import CSV_DATASET_FILE, INT_FOLDER, PROJECT_ROOT_DIR, RAW_DATA_PATH


def convert_dataset_to_csv(input_file, output_file):
    # Load the dataset from a JSON file
    df = pd.read_json(input_file)

    print("Sample data loaded from JSON:")
    print(df.sample(5))  # Show a sample of 5 rows from the loaded data

    # Save the DataFrame to a CSV file
    df.to_csv(output_file, index=False)
    print(f"Dataset successfully converted to CSV and saved to {output_file}")


if __name__ == "__main__":
    output_path = PROJECT_ROOT_DIR / INT_FOLDER / CSV_DATASET_FILE

    convert_dataset_to_csv(RAW_DATA_PATH, output_path)
