FROM python:3.9-slim

# Install dependencies for Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libglib2.0-0 \
    libfontconfig1 \
    libxcb1 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libxshmfence1 \
    libgbm1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Modify the code to always use headless mode
RUN sed -i 's/setup_driver(headless=False)/setup_driver(headless=True)/g' app.py

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    CHROMIUM_PATH="/usr/bin/chromium" \
    CHROMEDRIVER_PATH="/usr/bin/chromedriver"

# Expose port
EXPOSE 8080

# Run the application with Gunicorn (only 1 worker to save memory)
CMD ["gunicorn", "--workers", "1", "--timeout", "120", "--bind", "0.0.0.0:8080", "app:app"]
