# Dockerfile - Agente Pessoal v3.0
FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia requirements primeiro (cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY . .

# Cria diretórios necessários
RUN mkdir -p memory config

# Portas expostas
EXPOSE 8000 8501

# Comando padrão (API)
CMD ["python", "api/main.py"]
