# Use an official lightweight Python image
FROM python:3.11-slim

# Install dependencies and Chromium
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    chromium \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    xdg-utils \
    fonts-liberation \
    libgbm1 \
    libu2f-udev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install the latest ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Set environment variables
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV GOOGLE_CHROME_BIN=/usr/bin/chromium

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 5000

# Run the application with Gunicorn (better for production)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
