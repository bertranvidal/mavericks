import pandas as pd

from .config import DATA, TRAIN


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


EXTRA_FILES = ["aug_synth.csv", "llm_synth.csv", "neg_news.csv"]  # datos extra opcionales (augment / gen_llm_data / fetch_negatives)


def load_extra() -> list[tuple[str, pd.DataFrame]]:
    """Ficheros de entrenamiento extra que existan en data/. Todos con etiquetas por construccion."""
    out = []
    for name in EXTRA_FILES:
        f = DATA / name
        if f.exists():
            df = pd.read_csv(f)
            for c in ("Summary", "Affected_Supplier_IDs"):
                df[c] = df[c].fillna("")
            out.append((name, df))
    return out
