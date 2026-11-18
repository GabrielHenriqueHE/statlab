FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# versão fixa do uv (a mesma usada no desenvolvimento; o build backend exige uv_build < 0.14)
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

WORKDIR /app

# dependências primeiro (camada reaproveitada enquanto o uv.lock não mudar)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

# DESATUALIZADO: daqui para baixo é o app Streamlit, que não existe mais (o statlab virou um app de
# desktop em Qt). Rodar em contêiner exige expor o servidor gráfico (X11/Wayland) — ainda a decidir.
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["uv", "run", "--no-sync", "streamlit", "run", "src/statlab/ui/app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
