FROM python:3.11-slim

# Install Firefox & dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Geckodriver
RUN GECKO_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep "tag_name" | cut -d '"' -f 4) && \
    wget https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/geckodriver-$GECKO_VERSION-linux64.tar.gz && \
    tar -xvzf geckodriver-$GECKO_VERSION-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    rm geckodriver-$GECKO_VERSION-linux64.tar.gz

# Set workdir
WORKDIR /app

# Copy files
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "tiktok.py"]
