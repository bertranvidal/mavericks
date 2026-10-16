"""Pequeño diccionario geográfico de las ciudades donde hay proveedores.

Sirve solo para dar PISTAS al LLM (una noticia sobre 'Gujarat' afecta a proveedores de Ahmedabad y Vadodara).
El LLM decide al final.
"""

# ciudad del proveedor -> otros nombres con los que puede aparecer en una noticia
CITY_ALIASES = {
    "Hyderabad": ["telangana", "andhra pradesh"],
    "Ahmedabad": ["gujarat"],
    "Vadodara": ["gujarat", "baroda"],
    "Taizhou": ["zhejiang"],
    "Hangzhou": ["zhejiang"],
    "Wuhan": ["hubei"],
    "Xi'an": ["shaanxi"],
    "Bengaluru": ["bangalore", "karnataka"],
    "Cork": ["munster"],
    "Dublin": ["leinster"],
    "Ludwigshafen": ["rhineland palatinate", "rhine"],
    "Mainz": ["rhineland palatinate", "rhine"],
    "Cologne": ["koln", "north rhine westphalia", "rhine"],
    "Darmstadt": ["hesse"],
    "Milan": ["lombardy", "northern italy"],
    "Bergamo": ["lombardy", "northern italy"],
    "Valencia": ["valencian community"],
    "Barcelona": ["catalonia"],
    "Kaohsiung": ["southern taiwan"],
    "Hsinchu": ["northern taiwan"],
    "Osaka": ["kansai"],
    "Monterrey": ["nuevo leon"],
    "Lancaster": ["pennsylvania"],
    "Boston": ["massachusetts"],
    "San Juan": ["puerto rico"],
    "Ho Chi Minh City": ["saigon", "southern vietnam"],
    "Tangier": ["northern morocco"],
    "Antwerp": ["flanders"],
}

# nombres alternativos de pais (solo pistas debiles)
COUNTRY_ALIASES = {
    "USA": ["usa", "united states", "u s"],
    "Puerto Rico (USA)": ["puerto rico"],
}


def city_aliases() -> dict:
    """Alias manuales + los generados por fetch_geo.py (data/geo_regions.json) a partir de GeoNames."""
    import json

    from .config import DATA

    out = {c: list(a) for c, a in CITY_ALIASES.items()}
    geo = DATA / "geo_regions.json"
    if geo.exists():
        for city, aliases in json.loads(geo.read_text(encoding="utf-8")).items():
            cur = out.setdefault(city, [])
            for a in aliases:
                if a not in cur:
                    cur.append(a)
    return out
