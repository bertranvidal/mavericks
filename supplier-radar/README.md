# Supplier Risk Radar (modelos propios)

Noticia -> pistas de proveedor (matcher con alias y geografia) -> 2 modelos afinados por nosotros (ensemble) -> reglas -> Is_Risk / Urgent / Affected_Supplier_IDs + capa de impacto en negocio.

Modelos (preentrenados + fine-tuning nuestro, pesos abiertos, sin pago por uso):
1. `train_text.py`  -> modelo de texto con 5 cabezas: riesgo, urgencia, tipo de evento, impacto en suministro y duracion. Base: roberta-base.
2. `train_link.py`  -> cross-encoder noticia-proveedor. Base: bge-reranker-base.
Cada uno se entrena con 3 semillas y se promedia (ensemble). Los umbrales se calibran con `calibrate.py`.

Datos de entrenamiento: noticias reales de train (+ validation en la version final), sinteticas por plantillas (`radar/synth.py`)
y parafrasis por retrotraduccion (`augment.py`). Regiones y ciudades: `fetch_geo.py` (GeoNames).

Honestidad en la medida: las plantillas sinteticas se escribieron viendo train Y validation, asi que validation ya no es una medida limpia.
La medida limpia es el examen independiente `data/Supplier_Risk_Holdout.xlsx` (escrito por el equipo, plantilla en `data/Supplier_Risk_Holdout_TEMPLATE.xlsx`).
Nunca se usa el test, el feed del directo ni el archivo de respuestas.

## Comandos en el DGX (carpeta supplier-radar)

    git pull
    pip3 install --user -r requirements.txt
    python3 fetch_geo.py                     # 1 vez: regiones desde GeoNames -> data/geo_regions.json
    python3 -m radar.synth --n 3000          # datos sinteticos -> data/synthetic.csv
    python3 augment.py                       # parafrasis -> data/aug_*.csv (tarda unos minutos)
    bash train_all.sh                        # 3 modelos de texto + 3 de vinculacion
    python3 evaluate.py --data holdout       # examen independiente (cuando exista el fichero)
    python3 calibrate.py                     # umbrales -> models/thresholds.json
    python3 -m streamlit run dashboard.py --server.port 8501 --server.headless true --server.enableCORS false --server.enableXsrfProtection false

Version final (despues de decidir hiperparametros y umbrales):

    bash train_all.sh --with-val
    python3 run.py data/Supplier_Risk_3_Test.xlsx
    python3 run.py                           # Live Day feed

Los pesos quedan en `models/` (no se suben a git; se entrenan en el DGX).
Linea base sin modelos: `--mode rules`. Opcional y desactivado: `--mode llm` (Ollama).

## Alerta final con IA generativa

Los modelos propios deciden; una IA generativa local solo REDACTA la alerta con sus resultados (titulo, resumen, por que importa,
siguientes pasos y borrador de email al proveedor). Salida validada contra los hechos (sin IDs ni cifras inventadas) y plantilla
de respaldo si el LLM no responde.

    ollama list                                  # ver modelos instalados; se elige uno automaticamente (o ALERT_MODEL=...)
    python3 run.py --alerts --lang en            # alertas en la hoja Details (Results sigue con las 4 columnas)
    # el panel trae la casilla "Redactar alertas con IA generativa"
