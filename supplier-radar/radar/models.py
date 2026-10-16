"""Inferencia con NUESTROS modelos afinados (texto + vinculacion). Se cargan una sola vez."""
import os
from pathlib import Path

from .config import MODELS

_cache = {}


class Models:
    def __init__(self, text_dir: Path, link_dir: Path):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        from .nn import MultiHead

        for d in (text_dir, link_dir):
            if not (Path(d) / "meta.json").exists() and not (Path(d) / "config.json").exists():
                raise FileNotFoundError(
                    f"Falta el modelo en {d}. Entrena primero: python3 train_text.py y python3 train_link.py")
        self.torch = torch
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.text, self.ttok, self.events = MultiHead.load(text_dir)
        self.text.to(self.dev)
        self.link = AutoModelForSequenceClassification.from_pretrained(link_dir).eval().to(self.dev)
        self.ltok = AutoTokenizer.from_pretrained(link_dir)

    def predict_text(self, texts: list[str]) -> list[dict]:
        torch = self.torch
        enc = self.ttok(texts, truncation=True, max_length=192, padding=True, return_tensors="pt").to(self.dev)
        with torch.no_grad():
            r, u, e = self.text(enc["input_ids"], enc["attention_mask"])
        pr, pu, pe = r.softmax(-1)[:, 1], u.softmax(-1)[:, 1], e.softmax(-1)
        return [{"p_risk": float(pr[i]), "p_urgent": float(pu[i]), "event": self.events[int(pe[i].argmax())]}
                for i in range(len(texts))]

    def score_links(self, text: str, bs: list[str], chunk: int = 64) -> list[float]:
        torch = self.torch
        out = []
        for i in range(0, len(bs), chunk):
            part = bs[i:i + chunk]
            enc = self.ltok([text] * len(part), part, truncation="only_first", max_length=256,
                            padding=True, return_tensors="pt").to(self.dev)
            with torch.no_grad():
                logits = self.link(**enc).logits.squeeze(-1)
            out += torch.sigmoid(logits).float().cpu().tolist()
        return out


def get_models() -> Models:
    if "m" not in _cache:
        _cache["m"] = Models(Path(os.getenv("RADAR_TEXT_MODEL", MODELS / "text_clf")),
                             Path(os.getenv("RADAR_LINK_MODEL", MODELS / "link")))
    return _cache["m"]
