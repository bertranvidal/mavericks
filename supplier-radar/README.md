# Supplier Risk Radar (modelos propios)

Noticia -> pistas de proveedor (NER ligero) -> 2 modelos afinados por nosotros -> reglas -> Is_Risk / Urgent / Affected_Supplier_IDs.

Modelos (preentrenados + fine-tuning nuestro):
1. `train_text.py`  -> modelo de texto con 3 salidas (riesgo, urgencia, tipo de evento). Base: roberta-base.
2. `train_link.py`  -> cross-encoder noticia-proveedor. Base: bge-reranker-base.

Datos de entrenamiento: noticias reales de train (+ validation en la version final) y noticias sinteticas por plantillas (`python3 -m radar.synth`).
La medida de acierto es SIEMPRE la validacion real. Nunca se usa el test, el feed del directo ni el archivo de respuestas.

## Comandos en el DGX (carpeta supplier-radar)

    git pull
    pip3 install --user -r requirements.txt
    python3 -m radar.synth --n 1500          # datos sinteticos (ya vienen en data/synthetic.csv)
    python3 train_text.py                    # entrena y mide en validacion real
    python3 train_link.py                    # entrena y mide en validacion real
    python3 evaluate.py --data val           # pipeline completo contra validacion

Version final (despues de decidir hiperparametros):

    python3 train_text.py --with-val
    python3 train_link.py --with-val
    python3 run.py data/Supplier_Risk_3_Test.xlsx
    python3 run.py                           # Live Day feed

Los pesos quedan en `models/` (no se suben a git; se entrenan en el DGX).
Linea base sin modelos: `--mode rules`. Opcional y desactivado: `--mode llm` (Ollama).
