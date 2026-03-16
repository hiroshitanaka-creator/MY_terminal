FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for ptyprocess
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

COPY terminal/requirements.txt /app/terminal/requirements.txt
RUN pip install --no-cache-dir -r terminal/requirements.txt

COPY terminal/ /app/terminal/

# Create data directory for API presets
RUN mkdir -p /app/data

ENV PORT=8765
ENV MY_TERMINAL_TOKEN=changeme

EXPOSE 8765

CMD ["uvicorn", "terminal.server:app", "--host", "0.0.0.0", "--port", "8765"]
