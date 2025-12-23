import pandas as pd
from fastapi import FastAPI

from src.constants import (
    PROCESSED_FOLDER,
    PROJECT_ROOT_DIR,
    SYNTHETIC_INTERACTIONS_FILE,
)

app = FastAPI()

DATA_PATH = PROJECT_ROOT_DIR / PROCESSED_FOLDER / SYNTHETIC_INTERACTIONS_FILE

# Load and compute popular items at startup
df = pd.read_csv(DATA_PATH)
popular_items = df.groupby("item_id")["interaction"].sum().sort_values(ascending=False)


@app.get("/recommend/{user_id}")
def get_popular_recommendations(user_id: str, top_k: int = 100):
    top_items = popular_items.head(top_k).index.tolist()
    return {"user_id": user_id, "recommendations": top_items}
