# Guía de arranque – Mavericks

Repo: https://github.com/bertranvidal/mavericks

## A) En el DGX (code-server) – opción principal

1. Entra al portal del DGX, lanza una sesión **con GPU** (perfil Estudiante, 1 instancia de 16 GiB) y abre code-server. La sesión dura 8 h; si caduca, hay que lanzar otra.
2. Abre un terminal (Ctrl + `) y ejecuta:

```bash
cd ~/mavericks
git pull
```

3. Comprueba que Ollama responde y que están los modelos:

```bash
curl -s http://localhost:11434/api/version; echo
ollama list
```

Si no responde (no hay servidor), arranca el tuyo:

```bash
export PATH=$HOME/ollama/bin:$PATH
nohup ollama serve > ~/ollama/serve.log 2>&1 &
sleep 5
ollama pull qwen2.5:7b-instruct-q4_K_M   # solo si no está descargado
```

4. Lanza la app (no hay entorno virtual que activar en el DGX):

```bash
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
python3 -m streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false --server.enableXsrfProtection false
```

5. Abre la pestaña **PORTS**, busca el 8501 y pulsa el globo. Si no aparece, añade `/proxy/8501/` a la dirección del code-server.

Modelo mejor y algo más lento: `export OLLAMA_MODEL=qwen2.5:14b-instruct-q4_K_M`

Si faltan paquetes: `pip3 install --user -r requirements.txt`

## B) En el portátil (plan B, sin GPU, más lento)

En el terminal de VS Code, carpeta `C:\dev\mavericks`:

```powershell
cd C:\dev\mavericks
.venv\Scripts\Activate.ps1
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_MODEL="qwen2.5:3b"
streamlit run app.py
```

- Debe aparecer `(.venv)` al principio de la línea.
- Si da error de permisos: `Set-ExecutionPolicy -Scope Process Bypass` y repite la activación.
- Ollama de Windows arranca solo (icono en la bandeja). Comprueba con `ollama list`.
- Abre http://localhost:8501

## C) Guardar el trabajo en GitHub

```
git add .
git status --short      # no debe salir .venv
git commit -m "mensaje"
git push
```

## D) Si algo falla

| Síntoma | Causa probable |
|---|---|
| Error 404 en /api/chat | El modelo de `OLLAMA_MODEL` no está descargado (`ollama list`) |
| `Connection refused` | Ollama no está arrancado |
| La app tarda minutos | Estás usando CPU (portátil) o un modelo grande |
| JSON inválido en modo estructurado | Reintenta; prueba el modelo 7B/14B del DGX |
| `llm.py` raro tras tocar el repo | Haz `git pull` y reinicia Streamlit (no recarga `llm.py` solo) |
