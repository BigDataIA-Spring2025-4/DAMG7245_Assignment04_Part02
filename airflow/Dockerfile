FROM apache/airflow:2.5.1

USER root

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    apt-utils \
    libgconf-2-4 \
    libnss3 \
    libxi6 \
    libglib2.0-0 \
    libxss1 \
    libxtst6 \
    libxcb1 \
    libx11-xcb1

# Install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
    && wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

USER airflow

# Install Selenium
RUN pip install selenium