"""Procesa un Excel de noticias SIN tocar el fichero ni el codigo y exporta una fila por noticia.

  python3 run.py                                           # Live Day feed por defecto
  python3 run.py data/Supplier_Risk_3_Test.xlsx
  python3 run.py data/Supplier_Risk_LiveDay_Feed.xlsx --out out/live_result.xlsx
"""
import argparse
from pathlib import Path

from radar.config import LIVE, OUT
from radar.data import load_news
from radar.pipeline import analyze_news, load_pool, save_excel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default=str(LIVE))
    ap.add_argument("--out", default=None)
    ap.add_argument("--mode", default="models", choices=["models", "rules", "llm"])
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--alerts", action="store_true", help="redacta una alerta por riesgo con IA generativa local (hoja Details)")
    ap.add_argument("--lang", default="en", choices=["en", "es"])
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args()

    news = load_news(a.file)
    pool = load_pool(include_valid=True)  # train + validation como ejemplos; nunca test ni live
    res = analyze_news(news, pool, a.mode, alerts=a.alerts, alert_lang=a.lang, workers=a.workers, use_cache=not a.no_cache)

    OUT.mkdir(exist_ok=True)
    out = Path(a.out) if a.out else OUT / (Path(a.file).stem + "_result.xlsx")
    save_excel(res, out)
    print("Excel escrito en", out)
    if a.alerts:
        print(f"Alertas redactadas en {res.attrs.get('alert_seconds', 0):.1f} s")
    print(res[["News_ID", "Is_Risk", "Urgent", "Affected_Supplier_IDs"]].to_string(index=False))


if __name__ == "__main__":
    main()
