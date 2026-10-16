FROM python:3.10-slim

WORKDIR /app

# Instala dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]