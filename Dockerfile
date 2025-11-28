FROM python:3.9-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN echo '#!/bin/sh' > /app/run.sh && \
    echo 'streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0' >> /app/run.sh && \
    chmod +x /app/run.sh

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:$PORT/_stcore/health || exit 1

CMD ["python", "run_app.py"]