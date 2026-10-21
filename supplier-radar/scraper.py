"""News scraper for Supplier Risk Radar.

Fetches supply-chain-relevant news from RSS feeds (international + Spanish national)
and optionally NewsAPI. Deduplicates by title hash and inserts into Supabase.

  python3 scraper.py                     # scrape all sources
  python3 scraper.py --dry-run           # print without saving
  python3 scraper.py --source rss        # only RSS feeds
  python3 scraper.py --source newsapi    # only NewsAPI
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")

RSS_FEEDS = [
    # ── International business & supply chain ──
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.ft.com/?format=rss",
    "https://www.supplychaindive.com/feeds/news/",
    "https://www.pharmaceutical-technology.com/feed/",
    "https://www.chemistryworld.com/rss/news.xml",
    "https://www.scmp.com/rss/4/feed",

    # ── International world news (disasters, geopolitics) ──
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",

    # ── Spain: El País ──
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/ciencia/portada",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/sociedad/portada",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",

    # ── Spain: El Mundo ──
    "https://e00-elmundo.uecdn.es/elmundo/rss/economia.xml",
    "https://e00-elmundo.uecdn.es/elmundo/rss/ciencia.xml",
    "https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml",
    "https://e00-elmundo.uecdn.es/elmundo/rss/espana.xml",

    # ── Spain: Expansión (business) ──
    "https://e00-expansion.uecdn.es/rss/economia.xml",
    "https://e00-expansion.uecdn.es/rss/empresas.xml",

    # ── Spain: OKDiario ──
    "https://okdiario.com/economia/feed",
    "https://okdiario.com/ciencia/feed",
    "https://okdiario.com/internacional/feed",

    # ── Spain: ABC ──
    "https://www.abc.es/rss/feeds/abc_Economia.xml",
    "https://www.abc.es/rss/feeds/abc_Internacional.xml",
    "https://www.abc.es/rss/feeds/abc_Ciencia.xml",

    # ── Spain: La Razón ──
    "https://www.larazon.es/rss/economia.xml",
    "https://www.larazon.es/rss/ciencia.xml",

    # ── Spain: RTVE ──
    "https://www.rtve.es/rss/economia.xml",

    # ── Spain: EFE (Spanish news agency) ──
    "https://www.efe.com/rss/economia",
    "https://www.efe.com/rss/ciencia",

    # ── Science & tech ──
    "https://www.nature.com/nature.rss",
    "https://www.science.org/rss/news_current.xml",
    "https://www.newscientist.com/feed/home/",

    # ── Pharma specific ──
    "https://www.europeanpharmaceuticalreview.com/feed/",
    "https://www.in-pharmatechnologist.com/rss/news",
    "https://www.pharmamanufacturing.com/rss/",
]

# Keywords in English and Spanish for filtering
KEYWORDS_EN = [
    "supply chain", "supplier", "shortage", "disruption", "logistics",
    "procurement", "manufacturing", "factory", "plant", "warehouse",
    "fire", "explosion", "flood", "earthquake", "hurricane", "typhoon",
    "strike", "protest", "sanction", "embargo", "recall", "contamination",
    "shutdown", "closure", "bankruptcy", "insolvency", "cyber attack",
    "pharmaceutical", "drug", "medicine", "API", "active ingredient",
    "excipient", "packaging", "GMP", "FDA", "EMA", "regulatory",
    "shipping", "freight", "port", "container", "tariff", "export ban",
    "import restriction", "trade war",
]

KEYWORDS_ES = [
    "cadena de suministro", "proveedor", "escasez", "desabastecimiento",
    "logística", "fabricación", "fábrica", "planta", "almacén",
    "incendio", "explosión", "inundación", "terremoto", "huracán",
    "huelga", "protesta", "sanción", "embargo", "retirada", "contaminación",
    "cierre", "quiebra", "ciberataque", "ransomware",
    "farmacéutica", "medicamento", "principio activo", "excipiente",
    "envase", "regulación", "AEMPS", "EMA",
    "transporte", "puerto", "contenedor", "arancel", "restricción",
    "importación", "exportación", "guerra comercial",
    "suministro", "distribución", "materia prima", "laboratorio",
]

ALL_KEYWORDS = KEYWORDS_EN + KEYWORDS_ES
KEYWORD_PATTERN = re.compile("|".join(re.escape(k) for k in ALL_KEYWORDS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def title_hash(title: str) -> str:
    return hashlib.sha256(title.strip().lower().encode()).hexdigest()[:16]


def is_relevant(title: str, summary: str = "") -> bool:
    return bool(KEYWORD_PATTERN.search(f"{title} {summary}"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# RSS scraping
# ---------------------------------------------------------------------------

def fetch_rss(url: str, timeout: int = 15) -> list[dict]:
    articles = []
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "SupplierRadar/1.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for item in items:
            title = (item.findtext("title") or item.findtext("atom:title", namespaces=ns) or "").strip()
            summary = (item.findtext("description") or item.findtext("atom:summary", namespaces=ns) or "").strip()
            link = (item.findtext("link") or "").strip()
            # Handle Atom links
            if not link:
                link_el = item.find("atom:link[@href]", ns)
                if link_el is not None:
                    link = link_el.get("href", "")
            pub_date = (item.findtext("pubDate") or item.findtext("atom:updated", namespaces=ns) or "").strip()

            summary = re.sub(r"<[^>]+>", "", summary).strip()
            if not title:
                continue
            if is_relevant(title, summary):
                articles.append({
                    "title": title[:500],
                    "summary": summary[:2000],
                    "url": link[:1000],
                    "source": url.split("/")[2],
                    "published_at": pub_date or now_iso(),
                    "scraped_at": now_iso(),
                    "title_hash": title_hash(title),
                    "is_labeled": False,
                    "is_risk": None,
                    "urgent": None,
                    "event_type": None,
                    "affected_supplier_ids": None,
                })
    except Exception as e:
        print(f"  [WARN] {url.split('/')[2]}: {type(e).__name__}")
    return articles


def scrape_rss() -> list[dict]:
    all_articles = []
    seen: set[str] = set()
    for url in RSS_FEEDS:
        arts = fetch_rss(url)
        new = 0
        for a in arts:
            if a["title_hash"] not in seen:
                seen.add(a["title_hash"])
                all_articles.append(a)
                new += 1
        if new:
            print(f"  {url.split('/')[2]:40s} +{new}")
    return all_articles


# ---------------------------------------------------------------------------
# NewsAPI
# ---------------------------------------------------------------------------

def scrape_newsapi() -> list[dict]:
    if not NEWSAPI_KEY:
        print("  [SKIP] NEWSAPI_KEY not set")
        return []

    articles = []
    queries = [
        "pharmaceutical supply chain disruption",
        "supplier factory fire recall",
        "drug shortage manufacturing",
        "export restriction sanctions pharma",
        "logistics port strike shipping",
        "cadena suministro farmacéutica",
        "desabastecimiento medicamentos",
    ]

    for q in queries:
        try:
            r = requests.get("https://newsapi.org/v2/everything",
                params={"q": q, "language": "en", "sortBy": "publishedAt", "pageSize": 20, "apiKey": NEWSAPI_KEY},
                timeout=15)
            for item in r.json().get("articles", []):
                title = (item.get("title") or "").strip()
                summary = (item.get("description") or "").strip()
                if title and is_relevant(title, summary):
                    articles.append({
                        "title": title[:500],
                        "summary": summary[:2000],
                        "url": (item.get("url") or "")[:1000],
                        "source": item.get("source", {}).get("name", "newsapi"),
                        "published_at": item.get("publishedAt") or now_iso(),
                        "scraped_at": now_iso(),
                        "title_hash": title_hash(title),
                        "is_labeled": False, "is_risk": None, "urgent": None,
                        "event_type": None, "affected_supplier_ids": None,
                    })
        except Exception as e:
            print(f"  [WARN] NewsAPI '{q[:30]}': {type(e).__name__}")

    seen: set[str] = set()
    return [a for a in articles if not (a["title_hash"] in seen or seen.add(a["title_hash"]))]


# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------

def save_to_supabase(articles: list[dict]) -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] SUPABASE_URL / SUPABASE_KEY not set")
        return 0

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    inserted = 0
    for i in range(0, len(articles), 50):
        batch = articles[i:i + 50]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/scraped_news?on_conflict=title_hash",
            headers=headers, json=batch,
        )
        if r.status_code in (200, 201):
            inserted += len(batch)
        elif r.status_code == 409:
            # Some duplicates in batch — insert one by one
            for a in batch:
                r2 = requests.post(
                    f"{SUPABASE_URL}/rest/v1/scraped_news?on_conflict=title_hash",
                    headers=headers, json=[a],
                )
                if r2.status_code in (200, 201):
                    inserted += 1
        else:
            print(f"  [ERROR] batch {i}: {r.status_code} {r.text[:200]}")
    return inserted


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source", choices=["rss", "newsapi", "all"], default="all")
    args = parser.parse_args()

    print(f"[{now_iso()}] Supplier Radar Scraper")
    articles: list[dict] = []

    if args.source in ("rss", "all"):
        print("\n--- RSS feeds ---")
        articles.extend(scrape_rss())

    if args.source in ("newsapi", "all"):
        print("\n--- NewsAPI ---")
        articles.extend(scrape_newsapi())

    # Final dedup
    seen: set[str] = set()
    unique = [a for a in articles if not (a["title_hash"] in seen or seen.add(a["title_hash"]))]
    print(f"\nTotal unique relevant articles: {len(unique)}")

    if args.dry_run:
        for a in unique[:15]:
            print(f"  [{a['source']:30s}] {a['title'][:90]}")
        if len(unique) > 15:
            print(f"  ... +{len(unique) - 15} more")
        return

    if unique:
        n = save_to_supabase(unique)
        print(f"Saved {n} articles to Supabase")
    else:
        print("No new articles.")


if __name__ == "__main__":
    main()
