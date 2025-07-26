FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.23.11
ENV PATH="/usr/local/go/bin:/root/go/bin:$PATH"

# Install core dependencies
RUN apt update && apt install -y \
    curl wget unzip git python3 python3-pip build-essential \
    libpcap-dev dnsutils python3-dnspython jq ca-certificates \
    # Playwright dependencies
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 libatspi2.0-0 libwayland-client0 \
    # Additional recommended dependencies
    libharfbuzz-icu0 libglib2.0-0 libgstreamer-plugins-base1.0-0 \
    libgstreamer1.0-0 libhyphen0 libicu67 libjpeg62-turbo libpng16-16 \
    libwebp6 libwoff1 \
    && rm -rf /var/lib/apt/lists/*

# Install Go
RUN curl -OL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/bin/go && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

# Install Go tools
RUN go install github.com/haccer/subjack@latest && \
    go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest && \
    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install github.com/lc/gau/v2/cmd/gau@latest && \
    go install github.com/tomnomnom/waybackurls@latest && \
    ln -s /root/go/bin/* /usr/bin/

# Setup Subjack fingerprints
RUN mkdir -p /usr/share/subjack && \
    curl -o /usr/share/subjack/fingerprints.json https://raw.githubusercontent.com/haccer/subjack/master/fingerprints.json

# Install cero
RUN git clone --depth=1 https://github.com/glebarez/cero.git /opt/cero && \
    cd /opt/cero && go build && mv cero /usr/bin/ && \
    rm -rf /opt/cero

# Install shosubgo
RUN git clone --depth=1 https://github.com/incogbyte/shosubgo.git /opt/shosubgo && \
    cd /opt/shosubgo && go build -o shosubgo main.go && \
    mv shosubgo /usr/bin/shosubgo && rm -rf /opt/shosubgo

# Install ParamSpider
RUN git clone --depth=1 https://github.com/devanshbatham/ParamSpider.git /opt/ParamSpider && \
    pip install --no-cache-dir requests urllib3 && \
    ln -s /opt/ParamSpider/paramspider /usr/bin/paramspider && \
    chmod +x /opt/ParamSpider/paramspider/main.py && \
    rm -rf /opt/ParamSpider/.git

# Install Findomain
RUN wget -q https://github.com/findomain/findomain/releases/download/9.0.3/findomain-linux.zip -O /tmp/findomain.zip && \
    unzip -q /tmp/findomain.zip -d /tmp/ && \
    mv /tmp/findomain /usr/bin/findomain && \
    chmod +x /usr/bin/findomain && \
    rm -rf /tmp/*

# Set working dir and install Python deps
WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Copy rest of the project
COPY . /app

CMD ["python3", "main.py"]
