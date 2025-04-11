# Use an official lightweight Python image
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
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

# Install Google Chrome
RUN wget -q -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i chrome.deb || apt-get -fy install \
    && rm chrome.deb

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '[0-9.]+' | head -1) && \
    CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION) && \
    wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Set environment variables
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV GOOGLE_CHROME_BIN=/usr/bin/google-chrome

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
