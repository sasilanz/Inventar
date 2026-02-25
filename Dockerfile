FROM python:3.12-slim

WORKDIR /app

# Abhängigkeiten zuerst installieren (besseres Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY . .

EXPOSE 5000

# Flask-Dev-Server mit Auto-Reload
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
