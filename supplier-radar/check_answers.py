"""Comprueba las predicciones del modelo contra el Answer Key oficial.

  python3 check_answers.py --mode rules           # comprobar baseline
  python3 check_answers.py --mode models           # comprobar modelos entrenados
  python3 check_answers.py --mode rules --live     # comprobar Live Day feed
"""
import argparse

import pandas as pd

from radar.config import DATA, LIVE, TEST
from radar.data import load_news, load_suppliers
from radar.impact import ids_of
from radar.pipeline import analyze_news, load_pool


def load_answer_key(live: bool = False) -> pd.DataFrame:
    """Carga las respuestas correctas del Answer Key."""
    path = DATA / "Copy of Supplier_Risk_Answer_Key 1.xlsx"
    if live:
        df = pd.read_excel(path, sheet_name="LiveDay_Answer_Key")
    else:
        df = pd.read_excel(path, sheet_name="Answer_Key")
        df = df[df["Split"] == "Test"]
    return df


def compare(pred: pd.DataFrame, answers: pd.DataFrame):
    """Compara predicciones con respuestas correctas."""
    pred_idx = pred.set_index("News_ID")
    ans_idx = answers.set_index("News_ID")

    common = sorted(set(pred_idx.index) & set(ans_idx.index))
    if not common:
        print("  No hay noticias en comun entre predicciones y respuestas.")
        return

    ok_risk = ok_urg = tp = fp = fn = 0
    errors = []

    for nid in common:
        p = pred_idx.loc[nid]
        a = ans_idx.loc[nid]

        p_risk = p["Is_Risk"] if isinstance(p["Is_Risk"], str) else str(p["Is_Risk"])
        a_risk = a["Is_Risk"] if isinstance(a["Is_Risk"], str) else str(a["Is_Risk"])
        p_urg = p["Urgent"] if isinstance(p["Urgent"], str) else str(p["Urgent"])
        a_urg = a["Urgent"] if isinstance(a["Urgent"], str) else str(a["Urgent"])

        risk_ok = p_risk == a_risk
        urg_ok = p_urg == a_urg
        ok_risk += risk_ok
        ok_urg += urg_ok

        p_sups = set(ids_of(p.get("Affected_Supplier_IDs", "")))
        a_sups = set(ids_of(a.get("Affected_Supplier_IDs", "")))
        tp += len(p_sups & a_sups)
        fp += len(p_sups - a_sups)
        fn += len(a_sups - p_sups)

        if not risk_ok or not urg_ok or p_sups != a_sups:
            errors.append({
                "id": nid,
                "headline": a.get("Headline", ""),
                "expected_risk": a_risk,
                "got_risk": p_risk,
                "expected_urg": a_urg,
                "got_urg": p_urg,
                "expected_sups": "; ".join(sorted(a_sups)),
                "got_sups": "; ".join(sorted(p_sups)),
            })

    n = len(common)
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0

    print(f"\n  Noticias evaluadas: {n}")
    print(f"  Is_Risk accuracy:  {ok_risk}/{n} = {ok_risk/n:.0%}")
    print(f"  Urgent accuracy:   {ok_urg}/{n} = {ok_urg/n:.0%}")
    print(f"  Suppliers:         precision {prec:.0%}  recall {rec:.0%}  F1 {f1:.0%}")

    if errors:
        print(f"\n  --- ERRORES ({len(errors)}) ---")
        for e in errors:
            print(f"  {e['id']}: {e['headline'][:70]}")
            if e["expected_risk"] != e["got_risk"]:
                print(f"    Risk: esperado={e['expected_risk']} obtenido={e['got_risk']}")
            if e["expected_urg"] != e["got_urg"]:
                print(f"    Urgent: esperado={e['expected_urg']} obtenido={e['got_urg']}")
            if e["expected_sups"] != e["got_sups"]:
                print(f"    Suppliers: esperado={e['expected_sups']} obtenido={e['got_sups']}")
    else:
        print("\n  Sin errores.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["rules", "models"], default="rules")
    parser.add_argument("--live", action="store_true", help="comprobar Live Day feed")
    args = parser.parse_args()

    if args.live:
        print("=== Comprobacion: Live Day Feed ===")
        news = load_news(LIVE)
    else:
        print("=== Comprobacion: Test ===")
        news = load_news(TEST)

    pool = load_pool(include_valid=True)
    print(f"  Analizando {len(news)} noticias con modo '{args.mode}'...")
    results = analyze_news(news, pool, mode=args.mode)

    answers = load_answer_key(live=args.live)
    print(f"  Answer Key: {len(answers)} respuestas")

    compare(results, answers)


if __name__ == "__main__":
    main()
