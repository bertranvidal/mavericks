# Mavericks – Playbook (2 días, 16:00–21:00, equipos de ~5, reto nuevo cada día, pitch final)

## Antes de empezar cada reto (primeros 10 min)
Preguntar / apuntar:
- ¿Qué se evalúa exactamente? (innovación, viabilidad, negocio, demo, código…)
- ¿Duración y formato del pitch? ¿Hay Q&A?
- ¿Se pueden usar APIs externas (Claude/OpenAI) o solo modelos locales? ¿Hay internet?
- ¿Nos dan datos de ejemplo? ¿Formato?
- ¿Hay que entregar código/repo o solo presentar?

## Reparto de roles (5 personas)
| Rol | Qué hace |
|---|---|
| Líder / producto | Entiende el problema, define el alcance, controla el tiempo, decide qué se recorta |
| Backend / IA | Prompts, llamada al LLM, validación (Pydantic), lógica |
| Front / demo | Interfaz Streamlit, que la demo se vea bien y no falle |
| Datos / validación | Prepara datos de ejemplo, casos de prueba, mide si la solución funciona |
| Narrativa / pitch | Slides, historia, impacto de negocio, ensayo de la presentación |

## Cronograma sugerido (5 h)
- 16:00–16:30 Entender el reto, preguntas, definir **una sola** propuesta de valor
- 16:30–17:00 Arquitectura simple + reparto de tareas (dibujo en papel)
- 17:00–19:00 Construir el MVP (algo que funcione de punta a punta, aunque sea feo)
- 19:00–19:45 Pulir demo, casos de error, datos de ejemplo buenos
- 19:45–20:30 Slides y ensayo del pitch (mínimo 2 ensayos cronometrados)
- Último tramo: presentación. **Congelar el código al menos 30 min antes.**

## Estructura del pitch (3–5 min)
1. Problema (con un caso concreto y cifras si las hay)
2. Solución en una frase
3. Demo en vivo (con plan B: vídeo o capturas por si falla)
4. Cómo funciona (esquema simple, qué parte usa IA generativa y por qué)
5. Impacto/negocio y siguientes pasos
6. Riesgos y cómo se mitigan (privacidad, alucinaciones, sesgos): suma puntos

## Reglas de oro
- Un MVP sencillo y fiable gana a algo ambicioso que se rompe.
- Usar IA generativa donde aporta de verdad; explicar por qué.
- Validar las salidas del LLM (Pydantic) y mostrar que se controlan los errores.
- Guardar todo en GitHub desde el minuto 1; commits frecuentes.
- Probar la demo en el portátil que se va a usar, con la red del sitio.

## Arrancar el starter
```
cd starter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Con API de Claude:
set LLM_PROVIDER=anthropic
set ANTHROPIC_API_KEY=tu_clave
# O con Ollama (local o en tu servidor):
set LLM_PROVIDER=ollama
set OLLAMA_HOST=http://IP_SERVIDOR:11434
set OLLAMA_MODEL=llama3.1:8b
streamlit run app.py
```
