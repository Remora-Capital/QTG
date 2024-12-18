import pandas as pd
import numpy as np


def get_log(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(lambda x: np.sign(x) * np.log(abs(x)+1) if np.issubdtype(type(x), np.number) else x)

def get_log_col(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col].apply(lambda x: np.sign(x) * np.log(abs(x)+1) if np.issubdtype(type(x), np.number) else x)