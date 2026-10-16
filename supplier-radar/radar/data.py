import pandas as pd

from .config import TRAIN


def load_suppliers() -> pd.DataFrame:
    return pd.read_excel(TRAIN, sheet_name="Suppliers")


def load_materials() -> pd.DataFrame:
    return pd.read_excel(TRAIN, sheet_name="Materials")


def load_news(path) -> pd.DataFrame:
    """Lee la hoja de noticias de cualquiera de los 4 Excel (News, News_Validation, News_Test, News_Feed)."""
    xl = pd.ExcelFile(path)
    sheet = next(s for s in xl.sheet_names if s.lower().startswith("news"))
    df = xl.parse(sheet)
    df["Headline"] = df["Headline"].fillna("").astype(str)
    df["Summary"] = df["Summary"].fillna("").astype(str)
    df["text"] = df["Headline"] + ". " + df["Summary"]
    return df


def is_labelled(df: pd.DataFrame) -> bool:
    return "Is_Risk" in df.columns and df["Is_Risk"].notna().all()
