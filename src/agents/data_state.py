import uuid
from pathlib import Path
import pandas as pd


class DataState:
    def __init__(self):
        self.artifacts = {"dataframes": {}, "images": {}}
        self.session_id = str(uuid.uuid4())
        self.work_dir = Path(f"sessions/{self.session_id}")
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def add_dataframe(self, name: str, df: pd.DataFrame, explanation: str):
        path = self.work_dir / f"{name}.parquet"
        df.to_parquet(path)
        self.artifacts["dataframes"][name] = {
            "path": str(path),
            "explanation": explanation,
            "columns": list(df.columns),
            "shape": df.shape,
        }

    def add_image(self, name: str, path: str, explanation: str):
        self.artifacts["images"][name] = {"path": path, "explanation": explanation}
