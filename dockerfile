# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
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
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome (New Method)
RUN wget -q -O /usr/share/keyrings/google-chrome.gpg https://dl.google.com/linux/linux_signing_key.pub && \
    echo "deb [signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable
