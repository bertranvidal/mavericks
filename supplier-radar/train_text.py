"""Afina NUESTRO modelo de texto (riesgo, urgencia, tipo de evento) desde un encoder preentrenado.

  python3 train_text.py                       # entrena con sinteticas + train real; mide en validacion
  python3 train_text.py --with-val            # version final: incluye validacion (ya no se puede medir en ella)
  python3 train_text.py --base FacebookAI/roberta-base --epochs 5
"""
import argparse
import random

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from radar.config import MODELS, TRAIN, VALID
from radar.data import load_news
from radar.nn import MultiHead
from radar.schema import EVENT_TYPES
from radar.synth import load_synth


def encode_labels(df: pd.DataFrame, events: list[str]):
    ev = df["Event_Type"].map(lambda e: events.index(e) if e in events else events.index("Other risk")).values
    return (df["Is_Risk"].eq("Y").astype(int).values, df["Urgent"].eq("Y").astype(int).values, ev)


def batches(texts, labels, tok, bs, dev, shuffle):
    idx = list(range(len(texts)))
    if shuffle:
        random.shuffle(idx)
    for i in range(0, len(idx), bs):
        j = idx[i:i + bs]
        enc = tok([texts[k] for k in j], truncation=True, max_length=192, padding=True, return_tensors="pt").to(dev)
        yield enc, [torch.tensor(l[j], device=dev) for l in labels]


def predict(model, tok, texts, dev):
    model.eval()
    out = [[], [], []]
    with torch.no_grad():
        for enc, _ in batches(texts, [np.zeros(len(texts))], tok, 32, dev, False):
            for o, lg in zip(out, model(enc["input_ids"], enc["attention_mask"])):
                o.append(lg.float().argmax(-1).cpu().numpy())
    return [np.concatenate(o) for o in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="FacebookAI/roberta-base")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--real-weight", type=int, default=6, help="cuantas veces se repite cada noticia real")
    ap.add_argument("--with-val", action="store_true")
    ap.add_argument("--out", default=str(MODELS / "text_clf"))
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    events = list(EVENT_TYPES)

    real = load_news(TRAIN)
    val = load_news(VALID)
    if a.with_val:
        real = pd.concat([real, val], ignore_index=True)
    synth = load_synth()
    train = pd.concat([synth] + [real] * a.real_weight, ignore_index=True)
    print(f"entrenamiento: {len(synth)} sinteticas + {len(real)} reales x{a.real_weight} = {len(train)}", flush=True)

    tok = AutoTokenizer.from_pretrained(a.base)
    model = MultiHead.new(a.base, len(events)).to(dev)
    texts = train["text"].tolist()
    labels = list(encode_labels(train, events))
    steps = a.epochs * ((len(texts) + a.bs - 1) // a.bs)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    sch = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
    use_bf16 = dev == "cuda"

    for ep in range(a.epochs):
        model.train()
        tot = n = 0
        for enc, (yr, yu, ye) in batches(texts, labels, tok, a.bs, dev, True):
            with torch.autocast(device_type=dev, dtype=torch.bfloat16, enabled=use_bf16):
                lr_, lu_, le_ = model(enc["input_ids"], enc["attention_mask"])
            lr_, lu_, le_ = lr_.float(), lu_.float(), le_.float()
            loss = F.cross_entropy(lr_, yr) + F.cross_entropy(le_, ye)
            m = yr == 1  # la urgencia solo se aprende en noticias que son riesgo
            if m.any():
                loss = loss + F.cross_entropy(lu_[m], yu[m])
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sch.step()
            tot += float(loss) * len(yr)
            n += len(yr)
        print(f"epoca {ep + 1}/{a.epochs}  loss {tot / n:.4f}", flush=True)

    if not a.with_val:
        pr, pu, pe = predict(model, tok, val["text"].tolist(), dev)
        yr, yu, ye = encode_labels(val, events)
        print("\n== VALIDACION REAL (10 noticias) ==")
        print(f"Is_Risk {np.mean(pr == yr):.0%}   Urgent(en cabeza) {np.mean(pu == yu):.0%}   Evento {np.mean(pe == ye):.0%}")
    model.save(a.out, tok, events, a.base)
    print("guardado en", a.out)


if __name__ == "__main__":
    main()
