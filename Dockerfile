FROM python:3.12-slim

WORKDIR /app

# Install deps first so Docker caches this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source.
COPY . .

# Compile pages at image build time. Re-run at container start if pages
# are mounted as a volume in dev.
RUN python3 compile.py

ENV PORT=8080
EXPOSE 8080

CMD ["python3", "server.py"]
