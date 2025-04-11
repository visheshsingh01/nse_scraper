# Use an official lightweight Python image
FROM python:3.11-slim

# Install dependencies and Chromium
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    chromium \
    chromium-driver \
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

# Set environment variables
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV GOOGLE_CHROME_BIN=/usr/bin/chromium

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
