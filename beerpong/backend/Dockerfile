# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# system packages falls nötig
RUN pip install --no-cache-dir --upgrade pip

# requirements rein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app rein
COPY . .

# wir starten NICHT "flask run", sondern unser app.py direkt,
# weil wir socketio.run(...) verwenden
CMD ["python", "app.py"]
