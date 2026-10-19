"""FastAPI backend for Supplier Radar dashboard."""

from __future__ import annotations

import io
from collections import Counter
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from radar import config, data as radar_data, impact, pipeline

app = FastAPI(title="Supplier Radar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for last analysis results
_last_results: pd.DataFrame | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _df_to_records(df: pd.DataFrame) -> list[dict]:
    return df.where(pd.notnull(df), None).to_dict(orient="records")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    source: str  # "live" | "test" | "validation"
    mode: str    # "rules" | "models"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/suppliers")
def get_suppliers() -> list[dict]:
    df = radar_data.load_suppliers()
    return _df_to_records(df)


@app.get("/api/materials")
def get_materials() -> list[dict]:
    df = radar_data.load_materials()
    return _df_to_records(df)


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> list[dict]:
    global _last_results

    source_map = {
        "live": config.LIVE,
        "test": config.TEST,
        "validation": config.VALID,
    }
    if req.source not in source_map:
        raise HTTPException(status_code=400, detail=f"Unknown source '{req.source}'. Use live, test, or validation.")
    if req.mode not in ("rules", "models"):
        raise HTTPException(status_code=400, detail=f"Unknown mode '{req.mode}'. Use rules or models.")

    path = source_map[req.source]
    news_df = radar_data.load_news(path)
    pool_df = pipeline.load_pool(include_valid=True)
    results = pipeline.analyze_news(news_df, pool_df, mode=req.mode)

    _last_results = results
    return _df_to_records(results)


@app.get("/api/results")
def get_results() -> list[dict]:
    if _last_results is None:
        raise HTTPException(status_code=404, detail="No analysis has been run yet.")
    return _df_to_records(_last_results)


@app.get("/api/kpis")
def get_kpis() -> dict[str, Any]:
    if _last_results is None:
        raise HTTPException(status_code=404, detail="No analysis has been run yet.")

    df = _last_results.copy()

    # Normalise Is_Risk to uppercase string for comparison
    df["_is_risk"] = df["Is_Risk"].astype(str).str.upper().str.strip()

    risk_df = df[df["_is_risk"] == "Y"]

    total_alerts = int(risk_df["News_ID"].nunique())
    critical_alerts = int(
        risk_df[risk_df["Priority"].astype(str).str.upper() == "CRITICAL"]["News_ID"].nunique()
    )

    # Collect all affected supplier IDs from risk rows
    all_affected: list[str] = []
    for cell in risk_df["Affected_Supplier_IDs"]:
        all_affected.extend(impact.ids_of(cell))

    suppliers_at_risk = len(set(all_affected))

    # Cross-reference with suppliers table to get countries
    suppliers_df = radar_data.load_suppliers()
    affected_set = set(all_affected)
    affected_suppliers = suppliers_df[suppliers_df["Supplier_ID"].astype(str).isin(affected_set)]
    countries_affected = int(affected_suppliers["Country"].nunique())

    # Most exposed supplier
    most_exposed: dict[str, Any] = {}
    if all_affected:
        top_id, top_count = Counter(all_affected).most_common(1)[0]
        row = suppliers_df[suppliers_df["Supplier_ID"].astype(str) == top_id]
        if not row.empty:
            r = row.iloc[0]
            most_exposed = {
                "id": top_id,
                "name": r.get("Supplier_Name", ""),
                "country": r.get("Country", ""),
                "alert_count": top_count,
            }
        else:
            most_exposed = {"id": top_id, "name": "", "country": "", "alert_count": top_count}

    return {
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "suppliers_at_risk": suppliers_at_risk,
        "countries_affected": countries_affected,
        "most_exposed_supplier": most_exposed,
    }


@app.get("/api/alternatives/{supplier_id}")
def get_alternatives(supplier_id: str) -> list[dict]:
    suppliers_df = radar_data.load_suppliers()
    materials_df = radar_data.load_materials()

    # Find materials where this supplier is the primary
    primary_materials = materials_df[
        materials_df["Primary_Supplier_ID"].astype(str) == supplier_id
    ]

    results = []
    for _, mat_row in primary_materials.iterrows():
        alt_id = str(mat_row.get("Alternate_Supplier_ID", "")) if pd.notna(mat_row.get("Alternate_Supplier_ID")) else None
        alt_name = mat_row.get("Alternate_Supplier_Name", "")

        alt_details: dict[str, Any] = {}
        if alt_id:
            alt_sup = suppliers_df[suppliers_df["Supplier_ID"].astype(str) == alt_id]
            if not alt_sup.empty:
                alt_details = alt_sup.iloc[0].where(pd.notnull(alt_sup.iloc[0]), None).to_dict()

        results.append({
            "material_id": mat_row.get("Material_ID"),
            "material": mat_row.get("Material"),
            "alternate_supplier_id": alt_id,
            "alternate_supplier_name": alt_name,
            "alternate_supplier_details": alt_details,
        })

    return results


@app.get("/api/export")
def export_results() -> StreamingResponse:
    if _last_results is None:
        raise HTTPException(status_code=404, detail="No analysis has been run yet.")

    buf = io.BytesIO()
    pipeline.save_excel(_last_results, buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=supplier_radar_results.xlsx"},
    )
