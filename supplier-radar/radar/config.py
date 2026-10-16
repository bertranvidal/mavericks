from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"
CACHE = OUT / "cache"
MODELS = ROOT / "models"   # pesos afinados (no se suben a git)

TRAIN = DATA / "Supplier_Risk_1_Training.xlsx"   # trae Suppliers, Materials y 30 noticias con respuesta
VALID = DATA / "Supplier_Risk_2_Validation.xlsx"  # 10 noticias con respuesta (solo para medir)
TEST = DATA / "Supplier_Risk_3_Test.xlsx"         # 20 noticias sin respuesta
HOLDOUT = DATA / "Supplier_Risk_Holdout.xlsx"       # examen independiente escrito por el equipo (con respuesta)
LIVE = DATA / "Supplier_Risk_LiveDay_Feed.xlsx"   # noticias del dia de la presentacion

DATASETS = {"train": TRAIN, "val": VALID, "holdout": HOLDOUT, "test": TEST, "live": LIVE}
