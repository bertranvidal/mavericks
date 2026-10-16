"""Capa mínima para llamar a un LLM. Cambias de proveedor con una variable de entorno.

LLM_PROVIDER = "anthropic" (API de Claude, necesita ANTHROPIC_API_KEY)
             | "ollama"    (modelo local, por defecto en http://localhost:11434;
                            si está en tu servidor: OLLAMA_HOST=http://IP_SERVIDOR:11434)
             | "openai"    (cualquier API compatible con OpenAI: Groq, OpenRouter, Gemini...;
                            necesita OPENAI_API_KEY, OPENAI_BASE_URL y OPENAI_MODEL)
"""
import json
import os
import re

import requests
from pydantic import BaseModel, ValidationError

PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")


def ask(prompt: str, system: str = "", json_schema: dict | None = None) -> str:
    """Envía un prompt y devuelve el texto de la respuesta.

    Si pasas json_schema, Ollama obliga al modelo a respetar esa estructura.
    """
    if PROVIDER == "anthropic":
        import anthropic  # pip install anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    if PROVIDER == "openai":
        # Sirve para Groq, OpenRouter, Gemini (endpoint compatible), etc.
        # Ej. Groq:   OPENAI_BASE_URL=https://api.groq.com/openai/v1
        # Ej. Gemini: OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if json_schema:
            body["response_format"] = {"type": "json_object"}
        r = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            json=body,
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": 0.2},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if json_schema:
        body["format"] = json_schema  # Ollama fuerza la salida a ese esquema
    r = requests.post(f"{OLLAMA_HOST}/api/chat", json=body, timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"]


def _template(schema: type[BaseModel]) -> str:
    """Ejemplo de la forma del JSON (los modelos pequeños se confunden si les das el esquema técnico)."""
    example = {}
    for name, prop in schema.model_json_schema().get("properties", {}).items():
        t = prop.get("type")
        example[name] = (
            ["..."] if t == "array" else 0 if t in ("integer", "number") else False if t == "boolean" else "..."
        )
    return json.dumps(example, ensure_ascii=False)


def ask_structured(prompt: str, schema: type[BaseModel], system: str = "", retries: int = 2):
    """Pide JSON, lo valida con Pydantic y reintenta si no cuadra."""
    full = (
        f"Texto a analizar:\n{prompt}\n\n"
        f"Devuelve SOLO un objeto JSON con exactamente estas claves: {_template(schema)}\n"
        "Sustituye los '...' por contenido real basado en el texto. No repitas ni describas el esquema."
    )
    last_err = None
    for _ in range(retries + 1):
        raw = ask(full, system, json_schema=schema.model_json_schema())
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        try:
            return schema.model_validate_json(match.group(0) if match else raw)
        except (ValidationError, ValueError) as e:
            last_err = e
            full += f"\n\nTu respuesta anterior fue inválida ({e}). Corrígela."
    raise RuntimeError(f"No se obtuvo JSON válido: {last_err}")
