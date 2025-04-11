FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install Chrome dependencies with less verbose output
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget unzip gnupg curl apt-transport-https ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libx11-6 libxcb1 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install specific Chrome version and ChromeDriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Use a newer gunicorn for better performance
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port
EXPOSE 10000

# Run with gunicorn for better stability
CMD gunicorn --bind 0.0.0.0:$PORT app:app --log-level info