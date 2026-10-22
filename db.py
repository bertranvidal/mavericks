"""Conexión a Supabase y helpers de base de datos."""
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_news(rows: list[dict]):
    """Inserta noticias sin duplicados (por título)."""
    return supabase.table("news").upsert(rows, on_conflict="title").execute()


def get_news(limit: int = 500):
    return supabase.table("news").select("*").order("id", desc=True).limit(limit).execute()


def get_suppliers():
    return supabase.table("suppliers").select("*").execute()


def get_materials():
    return supabase.table("materials").select("*").execute()


def get_alerts(limit: int = 100):
    return supabase.table("alerts").select("*, news(*), suppliers(*)").order("created_at", desc=True).limit(limit).execute()


def insert_alerts(rows: list[dict]):
    return supabase.table("alerts").insert(rows).execute()
